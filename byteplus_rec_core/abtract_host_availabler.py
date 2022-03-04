import copy
import json
from abc import abstractmethod
import logging
import threading
import time
from typing import List, Optional, Dict

import requests
from requests import Response
from byteplus_rec_core import utils

from byteplus_rec_core.exception import BizException
from byteplus_rec_core import constant

log = logging.getLogger(__name__)

_FETCH_HOST_URL_FORMAT: str = "http://{}/data/api/sdk/host?project_id={}"
_HOST_AVAILABLE_SCORE_FORMAT: str = "host={}, score={}"


class HostAvailabilityScore:
    def __init__(self, host: Optional[str] = None,
                 score: Optional[float] = None):
        self.host = host
        self.score = score

    def __str__(self):
        return _HOST_AVAILABLE_SCORE_FORMAT.format(self.host, self.score)


class AbstractHostAvailabler(object):
    _host_config: Dict[str, List[str]] = None

    def __init__(self, project_id: str, default_hosts: List[str]):
        self._abort: bool = False
        self._project_id: str = project_id
        self.set_hosts(default_hosts)
        self.init()

    def init(self):
        if not utils.is_empty_str(self._project_id):
            self._fetch_hosts_from_server()
            threading.Thread(target=self._start_schedule_fetch_hosts).start()
        threading.Thread(target=self._start_schedule_update_hosts).start()

    def _start_schedule_update_hosts(self):
        if self._abort:
            return
        self._score_and_update_hosts(self._host_config)
        timer = threading.Timer(1, self._start_schedule_update_hosts)
        timer.start()
        return

    def _start_schedule_fetch_hosts(self):
        if self._abort:
            return
        self._fetch_hosts_from_server()
        # a timer only execute once after spec duration
        timer = threading.Timer(10, self._start_schedule_fetch_hosts)
        timer.start()
        return

    def set_hosts(self, hosts: List[str]):
        if hosts is None or len(hosts) == 0:
            raise BizException("host array is empty")
        self._stop_fetch_hosts_from_server()
        self._score_and_update_hosts({"*": hosts})

    def _stop_fetch_hosts_from_server(self):
        self.shutdown()

    def _fetch_hosts_from_server(self):
        url: str = _FETCH_HOST_URL_FORMAT.format(self.get_host("*"), self._project_id)
        for i in range(3):
            rsp_host_config: Dict[str, List[str]] = self._do_fetch_hosts_from_server(url)
            if not rsp_host_config:
                continue
            if self._is_server_hosts_not_updated(rsp_host_config):
                log.warning("[ByteplusSDK] hosts from server are not changed, config:'%s'", rsp_host_config)
                return
            if "*" not in rsp_host_config or rsp_host_config["*"] == []:
                log.warning("[ByteplusSDK] hosts from server is empty, url:'%s' config:'%s'", url, rsp_host_config)
                return
            self._score_and_update_hosts(rsp_host_config)
            return
        log.warning("[ByteplusSDK] fetch host from server fail although retried, url:'%s'", url)

    def _do_fetch_hosts_from_server(self, url: str) -> Dict[str, List[str]]:
        start = time.time()
        headers = None
        try:
            rsp: Response = requests.get(url, headers=headers, timeout=10)
            cost = int((time.time() - start) * 1000)
            if rsp.status_code == constant.HTTP_STATUS_NOT_FOUND:
                log.warning("[ByteplusSDK] fetch host from server return not found status, cost:'%s' ms", cost)
                return {}
            if rsp.status_code != constant.HTTP_STATUS_OK:
                log.warning("[ByteplusSDK] fetch host from server return not ok status, cost:'%s' ms, err:'%s'", cost,
                            rsp.reason)
                return {}
            rsp_str: str = str(rsp.content)
            log.warning("[ByteplusSDK] fetch host from server, cost:'%s' ms, rsp:'%s'", cost, rsp_str)
            if rsp_str is not None and len(rsp_str) > 0:
                return json.loads(rsp.text)
            return {}
        except BaseException as e:
            cost = int((time.time() - start) * 1000)
            log.warning("[ByteplusSDK] fetch host from server err, url:'%s', cost:'%s' ms, err:'%s'", url, cost, e)
            return {}

    def _is_server_host_not_update(self, new_host_config: Dict[str, List[str]]) -> bool:
        if self._host_config is None:
            return False
        if len(new_host_config.keys()) != len(self._host_config.keys()):
            return False
        for path, new_path_hosts in new_host_config:
            old_path_hosts = self._host_config[path]
            if len(new_path_hosts) != len(old_path_hosts):
                return False
            if new_path_hosts != old_path_hosts:
                return False
        return True

    def _score_and_update_hosts(self, host_config: Dict[str, List[str]]):
        hosts: List[str] = self._distinct_hosts(host_config)
        new_host_scores: List[HostAvailabilityScore] = self.do_score_hosts(hosts)
        log.debug("[ByteplusSDK] score hosts result: '%s'", new_host_scores)
        if new_host_scores is None or len(new_host_scores) == 0:
            log.error("[ByteplusSDK] scoring hosts return an empty list")
            return
        new_host_config: Dict[str, List[str]] = self._copy_and_sort_host(host_config, new_host_scores)
        if self._is_server_host_not_update(new_host_config):
            log.debug("[ByteplusSDK] host order is not changed, '%s'", new_host_config)
            return
        log.warning("[ByteplusSDK] set new host config: '%s', old config: '%s'", new_host_config,
                    self._host_config)
        self._host_config = new_host_config

    def _distinct_hosts(self, host_config: Dict[str, List[str]]):
        host_set = set()
        for path in host_config:
            host_set.update(host_config[path])
        return list(host_set)

    @abstractmethod
    def do_score_hosts(self, hosts: List[str]) -> List[HostAvailabilityScore]:
        raise NotImplementedError

    def _copy_and_sort_host(self, host_config: Dict[str, List[str]], new_host_scores: List[HostAvailabilityScore]) -> \
            Dict[str, List[str]]:
        host_score_index = {}
        for host_score in new_host_scores:
            host_score_index[host_score.host] = host_score.score
        new_host_config = {}
        for path in host_config:
            new_hosts: List[str] = copy.deepcopy(host_config[path])
            # sort from big to small
            new_hosts = sorted(new_hosts, key=lambda s: host_score_index.get(s, 0.0), reverse=True)
            new_host_config[path] = new_hosts
        return new_host_config

    def _is_server_hosts_not_updated(self, new_host_config: Dict[str, List[str]]) -> bool:
        if self._host_config is None or new_host_config is None:
            return False
        for path in self._host_config:
            new_host: List[str] = new_host_config.get(path)
            if new_host != self._host_config[path]:
                return False
        return True

    def get_host(self, path: str) -> str:
        if path in self._host_config and len(self._host_config[path]) > 0:
            return self._host_config.get(path)[0]
        return self._host_config.get("*")[0]

    def shutdown(self):
        self._abort = True
