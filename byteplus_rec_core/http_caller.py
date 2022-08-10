import gzip
import hashlib
import json
import logging
import random
import string
import threading
import time
import uuid
from typing import Optional, Union
import requests
from requests import Response, Session

from google.protobuf.message import Message
from requests.adapters import HTTPAdapter

from byteplus_rec_core import constant, utils
from byteplus_rec_core.abtract_host_availabler import AbstractHostAvailabler
from byteplus_rec_core.exception import BizException, NetException
from byteplus_rec_core.option import Option
from byteplus_rec_core.options import Options
from byteplus_rec_core.utils import _milliseconds, HTTPRequest
from byteplus_rec_core.auth import _Credential, _sign

log = logging.getLogger(__name__)

_DEFAULT_PING_URL_FORMAT: str = "{}://{}/predict/api/ping"
_DEFAULT_PING_TIMEOUT_SECONDS: float = 0.5


class Config(object):
    def __init__(self,
                 max_idle_connections: Optional[int] = constant.DEFAULT_MAX_IDLE_CONNECTIONS,
                 keep_alive_ping_interval_seconds: Optional[float] = constant.DEFAULT_KEEPALIVE_PING_INTERVAL_SECONDS):
        self.max_idle_connections = max_idle_connections
        self.keep_alive_ping_interval_seconds = keep_alive_ping_interval_seconds


