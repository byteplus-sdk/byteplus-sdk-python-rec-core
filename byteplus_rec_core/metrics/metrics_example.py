import time
import logging
import threading
import uuid

from byteplus_rec_core.metrics.metrics import Metrics
from byteplus_rec_core.metrics.metrics_collector import MetricsCollector
from byteplus_rec_core.metrics.metrics_log import MetricsLog
from byteplus_rec_core.metrics.metrics_option import MetricsOption


class MetricsExample(object):
    times = 100

    @classmethod
    def metrics_init(cls):
        # default log level is warning
        logging.basicConfig(level=logging.DEBUG)
        MetricsCollector.init_with_option(
            MetricsOption.with_metrics_http_schema("http"),
            MetricsOption.enable_metrics(),
            MetricsOption.enable_metrics_log(),
            MetricsOption.with_report_interval_seconds(5),
            MetricsOption.with_metrics_prefix("test.byteplus.sdk"),
            MetricsOption.with_metrics_timeout_seconds(1),
            MetricsOption.with_metrics_domain("rec-b-ap-singapore-1.byteplusapi.com")
        )

    # test demo for store report
    @classmethod
    def store_report(cls):
        print("start store reporting...")
        for i in range(cls.times):
            Metrics.store(
                "java.request.store", 200, "type:test_metrics1", "url:https://asfwe.sds.com/test?qu1=xxx&qu2=yyy")
            Metrics.store(
                "java.request.store", 100, "type:test_metrics2", "url:https://asfwe.sds.com/test?qu1=xxx&qu2=yyy")
            Metrics.store(
                "java.request.store", 200, "type:test_metrics3", "url:https://asfwe.sds.com/test?qu1=xxx&qu2=yyy")
            Metrics.store(
                "java.request.store", 100, "type:test_metrics4", "url:https://asfwe.sds.com/test?qu1<eq>xxx&qu2<eq>yyy")
            # 20s
            time.sleep(20)
        print("stop store reporting")

    # test demo for counter report
    @classmethod
    def counter_report(cls):
        print("start counter reporting...")
        for i in range(cls.times):
            Metrics.counter("java.request.counter", 1, "type:test_counter1")
            Metrics.counter("java.request.counter", 1, "type:test_counter2")
            # 20s
            time.sleep(20)
        print("stop counter reporting")

    # test demo for timer report
    @classmethod
    def timer_report(cls):
        print("start timer reporting...")
        for i in range(cls.times):
            Metrics.timer("java.request.timer", 140, "type:test_timer4")
            Metrics.timer("java.request.timer", 160, "type:test_timer4")
            # 30s
            time.sleep(30)
        print("stop timer reporting")


if __name__ == '__main__':
    MetricsExample.metrics_init()
    # MetricsExample.store_report()
    # MetricsExample.counter_report()
    MetricsExample.timer_report()
    # log_id = str(uuid.uuid4())
    # print("log_id: {}".format(log_id))
    # MetricsLog.info(log_id, "this is a test log: name:{}, value: {}", "demo", 1)

