import requests
from byteplus_rec_core import utils
from requests import Response

from byteplus_rec_core.exception import BizException
from byteplus_rec_core.metrics import constant
from byteplus_rec_core.metrics.metrics_collector import MetricsCfg
from byteplus_rec_core.metrics.protocol import MetricLogMessage, MetricMessage


class MetricsReporter(object):
    def __init__(self, metrics_cfg: MetricsCfg):
        self._http_cli = requests.Session()
        self._metrics_cfg = metrics_cfg

    def report_metrics(self, metric_message: MetricMessage, url: str):
        req_bytes: bytes = metric_message.SerializeToString()
        headers: dict = self._build_metrics_headers()
        self._do_request(url, req_bytes, headers)

    def report_metrics_log(self, metric_log_message: MetricLogMessage, url: str):
        req_bytes: bytes = metric_log_message.SerializeToString()
        headers: dict = self._build_metrics_headers()
        self._do_request(url, req_bytes, headers)

    def _do_request(self, url: str, req_bytes: bytes, headers: dict):
        for i in range(constant.MAX_TRY_TIMES):
            try:
                response: Response = self._http_cli.post(url=url, headers=headers, data=req_bytes,
                                                         timeout=self._metrics_cfg.http_timeout_seconds)
                if response.status_code == constant.SUCCESS_HTTP_CODE:
                    return
                if response.content is None:
                    raise BizException("rsp body is null")
                raise BizException("do http request fail, url:{}, code:{}, rsp:{}".
                                   format(url, response.status_code, response.content))
            except BaseException as e:
                if utils.is_timeout_exception(e) and i < constant.MAX_TRY_TIMES - 1:
                    continue
                raise BizException(str(e))

    @staticmethod
    def _build_metrics_headers() -> dict:
        headers = {
            "Content-Type": "application/x-protobuf",
            "Accept": "application/json"
        }
        return headers
