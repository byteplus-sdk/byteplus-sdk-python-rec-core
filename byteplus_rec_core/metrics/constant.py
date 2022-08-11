from enum import Enum, unique

# metrics default domain and prefix
DEFAULT_METRICS_DOMAIN: str = "rec-api-sg1.recplusapi.com"
DEFAULT_METRICS_PREFIX: str = "byteplus.rec.sdk"
DEFAULT_HTTP_SCHEMA: str = "https"

# monitor url format
METRICS_URL_FORMAT: str = "{}://{}/predict/api/monitor/metrics"
METRICS_LOG_URL_FORMAT: str = "{}://{}/predict/api/monitor/metrics/log"

# domain path
METRICS_PATH: str = "/monitor/metrics"
METRICS_LOG_PATH: str = "/monitor/metrics/log"

# metrics flush interval
DEFAULT_REPORT_INTERVAL_SECONDS: float = 15
DEFAULT_HTTP_TIMEOUT_SECONDS: float = 0.8
MAX_TRY_TIMES: int = 3
MAX_SPIN_TIMES: int = 5
SUCCESS_HTTP_CODE: int = 200
MAX_METRICS_SIZE: int = 10000
MAX_METRICS_LOG_SIZE: int = 5000

# metrics log level
LOG_LEVEL_TRACE: str = "trace"
LOG_LEVEL_DEBUG: str = "debug"
LOG_LEVEL_INFO: str = "info"
LOG_LEVEL_NOTICE: str = "notice"
LOG_LEVEL_WARN: str = "warn"
LOG_LEVEL_ERROR: str = "error"
LOG_LEVEL_FATAL: str = "fatal"

# metrics type
METRICS_TYPE_COUNTER: str = "counter"
METRICS_TYPE_STORE: str = "store"
METRICS_TYPE_TIMER: str = "timer"
METRICS_TYPE_RATE_COUNTER: str = "rate_counter"
METRICS_TYPE_METER: str = "meter"


@unique
class MetricsType(Enum):
    metrics_type_counter = 0
    metrics_type_timer = 1
    metrics_type_store = 2
