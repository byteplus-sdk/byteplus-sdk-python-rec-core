import time
import uuid
from datetime import timedelta
import logging
from typing import List, Optional

from byteplus_rec_core import constant
from requests import Session, Response

from byteplus_rec_core.exception import NetException, BizException
from byteplus_rec_core.metrics.metrics_log import MetricsLog

log = logging.getLogger(__name__)


def current_time_millis() -> int:
    return int(time.time() * 1000)


def _milliseconds(delta: timedelta) -> int:
    return int(delta.total_seconds() * 1000.0)


def do_with_retry(call, request, opts: tuple, retry_times: int):
    # To ensure the request is successfully received by the server,
    # it should be retried after a network exception occurs.
    # To prevent the retry from causing duplicate uploading same data,
    # the request should be retried by using the same requestId.
    # If a new requestId is used, it will be treated as a new request
    # by the server, which may save duplicate data
    if retry_times < 0:
        retry_times = 0
    try_times = retry_times + 1
    for i in range(try_times):
        try:
            rsp = call(request, *opts)
        except NetException as e:
            if i == try_times - 1:
                log.error("[DoRetryRequest] fail finally after retried '%s' times", try_times)
                raise BizException(str(e))
            continue
        return rsp
    return


def build_url(schema: str, host: str, path: str) -> str:
    if path[0] == '/':
        return "{}://{}{}".format(schema, host, path)
    return "{}://{}/{}".format(schema, host, path)


def none_empty_str(st: List[str]) -> bool:
    if str is None:
        return False
    for s in st:
        if s is None or len(s) == 0:
            return False
    return True


def is_all_empty_str(st: List[str]) -> bool:
    if st is None:
        return True
    for s in st:
        if s is not None and len(s) > 0:
            return False
    return True


def is_empty_str(st: str) -> bool:
    return st is None or len(st) == 0


def ping(project_id: str, http_cli: Session, ping_url_format: str,
         schema: str, host: str, ping_timeout_seconds: float) -> bool:
    url: str = ping_url_format.format(schema, host)
    req_id: str = "ping_" + str(uuid.uuid1())
    headers = {
        "Request-Id": req_id,
        "Project-Id": project_id,
    }
    start = time.time()
    try:
        rsp: Response = http_cli.get(url, headers=headers, timeout=ping_timeout_seconds)
        cost = int((time.time() - start) * 1000)
        if is_ping_success(rsp):
            MetricsLog.info(req_id, "[ByteplusSDK] ping success, project_id:{}, host:{}, cost:{}ms",
                            project_id, host, cost)
            log.debug("[ByteplusSDK] ping success, host:'%s' cost:%dms", host, cost)
            return True
        MetricsLog.warn(req_id, "[ByteplusSDK] ping fail, project_id:{}, host:{}, cost:{}ms, status:{}",
                        project_id, host, cost, rsp.status_code)
        log.warning("[ByteplusSDK] ping fail, host:'%s', cost:%dms, status:'%s'", host, cost, rsp.status_code)
        return False
    except BaseException as e:
        cost = int((time.time() - start) * 1000)
        MetricsLog.warn(req_id, "[ByteplusSDK] ping find err, project_id:{}, host:{}, cost:{}ms, err:{}",
                        project_id, host, cost, e)
        log.warning("[ByteplusSDK] ping find err, host:'%s', cost:%dms, err:'%s'", host, cost, e)
        return False


def is_ping_success(rsp: Response) -> bool:
    if rsp.status_code != constant.HTTP_STATUS_OK:
        return False
    if rsp.content is None:
        return False
    rsp_str: str = str(rsp.content)
    return len(rsp_str) < 20 and "pong" in rsp_str


def is_timeout_exception(e):
    lower_err_msg = str(e).lower()
    if "time" in lower_err_msg and "out" in lower_err_msg:
        return True
    return False


def escape_metrics_tag_value(value: str) -> str:
    value = value.replace("?", "-qu-", -1)
    value = value.replace("&", "-and-", -1)
    value = value.replace("=", "-eq-", -1)
    return value


class HTTPRequest(object):
    def __init__(self,
                 header: dict,
                 url: str,
                 method: str,
                 req_bytes: bytes):
        self.header: dict = header
        self.url: str = url
        self.method: str = method
        self.req_bytes: bytes = req_bytes
