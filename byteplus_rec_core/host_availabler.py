from abc import abstractmethod
import logging
import threading
import time
from typing import List, Optional, Dict

import requests
from requests import Response

log = logging.getLogger(__name__)

_DEFAULT_PING_INTERVAL_SECONDS: int = 1
_DEFAULT_WINDOW_SIZE: int = 60
_DEFAULT_FAILURE_RATE_THRESHOLD: float = 0.1
_DEFAULT_PING_URL_FORMAT: str = "http://{}/predict/api/ping"
_DEFAULT_PING_TIMEOUT_SECONDS: float = 0.3
_PING_SUCCESS_HTTP_CODE = 200


class HostAvailabler(object):
    @abstractmethod
    def get_available_hosts(self) -> list:
        raise NotImplementedError

    @abstractmethod
    def hosts(self) -> Optional[List[str]]:
        raise NotImplementedError

    @abstractmethod
    def host_header(self) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def set_hosts(self, hosts: List[str]):
        raise NotImplementedError

    @abstractmethod
    def set_host_header(self, host_header: Optional[str]):
        raise NotImplementedError

    @abstractmethod
    def get_host(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def shutdown(self):
        raise NotImplementedError


class PingHostAvailablerConfig(object):
    def __init__(self, hosts: Optional[List[str]],
                 host_header: Optional[str] = None,
                 ping_url_format=_DEFAULT_PING_URL_FORMAT,
                 window_size=_DEFAULT_WINDOW_SIZE,
                 failure_rate_threshold=_DEFAULT_FAILURE_RATE_THRESHOLD,
                 ping_interval_seconds=_DEFAULT_PING_INTERVAL_SECONDS,
                 ping_timeout_seconds=_DEFAULT_PING_TIMEOUT_SECONDS):
        self.hosts = hosts
        self.host_header = host_header
        self.ping_url_format = ping_url_format
        self.window_size = window_size
        self.failure_rate_threshold = failure_rate_threshold
        self.ping_interval_seconds = ping_interval_seconds
        self.ping_timeout_seconds = ping_timeout_seconds


class _PingHostAvailabler(HostAvailabler):
    def __init__(self, config: PingHostAvailablerConfig):
        self._config: PingHostAvailablerConfig = config
        self._available_hosts: List[str] = config.hosts
        if len(config.hosts) <= 1:
            return
        self._host_window_map: Dict[str, _Window] = {}
        self._abort: bool = False
        for host in config.hosts:
            self._host_window_map[host] = _Window(config.window_size)
        threading.Thread(target=self._start_schedule).start()
        return

    def get_available_hosts(self) -> List[str]:
        return self._available_hosts

    def hosts(self) -> Optional[List[str]]:
        return self._config.hosts

    def host_header(self) -> Optional[str]:
        return self._config.host_header

    def set_hosts(self, hosts: List[str]):
        self._config.hosts = hosts

    def set_host_header(self, host_header: Optional[str]):
        self._config.host_header = host_header

    def get_host(self) -> str:
        return self._available_hosts[0]

    def shutdown(self):
        self._abort = True

    def _start_schedule(self) -> None:
        if self._abort:
            return
        # log.debug("[ByteplusSDK] http")
        self._check_host()
        # a timer only execute once after spec duration
        timer = threading.Timer(self._config.ping_interval_seconds, self._start_schedule)
        timer.start()
        return

    def _check_host(self) -> None:
        available_hosts = []
        for host in self._config.hosts:
            window = self._host_window_map[host]
            success = self._ping(host)
            window.put(success)
            if window.failure_rate() < self._config.failure_rate_threshold:
                available_hosts.append(host)
        self._available_hosts = available_hosts
        # Make sure that at least have host returns
        if len(self._available_hosts) < 1:
            self._available_hosts = self._config.hosts
        if len(self._available_hosts) == 1:
            return
        self._available_hosts.sort(key=lambda item: self._host_window_map[item].failure_rate())

    def _ping(self, host) -> bool:
        url: str = self._config.ping_url_format.format(host)
        start = time.time()
        headers = None
        if self._config.host_header is not None and len(self._config.host_header) > 0:
            headers = {"Host": self._config.host_header}
        try:
            rsp: Response = requests.get(url, headers=headers, timeout=self._config.ping_timeout_seconds)
        except BaseException as e:
            log.warning("[ByteplusSDK] ping find err, host:'%s' err:'%s'", host, e)
            return False
        finally:
            cost = int((time.time() - start) * 1000)
            log.debug("[ByteplusSDK] http path:%s, cost:%dms", url, cost)
        return rsp.status_code == _PING_SUCCESS_HTTP_CODE


def new_ping_host_availabler(config: PingHostAvailablerConfig) -> _PingHostAvailabler:
    return _PingHostAvailabler(config)


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
