import logging
import time
from typing import List, Optional, Dict
import requests
from requests import Response

from byteplus_rec_core import constant
from byteplus_rec_core.abtract_host_availabler import AbstractHostAvailabler, HostAvailabilityScore

log = logging.getLogger(__name__)

_DEFAULT_WINDOW_SIZE: int = 60
_DEFAULT_PING_URL_FORMAT: str = "http://{}/predict/api/ping"
_DEFAULT_PING_TIMEOUT_SECONDS: float = 0.3


class Config(object):
    def __init__(self,
                 ping_url_format=_DEFAULT_PING_URL_FORMAT,
                 window_size=_DEFAULT_WINDOW_SIZE,
                 ping_timeout_seconds=_DEFAULT_PING_TIMEOUT_SECONDS):
        self.ping_url_format = ping_url_format
        self.window_size = window_size
        if window_size < 0:
            self.window_size = _DEFAULT_WINDOW_SIZE
        self.ping_timeout_seconds = ping_timeout_seconds


class _PingHostAvailabler(AbstractHostAvailabler):
    def __init__(self, default_hosts: Optional[List[str]] = None,
                 project_id: Optional[str] = None,
                 config: Optional[Config] = Config()):
        super().__init__(default_hosts, project_id)
        self._config: Config = config
        self._host_window_map: Dict[str, _Window] = {}
        for host in default_hosts:
            self._host_window_map[host] = _Window(self._config.window_size)
        return

    def do_score_hosts(self, hosts: List[str]) -> List[HostAvailabilityScore]:
        log.debug("[ByteplusSDK] do score hosts:'%s'", hosts)
        if len(hosts) == 1:
            return [HostAvailabilityScore(hosts[0], 0.0)]
        host_availability_scores = []
        for host in hosts:
            window = self._host_window_map[host]
            if window is None:
                window = _Window(self._config.window_size)
                self._host_window_map[host] = window
            success = self._ping(host)
            window.put(success)
            host_availability_scores.append(HostAvailabilityScore(host, 1 - window.failure_rate()))
        return host_availability_scores

    def _ping(self, host) -> bool:
        url: str = self._config.ping_url_format.format(host)
        start = time.time()
        try:
            rsp: Response = requests.get(url, headers=None, timeout=self._config.ping_timeout_seconds)
            cost = int((time.time() - start) * 1000)
            if self._is_ping_success(rsp):
                log.debug("[ByteplusSDK] ping success, host:'%s' cost:%dms", host, cost)
                return True
            log.warning("[ByteplusSDK] ping fail, host:'%s', cost:%dms, status:'%s'", host, cost, rsp.status_code)
            return False
        except BaseException as e:
            cost = int((time.time() - start) * 1000)
            log.warning("[ByteplusSDK] ping find err, host:'%s', cost:%dms, err:'%s'", host, cost, e)
            return False

    @staticmethod
    def _is_ping_success(rsp: Response):
        if rsp.status_code != constant.HTTP_STATUS_OK:
            return False
        if rsp.content is None:
            return False
        rsp_str: str = str(rsp.content)
        return len(rsp_str) < 20 and "pong" in rsp_str


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
