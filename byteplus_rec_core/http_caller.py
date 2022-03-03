import datetime
import gzip
import hashlib
import json
import logging
import random
import string
import time
import uuid
from typing import Callable, Optional, Union

import requests
from google.protobuf.message import Message
from requests import Response

from byteplus_rec_core.exception import BizException, NetException
from byteplus_rec_core.option import Option
from byteplus_rec_core.options import Options
from byteplus_rec_core.utils import _milliseconds
from byteplus_rec_core.volc_auth import _Credential, _volc_sign

log = logging.getLogger(__name__)

_SUCCESS_HTTP_CODE = 200


class _HTTPCaller(object):

    def __init__(self,
                 tenant_id: str,
                 host_header: str,
                 token: str,
                 use_air_auth: bool,
                 credential: _Credential):
        self._tenant_id: str = tenant_id
        self._token: Optional[str] = token
        self._use_air_auth: Optional[bool] = use_air_auth
        self._credential: Optional[_Credential] = credential
        self._host_header: Optional[str] = host_header

    def do_json_request(self, url: str, request: Union[dict, list], *opts: Option) -> Union[dict, list]:
        options: Options = Option.conv_to_options(opts)
        req_str: str = json.dumps(request)
        req_bytes: bytes = req_str.encode("utf-8")
        content_type: str = "application/json"
        rsp_bytes = self.do_request(url, req_bytes, content_type, options)
        return json.loads(rsp_bytes)

    def do_pb_request(self, url: str, request: Message, response: Message, *opts: Option):
        options: Options = Option.conv_to_options(opts)
        req_bytes: bytes = request.SerializeToString()
        content_type: str = "application/x-protobuf"
        rsp_bytes = self.do_request(url, req_bytes, content_type, options)
        try:
            response.ParseFromString(rsp_bytes)
        except BaseException as e:
            log.error("[ByteplusSDK] parse response fail, err:%s url:%s", e, url)
            raise BizException("parse response fail")

    def do_request(self, url, req_bytes, content_type, options: Options) -> bytes:
        req_bytes: bytes = gzip.compress(req_bytes)
        headers: dict = self._build_headers(options, content_type)
        url = self._build_url_with_queries(options, url)
        auth_func = self._get_auth_func(req_bytes)
        return self._do_http_request(url, headers, req_bytes, options.timeout, auth_func)

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
        if self._host_header is not None and len(self._host_header) > 0:
            headers["Host"] = self._host_header
        self._with_options_headers(headers, options)
        return headers

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

    @staticmethod
    def _with_options_headers(headers: dict, options: Options):
        if options.headers is not None:
            headers.update(options.headers)
        if options.request_id is not None and len(options.request_id) > 0:
            headers["Request-Id"] = options.request_id
        else:
            request_id = uuid.uuid1()
            log.info("[ByteplusSDK] use requestId generated by sdk: '%s' ", request_id)
            headers["Request-Id"] = str(request_id)
        if options.server_timeout is not None:
            headers["Timeout-Millis"] = str(_milliseconds(options.server_timeout))

    def _get_auth_func(self, req_bytes: bytes) -> Callable:
        if self._use_air_auth:
            return lambda req: self._with_air_auth_headers(req, req_bytes)
        return _volc_sign(self._credential)

    def _with_air_auth_headers(self, req, req_bytes: bytes) -> None:
        ts = str(int(time.time()))
        nonce = ''.join(random.sample(string.ascii_letters + string.digits, 8))
        signature = self._cal_signature(req_bytes, ts, nonce)

        req.headers['Tenant-Ts'] = ts
        req.headers['Tenant-Nonce'] = nonce
        req.headers['Tenant-Signature'] = signature
        return req

    def _cal_signature(self, req_bytes: bytes, ts: str, nonce: str) -> str:
        sha256 = hashlib.sha256()
        sha256.update(self._token.encode('utf-8'))
        sha256.update(req_bytes)
        sha256.update(self._tenant_id.encode('utf-8'))
        sha256.update(ts.encode('utf-8'))
        sha256.update(nonce.encode('utf-8'))
        return sha256.hexdigest()

    def _do_http_request(self,
                         url: str,
                         headers: dict,
                         req_bytes: bytes,
                         timeout: Optional[datetime.timedelta],
                         auth_func: Callable) -> Optional[bytes]:
        start = time.time()
        log.debug("[ByteplusSDK][HTTPCaller] URL:%s, Request Headers:\n%s", url, str(headers))
        try:
            if timeout is not None:
                timeout_secs = timeout.total_seconds()
                rsp: Response = requests.post(url=url, headers=headers, data=req_bytes, timeout=timeout_secs, auth=auth_func)
                # TODO check content type: response.header("Content-Encoding")
            else:
                rsp: Response = requests.post(url=url, headers=headers, data=req_bytes, auth=auth_func)
        except BaseException as e:
            if self._is_timeout_exception(e):
                log.error("[ByteplusSDK] do http request timeout, url:%s msg:%s", url, e)
                raise NetException(str(e))
            log.error("[ByteplusSDK] do http request occur io exception, url:%s msg:%s", url, e)
            raise BizException(str(e))
        finally:
            cost = int((time.time() - start) * 1000)
            log.debug("[ByteplusSDK] http path:%s, cost:%dms", url, cost)
        log.debug("[ByteplusSDK][HTTPCaller] URL:%s, Response Headers:\n%s", url, str(rsp.headers))
        if rsp.status_code != _SUCCESS_HTTP_CODE:
            self._log_rsp(url, rsp)
            raise BizException("code:{} msg:{}".format(rsp.status_code, rsp.reason))
        return rsp.content

    @staticmethod
    def _is_timeout_exception(e):
        lower_err_msg = str(e).lower()
        if "time" in lower_err_msg and "out" in lower_err_msg:
            return True
        return False

    @staticmethod
    def _log_rsp(url: str, rsp: Response) -> None:
        rsp_bytes = rsp.content
        if rsp_bytes is not None and len(rsp.content) > 0:
            log.error("[ByteplusSDK] http status not 200, url:%s code:%d msg:%s headers:\n%s body:\n%s",
                      url, rsp.status_code, rsp.reason, str(rsp.headers), str(rsp_bytes))
        else:
            log.error("[ByteplusSDK] http status not 200, url:%s code:%d msg:%s headers:\n%s",
                      url, rsp.status_code, rsp.reason, str(rsp.headers))
        return