class _HTTPCaller(object):
    def __init__(self,
                 project_id: str,
                 tenant_id: str,
                 air_auth_token: str,
                 host_availabler: AbstractHostAvailabler,
                 caller_config: Config,
                 schema: str,
                 keep_alive: bool,
                 credential: _Credential = None):
        self._abort: bool = False
        self._project = project_id
        self._tenant_id: str = tenant_id
        self._air_auth_token: Optional[str] = air_auth_token
        self._host_availabler = host_availabler
        self._config = caller_config
        self._schema = schema
        self._keep_alive = keep_alive
        self._credential: Optional[_Credential] = credential
        # requests.post creates a new connection for each request, and cannot reuse the connection.
        # Change it to session mode. By default, it maintains a connection pool of up to 10 different hosts.
        self._http_cli: Session = requests.Session()
        self._http_cli.mount("https://", HTTPAdapter(pool_maxsize=self._config.max_idle_connections))
        self._http_cli.mount("http://", HTTPAdapter(pool_maxsize=self._config.max_idle_connections))
        if self._keep_alive:
            self._init_heartbeat_executor()

    def _init_heartbeat_executor(self):
        threading.Thread(target=self._heartbeat).start()

    def _heartbeat(self):
        if self._abort:
            return
        time.sleep(self._config.keep_alive_ping_interval_seconds)
        for host in self._host_availabler.get_hosts():
            utils.ping(self._project, self._http_cli, _DEFAULT_PING_URL_FORMAT,
                       self._schema, host, _DEFAULT_PING_TIMEOUT_SECONDS)
        self._heartbeat()

    def do_json_request(self, url: str, request: Union[dict, list], *opts: Option) -> Union[dict, list]:
        options: Options = Option.conv_to_options(opts)
        try:
            req_str: str = json.dumps(request)
        except BaseException as e:
            raise BizException(str(e))
        req_bytes: bytes = req_str.encode("utf-8")
        content_type: str = "application/json"
        rsp_bytes = self._do_request(url, req_bytes, content_type, options)
        try:
            rsp = json.loads(rsp_bytes)
        except BaseException as e:
            raise BizException(str(e))
        return rsp

    def do_pb_request(self, url: str, request: Message, response: Message, *opts: Option):
        options: Options = Option.conv_to_options(opts)
        req_bytes: bytes = request.SerializeToString()
        content_type: str = "application/x-protobuf"
        rsp_bytes = self._do_request(url, req_bytes, content_type, options)
        try:
            response.ParseFromString(rsp_bytes)
        except BaseException as e:
            log.error("[ByteplusSDK] parse response fail, err:%s url:%s", e, url)
            raise BizException("parse response fail")

    def _do_request(self, url: str, req_bytes: bytes, content_type: str, options: Options) -> Optional[bytes]:
        req_bytes: bytes = gzip.compress(req_bytes)
        headers: dict = self._build_headers(options, content_type)
        url = self._build_url_with_queries(options, url)
        return self._do_http_request(url, headers, req_bytes, options)

    def _build_headers(self, options: Options, content_type: str) -> dict:
        headers = {
            "Content-Encoding": "gzip",
            # The 'requests' lib support '"Content-Encoding": "gzip"' header,
            # it will decompress gzip response without us
            "Accept-Encoding": "gzip",
            "Content-Type": content_type,
            "Accept": content_type,
            "Tenant-Id": self._tenant_id,
        }
        self._with_options_headers(headers, options)
        return headers

    @staticmethod
    def _with_options_headers(headers: dict, options: Options):
        if options.headers is not None:
            headers.update(options.headers)
        if options.request_id is not None and len(options.request_id) > 0:
            headers["Request-Id"] = options.request_id
        else:
            request_id = uuid.uuid1()
            log.info("[ByteplusSDK] requestID is generated by sdk: '%s'", request_id)
            headers["Request-Id"] = str(request_id)
        if options.server_timeout is not None:
            headers["Timeout-Millis"] = str(_milliseconds(options.server_timeout))

    @staticmethod
    def _build_url_with_queries(options: Options, url: str):
        queries = {}
        if options.queries is not None:
            queries.update(options.queries)
        if len(queries) == 0:
            return url
        query_parts = []
        for query_name in queries.keys():
            query_parts.append(query_name + "=" + queries[query_name])
        query_string = "&".join(query_parts)
        if "?" in url:
            return url + "&" + query_string
        return url + "?" + query_string

    def _do_http_request(self, url: str, headers: dict, req_bytes: bytes, options: Options) -> Optional[bytes]:
        req = HTTPRequest(headers, url, constant.POST_METHOD_NAME, req_bytes)
        self._with_auth_headers(req)
        start = time.time()
        log.debug("[ByteplusSDK][HTTPCaller] URL:%s, Request Headers:\n%s", url, str(headers))
        try:
            if options.timeout is not None:
                timeout_secs = options.timeout.total_seconds()
                rsp: Response = self._http_cli.post(url=req.url, headers=req.header, data=req.req_bytes,
                                                    timeout=timeout_secs)
            else:
                rsp: Response = self._http_cli.post(url=url, headers=headers, data=req_bytes)
            if rsp.status_code != constant.HTTP_STATUS_OK:
                self._log_err_http_rsp(url, rsp)
                raise BizException("code:{} msg:{}".format(rsp.status_code, rsp.reason))
            cost = int((time.time() - start) * 1000)
            log.debug("[ByteplusSDK] http path:%s, cost:%dms", url, cost)
        except BaseException as e:
            cost = int((time.time() - start) * 1000)
            if self._is_timeout_exception(e):
                log.error("[ByteplusSDK] do http request timeout, url:%s, cost:%dms, msg:%s", url, cost, e)
                raise NetException(str(e))
            log.error("[ByteplusSDK] do http request occur io exception, url:%s, cost:%dms, msg:%s", url, cost, e)
            raise BizException(str(e))
        log.debug("[ByteplusSDK][HTTPCaller] URL:%s, Response Headers:\n%s", url, str(rsp.headers))
        return rsp.content

    def _with_auth_headers(self, req: HTTPRequest):
        if self._credential is None:
            self._with_air_auth_headers(req)
            return
        _sign(req, self._credential)

    def _with_air_auth_headers(self, req: HTTPRequest) -> None:
        ts = str(int(time.time()))
        nonce = ''.join(random.sample(string.ascii_letters + string.digits, 8))
        signature = self._cal_signature(req.req_bytes, ts, nonce)
        req.header['Tenant-Ts'] = ts
        req.header['Tenant-Nonce'] = nonce
        req.header['Tenant-Signature'] = signature

    def _cal_signature(self, req_bytes: bytes, ts: str, nonce: str) -> str:
        sha256 = hashlib.sha256()
        sha256.update(self._air_auth_token.encode('utf-8'))
        sha256.update(req_bytes)
        sha256.update(self._tenant_id.encode('utf-8'))
        sha256.update(ts.encode('utf-8'))
        sha256.update(nonce.encode('utf-8'))
        return sha256.hexdigest()

    @staticmethod
    def _log_err_http_rsp(url: str, rsp: Response) -> None:
        rsp_bytes = rsp.content
        if rsp_bytes is not None and len(rsp.content) > 0:
            log.error("[ByteplusSDK] http status not 200, url:%s code:%d msg:%s headers:\n%s body:\n%s",
                      url, rsp.status_code, rsp.reason, str(rsp.headers), str(rsp_bytes))
        else:
            log.error("[ByteplusSDK] http status not 200, url:%s code:%d msg:%s headers:\n%s",
                      url, rsp.status_code, rsp.reason, str(rsp.headers))
        return

    @staticmethod
    def _is_timeout_exception(e):
        lower_err_msg = str(e).lower()
        if "time" in lower_err_msg and "out" in lower_err_msg:
            return True
        return False

    def shutdown(self):
        self._abort = True
