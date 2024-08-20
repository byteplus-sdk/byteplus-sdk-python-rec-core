import copy
import json
import uuid
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
from byteplus_rec_core.metrics.metrics import Metrics
from byteplus_rec_core.metrics.metrics_log import MetricsLog

log = logging.getLogger(__name__)

_FETCH_HOST_URL_FORMAT: str = "http://{}/data/api/sdk/host?project_id={}"
_HOST_AVAILABLE_SCORE_FORMAT: str = "host={}, score={}"
_DEFAULT_SCORE_HOST_INTERVAL_SECONDS: float = 1
_MAIN_HOST_AVAILABLE_SCORE: float = 0.9


class HostAvailabilityScore:
    def __init__(self, host: Optional[str] = None, score: Optional[float] = None):
        self.host = host
        self.score = score

    def __str__(self):
        return _HOST_AVAILABLE_SCORE_FORMAT.format(self.host, self.score)


class HostScoreResult:
    def __init__(self, host_scores: Optional[List[HostAvailabilityScore]] = None):
        self.host_scores = host_scores

    def __str__(self):
        if self.host_scores is None:
            return '[]'
        host_score_str_list = [host_score.__str__() for host_score in self.host_scores]
        return '[{}]'.format(','.join(host_score_str_list))


# class AvailablerConfig(object):
#     def __init__(self, default_hosts: Optional[List[str]] = None,
#                  project_id: Optional[str] = None,
#                  host_config: Optional[Dict[str, List[str]]] = None):
#         self.default_hosts = default_hosts
#         self.project_id = project_id
#         self.host_config = host_config


class AbstractHostAvailabler(object):
    def __init__(self, default_hosts: Optional[List[str]] = None,
                 project_id: Optional[str] = None,
                 main_host: Optional[str] = None,
                 score_host_interval_seconds: Optional[float] = _DEFAULT_SCORE_HOST_INTERVAL_SECONDS):
        self.project_id = project_id
        self._default_hosts = default_hosts
        self._main_host = main_host
        self._host_config = None
        self._score_host_interval_seconds = score_host_interval_seconds
        self._cancel = None
        self.init()

    def init(self):
        self.set_hosts(self._default_hosts)
        self._cancel = utils.time_schedule(self._start_score_and_update_hosts, self._score_host_interval_seconds)

    def set_hosts(self, hosts: List[str]):
        if hosts is None or len(hosts) == 0:
            raise BizException("host array is empty")
        self._default_hosts = hosts
        self._score_and_update_hosts({"*": hosts})

    def _start_score_and_update_hosts(self):
        self._score_and_update_hosts(self._host_config)
        return

    def _score_and_update_hosts(self, host_config: Dict[str, List[str]]):
        log_id: str = "score_" + str(uuid.uuid1())
        hosts: List[str] = self._distinct_hosts(host_config)
        new_host_scores: List[HostAvailabilityScore] = self.do_score_hosts(hosts)
        MetricsLog.info(log_id, "[ByteplusSDK][Score] score hosts: project_id: {}, result:{}",
                        self.project_id, HostScoreResult(new_host_scores))
        log.debug("[ByteplusSDK] score hosts result: '%s'", HostScoreResult(new_host_scores))
        if new_host_scores is None or len(new_host_scores) == 0:
            metrics_tags = [
                "type:scoring_hosts_return_empty_list",
                "project_id:" + self.project_id,
            ]
            Metrics.counter(constant.METRICS_KEY_COMMON_ERROR, 1, *metrics_tags)
            MetricsLog.error(log_id, "[ByteplusSDK][Score] scoring hosts return an empty list, project_id:{}",
                             self.project_id)
            log.error("[ByteplusSDK] scoring hosts return an empty list")
            return
        new_host_config: Dict[str, List[str]] = self._copy_and_sort_host(host_config, new_host_scores)
        if self._is_host_config_not_update(self._host_config, new_host_config):
            MetricsLog.info(log_id, "[ByteplusSDK][Score] host order is not changed, project_id: {}, config:{}",
                            self.project_id, new_host_config)
            log.debug("[ByteplusSDK] host order is not changed, '%s'", new_host_config)
            return
        metrics_tags = [
            "type:set_new_host_config",
            "project_id:" + self.project_id,
        ]
        Metrics.counter(constant.METRICS_KEY_COMMON_INFO, 1, *metrics_tags)
        MetricsLog.info(log_id, "[ByteplusSDK][Score] set new host config:{}, old config: {}, project_id: {}",
                        new_host_config, self._host_config, self.project_id)
        log.warning("[ByteplusSDK] set new host config: '%s', old config: '%s'", new_host_config,
                    self._host_config)
        self._host_config = new_host_config

    @staticmethod
    def _distinct_hosts(host_config: Dict[str, List[str]]):
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
            # main_host is prioritized for use when available
            if self._main_host is not None and self._main_host == host_score.host \
                    and host_score.score >= _MAIN_HOST_AVAILABLE_SCORE:
                host_score.score = 1 + host_score.score
            host_score_index[host_score.host] = host_score.score
        new_host_config = {}
        for path in host_config:
            new_hosts: List[str] = copy.deepcopy(host_config[path])
            # sort from big to small
            new_hosts = sorted(new_hosts, key=lambda s: host_score_index.get(s, 0.0), reverse=True)
            new_host_config[path] = new_hosts
        return new_host_config

    @staticmethod
    def _is_host_config_not_update(old_host_config: Dict[str, List[str]],
                                   new_host_config: Dict[str, List[str]]) -> bool:
        if old_host_config is None:
            return False
        if new_host_config is None:
            return True
        if len(old_host_config) != len(new_host_config):
            return False
        for path in old_host_config:
            new_hosts = new_host_config.get(path)
            old_hosts = old_host_config.get(path)
            if new_hosts != old_hosts:
                return False
        return True

    def get_hosts(self) -> List[str]:
        return self._distinct_hosts(self._host_config)

    def get_host(self, path: str) -> str:
        hosts = self._host_config.get(path)
        if hosts is None or len(hosts) == 0:
            return self._host_config.get("*")[0]
        return hosts[0]

    def shutdown(self):
        if self._cancel is not None:
            self._cancel()
