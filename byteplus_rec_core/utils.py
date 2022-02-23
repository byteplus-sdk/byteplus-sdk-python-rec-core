from datetime import timedelta, datetime

from byteplus_rec_core.exception import NetException, BizException

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
                raise BizException(str(e))
            continue
        return rsp
    return
