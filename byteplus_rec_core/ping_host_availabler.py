import logging
import time
from typing import List, Optional, Dict
import requests
from requests import Response, Session

from byteplus_rec_core import constant, utils
from byteplus_rec_core.abtract_host_availabler import AbstractHostAvailabler, HostAvailabilityScore

log = logging.getLogger(__name__)

_DEFAULT_WINDOW_SIZE: int = 60
_DEFAULT_PING_SCHEMA = "http"
_DEFAULT_PING_URL_FORMAT: str = "{}://{}/predict/api/ping"
_DEFAULT_PING_TIMEOUT_SECONDS: float = 0.3
_DEFAULT_PING_INTERVAL_SECONDS: float = 1
_DEFAULT_FETCH_HOST_INTERVAL_SECONDS: float = 10


class Config(object):
    def __init__(self,
                 ping_url_format: str = _DEFAULT_PING_URL_FORMAT,
                 window_size: int = _DEFAULT_WINDOW_SIZE,
                 ping_timeout_seconds: float = _DEFAULT_PING_TIMEOUT_SECONDS,
                 ping_interval_seconds: float = _DEFAULT_PING_INTERVAL_SECONDS,
                 fetch_host_interval_seconds: float = _DEFAULT_FETCH_HOST_INTERVAL_SECONDS):
        self.ping_url_format = ping_url_format
        self.window_size = window_size
        if window_size < 0:
            self.window_size = _DEFAULT_WINDOW_SIZE
        self.ping_timeout_seconds = ping_timeout_seconds
        self.ping_interval_seconds = ping_interval_seconds
        self.fetch_host_interval_seconds = fetch_host_interval_seconds


class PingHostAvailabler(AbstractHostAvailabler):
    def __init__(self, default_hosts: Optional[List[str]] = None,
                 project_id: Optional[str] = None,
                 config: Optional[Config] = None,
                 main_host: Optional[str] = None,
                 skip_fetch_hosts: Optional[bool] = False):
        if config is None:
            config = Config()
        self._config: Config = config
        self._ping_http_cli: Session = requests.Session()
        self._host_window_map: Dict[str, _Window] = {}
        for host in default_hosts:
            self._host_window_map[host] = _Window(self._config.window_size)
        super().__init__(
            default_hosts,
            project_id,
            main_host,
            skip_fetch_hosts,
            self._config.fetch_host_interval_seconds,
            self._config.ping_interval_seconds
        )
        return

    def do_score_hosts(self, hosts: List[str]) -> List[HostAvailabilityScore]:
        log.debug("[ByteplusSDK] do score hosts:'%s'", hosts)
        if len(hosts) == 1:
            return [HostAvailabilityScore(hosts[0], 0.0)]
        host_availability_scores = []
        for host in hosts:
            window = self._host_window_map.get(host, None)
            if window is None:
                window = _Window(self._config.window_size)
                self._host_window_map[host] = window
            success = utils.ping(self.project_id, self._ping_http_cli, self._config.ping_url_format,
                                 _DEFAULT_PING_SCHEMA, host, self._config.ping_timeout_seconds)
            window.put(success)
            host_availability_scores.append(HostAvailabilityScore(host, 1 - window.failure_rate()))
        return host_availability_scores


class _Window(object):
    def __init__(self, size: int):
        self.size: int = size
        self.head: int = size - 1
        self.tail: int = 0
        self.items: list = [True] * size
        self.failure_count: int = 0

    def put(self, success: bool) -> None:
        if not success:
            self.failure_count += 1
        self.head = (self.head + 1) % self.size
        self.items[self.head] = success
        self.tail = (self.tail + 1) % self.size
        removing_item = self.items[self.tail]
        if not removing_item:
            self.failure_count -= 1

    def failure_rate(self) -> float:
        return self.failure_count / self.size
