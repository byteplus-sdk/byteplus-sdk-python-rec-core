HTTP_STATUS_OK: int = 200

HTTP_STATUS_NOT_FOUND: int = 404

# The request was executed successfully without any exception
STATUS_CODE_SUCCESS: int = 0
# A Request with the same "Request-ID" was already received. This Request was rejected
STATUS_CODE_IDEMPOTENT: int = 409
# Operation information is missing due to an unknown exception
STATUS_CODE_OPERATION_LOSS: int = 410
# The server hope slow down request frequency, and this request was rejected
STATUS_CODE_TOO_MANY_REQUEST: int = 429

POST_METHOD_NAME = "POST"


# The default max idle connections of okhttp client connection pool
DEFAULT_MAX_IDLE_CONNECTIONS: int = 32
# The default keepalive ping interval
DEFAULT_KEEPALIVE_PING_INTERVAL_SECONDS: float = 45

# Metrics Key
METRICS_KEY_COMMON_INFO = "common.info"
METRICS_KEY_COMMON_WARN = "common.warn"
METRICS_KEY_COMMON_ERROR = "common.err"
METRICS_KEY_REQUEST_TOTAL_COST = "request.total.cost"
METRICS_KEY_REQUEST_COUNT = "request.count"
METRICS_KEY_HEARTBEAT_COUNT = "heartbeat.count"
