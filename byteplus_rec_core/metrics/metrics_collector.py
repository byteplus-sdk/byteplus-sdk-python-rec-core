import logging
import threading
import time
from threading import Lock
from queue import Queue
from typing import Optional, List

from byteplus_rec_core.metrics.metrics_option import *
from byteplus_rec_core.metrics.constant import *
from byteplus_rec_core.metrics.metrics_reporter import MetricsReporter
from byteplus_rec_core.metrics.protocol import Metric, MetricMessage, MetricLog, MetricLogMessage

log = logging.getLogger(__name__)


class MetricsCollector(object):
    metrics_cfg: MetricsCfg = None
    host_availabler = None
    metrics_reporter: MetricsReporter
    metrics_collector: Queue = None
    metrics_log_collector: Queue = None
    cleaning_metrics_collector: bool = False
    cleaning_metrics_log_collector: bool = False
    initialed: bool = False
    lock: Lock = Lock()

    @classmethod
    def init(cls, cfg: MetricsCfg = None, host_availabler = None):
        if cls.initialed:
            return
        if cfg is None:
            cfg = MetricsCfg()
        cls._do_init(cfg, host_availabler)

    @classmethod
    def init_with_option(cls, *metrics_opts: MetricsOption):
        if cls.initialed:
            return
        cfg = MetricsCfg()
        for opt in metrics_opts:
            opt.fill(cfg)
        cls._do_init(cfg)

    @classmethod
    def _do_init(cls, cfg: MetricsCfg, host_availabler = None):
        cls.lock.acquire()
        if cls.initialed:
            return
        cls.metrics_cfg = cfg
        cls.host_availabler = host_availabler
        # initialize metrics reporter
        cls.metrics_reporter = MetricsReporter(cls.metrics_cfg)
        # initialize metrics collector
        cls.metrics_collector = Queue(maxsize=MAX_METRICS_SIZE)
        cls.metrics_log_collector = Queue(maxsize=MAX_METRICS_LOG_SIZE)

        if not cls.is_enable_metrics() and not cls.is_enable_metrics_log():
            cls.initialed = True
            return
        threading.Thread(target=cls._report).start()
        cls.initialed = True
        cls.lock.release()

    @classmethod
    def is_initialed(cls) -> bool:
        return cls.initialed

    @classmethod
    def is_enable_metrics(cls) -> bool:
        if cls.metrics_cfg is None:
            return False
        return cls.metrics_cfg.enable_metrics

    @classmethod
    def is_enable_metrics_log(cls) -> bool:
        if cls.metrics_cfg is None:
            return False
        return cls.metrics_cfg.enable_metrics_log

    @classmethod
    def emit_metrics(cls, metrics_type: str, name: str, value: int, *tag_kvs: str):
        if not cls.is_enable_metrics():
            return
        # spin when cleaning collector
        try_times = 0
        while cls.cleaning_metrics_collector:
            if try_times >= MAX_SPIN_TIMES:
                return
            # sleep 10ms.
            time.sleep(1/1000 * 10)
            try_times += 1
        if cls.metrics_collector.full():
            log.debug("[BytePlusSDK][Metrics]: The number of metrics exceeds the limit, the metrics write is rejected")
            return
        metric_name: str = name
        if not utils.is_empty_str(cls.metrics_cfg.prefix):
            metric_name = "{}.{}".format(cls.metrics_cfg.prefix, metric_name)
        metric: Metric = Metric()
        metric.name = metric_name
        metric.type = metrics_type
        metric.value = float(value)
        metric.timestamp = utils.current_time_millis()
        metric.tags.update(cls._recover_tags(*tag_kvs))
        cls.metrics_collector.put(metric)

    @classmethod
    def _recover_tags(cls, *tag_kvs: str) -> dict:
        tags = {}
        for tag in tag_kvs:
            kv = tag.split(':', 1)  # only split once, the first part is key, the rest is value
            if len(kv) < 2:
                continue
            tags[kv[0]] = kv[1]
        return tags

    @classmethod
    def emit_log(cls, log_id: str, message: str, log_level: str, timestamp: int):
        if not cls.is_enable_metrics_log():
            return
        # spin when cleaning collector
        try_times = 0
        while cls.cleaning_metrics_log_collector:
            if try_times >= MAX_SPIN_TIMES:
                return
            # sleep 10ms.
            time.sleep(1/1000 * 10)
            try_times += 1
        if cls.metrics_log_collector.full():
            log.debug("[BytePlusSDK][Metrics]: The number of metrics logs exceeds the limit, the metrics write is "
                      "rejected")
            return
        metric_log: MetricLog = MetricLog()
        metric_log.id = log_id
        metric_log.message = message
        metric_log.level = log_level
        metric_log.timestamp = timestamp
        cls.metrics_log_collector.put(metric_log)

    @classmethod
    def _report(cls):
        time.sleep(cls.metrics_cfg.report_interval_seconds)
        if cls.is_enable_metrics():
            cls._report_metrics()
        if cls.is_enable_metrics_log():
            cls._report_metrics_log()
        cls._report()

    @classmethod
    def _report_metrics(cls):
        if cls.metrics_collector.empty():
            return
        metrics: List[Metric] = []
        cls.cleaning_metrics_collector = True
        while True:
            if cls.metrics_collector.empty():
                break
            metrics.append(cls.metrics_collector.get())
        cls.cleaning_metrics_collector = False
        cls._do_report_metrics(metrics)

    @classmethod
    def _do_report_metrics(cls, metrics: List[Metric]):
        url: str = METRICS_URL_FORMAT.format(cls.metrics_cfg.http_schema, cls._get_domain(METRICS_PATH))
        metric_message: MetricMessage = MetricMessage()
        metric_message.metrics.extend(metrics)
        try:
            cls.metrics_reporter.report_metrics(metric_message, url)
        except BaseException as e:
            log.error("[BytePlusSDK][Metrics] report metrics exception, msg:{}, url:{}".format(str(e), url))

    @classmethod
    def _report_metrics_log(cls):
        if cls.metrics_log_collector.empty():
            return
        metric_logs: List[MetricLog] = []
        cls.cleaning_metrics_log_collector = True
        while True:
            if cls.metrics_log_collector.empty():
                break
            metric_logs.append(cls.metrics_log_collector.get())
        cls.cleaning_metrics_log_collector = False
        cls.do_report_metrics_log(metric_logs)

    @classmethod
    def do_report_metrics_log(cls, metric_logs: List[MetricLog]):
        url: str = METRICS_LOG_URL_FORMAT.format(cls.metrics_cfg.http_schema, cls._get_domain(METRICS_LOG_PATH))
        metric_log_message: MetricLogMessage = MetricLogMessage()
        metric_log_message.metric_logs.extend(metric_logs)
        try:
            cls.metrics_reporter.report_metrics_log(metric_log_message, url)
        except BaseException as e:
            log.error("[BytePlusSDK][Metrics] report metrics log exception, msg:{}, url:{}".format(str(e), url))

    @classmethod
    def _get_domain(cls, path: str) -> str:
        if cls.host_availabler is None:
            return cls.metrics_cfg.domain
        return cls.host_availabler.get_host(path)
