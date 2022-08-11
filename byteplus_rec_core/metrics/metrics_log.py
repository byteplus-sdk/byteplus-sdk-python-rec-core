from byteplus_rec_core import utils

from byteplus_rec_core.metrics import constant
from byteplus_rec_core.metrics.metrics_collector import MetricsCollector


class MetricsLog(object):
    @staticmethod
    def trace(log_id: str, log_format: str, *args):
        message: str = log_format.format(*args)
        MetricsCollector.emit_log(log_id, message, constant.LOG_LEVEL_TRACE, utils.current_time_millis())

    @staticmethod
    def debug(log_id: str, log_format: str, *args):
        message: str = log_format.format(*args)
        MetricsCollector.emit_log(log_id, message, constant.LOG_LEVEL_DEBUG, utils.current_time_millis())

    @staticmethod
    def info(log_id: str, log_format: str, *args):
        message: str = log_format.format(*args)
        MetricsCollector.emit_log(log_id, message, constant.LOG_LEVEL_INFO, utils.current_time_millis())

    @staticmethod
    def notice(log_id: str, log_format: str, *args):
        message: str = log_format.format(*args)
        MetricsCollector.emit_log(log_id, message, constant.LOG_LEVEL_NOTICE, utils.current_time_millis())

    @staticmethod
    def warn(log_id: str, log_format: str, *args):
        message: str = log_format.format(*args)
        MetricsCollector.emit_log(log_id, message, constant.LOG_LEVEL_WARN, utils.current_time_millis())

    @staticmethod
    def error(log_id: str, log_format: str, *args):
        message: str = log_format.format(*args)
        MetricsCollector.emit_log(log_id, message, constant.LOG_LEVEL_ERROR, utils.current_time_millis())

    @staticmethod
    def fatal(log_id: str, log_format: str, *args):
        message: str = log_format.format(*args)
        MetricsCollector.emit_log(log_id, message, constant.LOG_LEVEL_FATAL, utils.current_time_millis())
