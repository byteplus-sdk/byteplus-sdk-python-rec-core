from datetime import timedelta
import logging
from typing import List

from byteplus_rec_core.exception import NetException, BizException

log = logging.getLogger(__name__)


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
    if str is None:
        return True
    for s in st:
        if s is not None and len(s) > 0:
            return False
    return True


def is_empty_str(st: str) -> bool:
    return st is None or len(st) == 0


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
