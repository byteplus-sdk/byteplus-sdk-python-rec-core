from abc import abstractmethod

from byteplus_rec_core import utils
from byteplus_rec_core.metrics.constant import *


class MetricsCfg(object):
    def __init__(self, enable_metrics: bool = False, enable_metrics_log: bool = False,
                 domain: str = DEFAULT_METRICS_DOMAIN, prefix: str = DEFAULT_METRICS_PREFIX,
                 http_schema: str = DEFAULT_HTTP_SCHEMA,
                 report_interval_seconds: float = DEFAULT_REPORT_INTERVAL_SECONDS,
                 http_timeout_seconds: float = DEFAULT_HTTP_TIMEOUT_SECONDS):
        # When metrics are enabled, monitoring metrics will be reported to the byteplus server during use.
        self.enable_metrics: bool = enable_metrics
        # When metrics log is enabled, the log will be reported to the byteplus server during use.
        self.enable_metrics_log: bool = enable_metrics_log
        # The address of the byteplus metrics service, will be consistent with the host maintained by hostAvailabler.
        self.domain: str = domain
        # The prefix of the Metrics indicator, the default is byteplus.rec.sdk, do not modify.
        self.prefix: str = prefix
        # Use this httpSchema to report metrics to byteplus server, default is https.
        self.http_schema: str = http_schema
        # The reporting interval, the default is 15s, if the QPS is high,
        # the reporting interval can be reduced to prevent data loss.
        self.report_interval_seconds: float = report_interval_seconds
        # Timeout for request reporting.
        self.http_timeout_seconds: float = http_timeout_seconds


class MetricsOption(object):
    @abstractmethod
    def fill(self, cfg: MetricsCfg) -> None:
        raise NotImplementedError

    @staticmethod
    def with_metrics_domain(domain: str):
        class OptionImpl(MetricsOption):
            def fill(self, cfg: MetricsCfg) -> None:
                if not utils.is_empty_str(domain):
                    cfg.domain = domain

        return OptionImpl()

    @staticmethod
    def with_metrics_prefix(prefix: str):
        class OptionImpl(MetricsOption):
            def fill(self, cfg: MetricsCfg) -> None:
                if not utils.is_empty_str(prefix):
                    cfg.prefix = prefix

        return OptionImpl()

    @staticmethod
    def with_metrics_http_schema(schema: str):
        class OptionImpl(MetricsOption):
            def fill(self, cfg: MetricsCfg) -> None:
                # only support "http" and "https"
                if schema in ["http", "https"]:
                    cfg.http_schema = schema

        return OptionImpl()

    # if not set, will report metrics.
    @staticmethod
    def enable_metrics():
        class OptionImpl(MetricsOption):
            def fill(self, cfg: MetricsCfg) -> None:
                cfg.enable_metrics = True

        return OptionImpl()

    # if not set, will not report metrics logs.
    @staticmethod
    def enable_metrics_log():
        class OptionImpl(MetricsOption):
            def fill(self, cfg: MetricsCfg) -> None:
                cfg.enable_metrics_log = True

        return OptionImpl()

    # set the interval of reporting metrics
    @staticmethod
    def with_report_interval_seconds(report_interval_seconds: float):
        class OptionImpl(MetricsOption):
            def fill(self, cfg: MetricsCfg) -> None:
                if report_interval_seconds > 1:
                    cfg.report_interval_seconds = report_interval_seconds

        return OptionImpl()

    @staticmethod
    def with_metrics_timeout_seconds(metrics_timeout_seconds: int):
        class OptionImpl(MetricsOption):
            def fill(self, cfg: MetricsCfg) -> None:
                cfg.http_timeout_seconds = metrics_timeout_seconds

        return OptionImpl()
