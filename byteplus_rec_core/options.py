import datetime
from typing import Optional


class Options(object):
    def __init__(self):
        self.timeout: Optional[datetime.timedelta] = None
        self.request_id: Optional[str] = None
        self.headers: Optional[dict] = None
        self.queries: Optional[dict] = None
        self.server_timeout: Optional[datetime.timedelta] = None
