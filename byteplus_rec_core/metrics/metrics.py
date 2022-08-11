from byteplus_rec_core import utils

from byteplus_rec_core.metrics import constant
from byteplus_rec_core.metrics.metrics_collector import MetricsCollector


class Metrics(object):
    # description: Store tagKvs should be formatted as "key:value"
    # example: store("goroutine.count", 400, "ip:127.0.0.1")
    @staticmethod
    def store(key: str, value: int, *tag_kvs: str):
        MetricsCollector.emit_metrics(constant.METRICS_TYPE_STORE, key, value, *tag_kvs)

    # description: Store tagKvs should be formatted as "key:value"
    # example: counter("request.count", 1, "method:user", "type:upload")
    @staticmethod
    def counter(key: str, value: int, *tag_kvs: str):
        MetricsCollector.emit_metrics(constant.METRICS_TYPE_COUNTER, key, value, *tag_kvs)

    # The unit of `value` is milliseconds
    # example: timer("request.cost", 100, "method:user", "type:upload")
    # description: Store tagKvs should be formatted as "key:value"
    @staticmethod
    def timer(key: str, value: int, *tag_kvs: str):
        MetricsCollector.emit_metrics(constant.METRICS_TYPE_TIMER, key, value, *tag_kvs)

    # The unit of `begin` is milliseconds
    # example: latency("request.latency", startTime, "method:user", "type:upload")
    # description: Store tagKvs should be formatted as "key:value"
    @staticmethod
    def latency(key: str, begin: int, *tag_kvs: str):
        MetricsCollector.emit_metrics(constant.METRICS_TYPE_TIMER, key,
                                      utils.current_time_millis() - begin, *tag_kvs)

    # description: Store tagKvs should be formatted as "key:value"
    # example: rateCounter("request.count", 1, "method:user", "type:upload")
    @staticmethod
    def rate_counter(key: str, value: int, *tag_kvs: str):
        MetricsCollector.emit_metrics(constant.METRICS_TYPE_RATE_COUNTER, key, value, *tag_kvs)

    # description:
    #   - meter(xx) = counter(xx) + rateCounter(xx.rate)
    #   - Store tagKvs should be formatted as "key:value"
    # example: rateCounter("request.count", 1, "method:user", "type:upload")
    @staticmethod
    def meter(key: str, value: int, *tag_kvs: str):
        MetricsCollector.emit_metrics(constant.METRICS_TYPE_METER, key, value, *tag_kvs)
