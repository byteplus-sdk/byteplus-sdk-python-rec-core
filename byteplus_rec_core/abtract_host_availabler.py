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
_DEFAULT_FETCH_HOST_INTERVAL_SECONDS: float = 10
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
                 skip_fetch_hosts: Optional[bool] = False,
                 fetch_host_interval_seconds: Optional[float] = _DEFAULT_FETCH_HOST_INTERVAL_SECONDS,
                 score_host_interval_seconds: Optional[float] = _DEFAULT_SCORE_HOST_INTERVAL_SECONDS):
        self.project_id = project_id
        self._default_hosts = default_hosts
        self._main_host = main_host
        self._skip_fetch_hosts = skip_fetch_hosts
        self._host_config = None
        self._abort: bool = False
        self._close_fetch_hosts_flag: bool = False
        self._fetch_hosts_thread = None
        self._fetch_host_interval_seconds = fetch_host_interval_seconds
        self._score_host_interval_seconds = score_host_interval_seconds
        self.init()

    def init(self):
        self.set_hosts(self._default_hosts)
        if not self._skip_fetch_hosts:
            self._fetch_hosts_from_server()
            self._fetch_hosts_thread = threading.Thread(target=self._start_fetch_hosts_from_server)
            self._fetch_hosts_thread.start()
        threading.Thread(target=self._start_score_and_update_hosts).start()

    def set_hosts(self, hosts: List[str]):
        if hosts is None or len(hosts) == 0:
            raise BizException("host array is empty")
        self._default_hosts = hosts
        self._stop_fetch_hosts_from_server()
        self._score_and_update_hosts({"*": hosts})

    def _stop_fetch_hosts_from_server(self):
        # do not need to close fetch thread when setting default hosts
        # close fetch thread only when set_hosts was called by user
        if self._fetch_hosts_thread is not None:
            self._close_fetch_hosts_flag = True

    def _start_fetch_hosts_from_server(self):
        if self._close_fetch_hosts_flag or self._abort:
            return
        time.sleep(self._fetch_host_interval_seconds)
        self._fetch_hosts_from_server()
        self._start_fetch_hosts_from_server()
        return

    def _start_score_and_update_hosts(self):
        if self._abort:
            return
        time.sleep(self._score_host_interval_seconds)
        self._score_and_update_hosts(self._host_config)
        self._start_score_and_update_hosts()
        return

    def _fetch_hosts_from_server(self):
        url: str = _FETCH_HOST_URL_FORMAT.format(self._default_hosts[0], self.project_id)
        req_id: str = "fetch_" + str(uuid.uuid1())
        for i in range(3):
            rsp_host_config: Dict[str, List[str]] = self._do_fetch_hosts_from_server(req_id, url)
            if not rsp_host_config:
                continue
            if self._is_server_hosts_not_updated(rsp_host_config):
                MetricsLog.info(req_id,
                                "[ByteplusSDK][Fetch] hosts from server are not changed, project_id:{}, config: {}",
                                self.project_id, rsp_host_config)
                log.debug("[ByteplusSDK] hosts from server are not changed, config:'%s'", rsp_host_config)
                return
            if "*" not in rsp_host_config or rsp_host_config["*"] == []:
                metrics_tags = [
                    "type:no_default_hosts",
                    "project_id:" + self.project_id,
                    "url:" + utils.escape_metrics_tag_value(url),
                ]
                Metrics.counter(constant.METRICS_KEY_COMMON_WARN, 1, *metrics_tags)
                MetricsLog.warn(req_id,
                                "[ByteplusSDK][Fetch] no default value in hosts from server, project_id:{}, config: {}",
                                self.project_id, rsp_host_config)
                log.warning("[ByteplusSDK] no default value in hosts from server, config:'%s'", rsp_host_config)
                return
            self._score_and_update_hosts(rsp_host_config)
            return
        metrics_tags = [
            "type:fetch_host_fail_although_retried",
            "project_id:" + self.project_id,
            "url:" + utils.escape_metrics_tag_value(url),
        ]
        Metrics.counter(constant.METRICS_KEY_COMMON_ERROR, 1, *metrics_tags)
        MetricsLog.warn(req_id,
                        "[ByteplusSDK][Fetch] fetch host from server fail although retried, project_id:{}, url: {}",
                        self.project_id, url)
        log.warning("[ByteplusSDK] fetch host from server fail although retried, url:'%s'", url)

    def _is_server_hosts_not_updated(self, new_host_config: Dict[str, List[str]]) -> bool:
        if self._host_config is None or new_host_config is None:
            return False
        if len(self._host_config) != len(new_host_config):
            return False
        for path in self._host_config:
            new_host: List[str] = new_host_config.get(path)
            old_host: List[str] = self._host_config.get(path)
            if old_host is None or new_host is None or len(old_host) == 0:
                return False
            if len(old_host) != len(new_host):
                return False
            if not set(old_host).issubset(set(new_host)):
                return False
        return True

    def _do_fetch_hosts_from_server(self, req_id: str, url: str) -> Dict[str, List[str]]:
        start = time.time()
        try:
            headers = {
                "Request-Id": req_id,
            }
            rsp: Response = requests.get(url, headers=headers, timeout=10)
            cost = int((time.time() - start) * 1000)
            if rsp.status_code == constant.HTTP_STATUS_NOT_FOUND:
                metrics_tags = [
                    "type:fetch_host_status_400",
                    "project_id:" + self.project_id,
                    "url:" + utils.escape_metrics_tag_value(url),
                ]
                Metrics.counter(constant.METRICS_KEY_COMMON_ERROR, 1, *metrics_tags)
                log_format = "[ByteplusSDK][Fetch] fetch host from server return not found status project_id:{}, " \
                             "cost: {}ms"
                MetricsLog.warn(req_id, log_format, self.project_id, cost)
                log.warning("[ByteplusSDK] fetch host from server return not found status, cost:%dms", cost)
                return {}
            if rsp.status_code != constant.HTTP_STATUS_OK:
                metrics_tags = [
                    "type:fetch_host_not_ok",
                    "project_id:" + self.project_id,
                    "url:" + utils.escape_metrics_tag_value(url),
                ]
                Metrics.counter(constant.METRICS_KEY_COMMON_ERROR, 1, *metrics_tags)
                log_format = "[ByteplusSDK][Fetch] fetch host from server return not ok status, project_id:{}, " \
                             "cost: {}ms, err:{}"
                MetricsLog.warn(req_id, log_format, self.project_id, cost, rsp.reason)
                log.warning("[ByteplusSDK] fetch host from server return not ok status, cost:%dms, err:'%s'",
                            cost, rsp.reason)
                return {}
            rsp_str: str = str(rsp.content)
            metrics_tags = [
                "project_id:" + self.project_id,
                "url:" + utils.escape_metrics_tag_value(url),
            ]
            Metrics.timer(constant.METRICS_KEY_REQUEST_TOTAL_COST, cost, *metrics_tags)
            Metrics.counter(constant.METRICS_KEY_REQUEST_COUNT, 1, *metrics_tags)
            log.debug("[ByteplusSDK] fetch host from server, cost:%dms, rsp:'%s'", cost, rsp_str)
            if rsp_str is not None and len(rsp_str) > 0:
                return json.loads(rsp.text)
            return {}
        except BaseException as e:
            cost = int((time.time() - start) * 1000)
            metrics_tags = [
                "type:fetch_host_fail",
                "project_id:" + self.project_id,
                "url:" + utils.escape_metrics_tag_value(url),
            ]
            Metrics.counter(constant.METRICS_KEY_COMMON_ERROR, 1, *metrics_tags)
            log_format = "[ByteplusSDK][Fetch] fetch host from server err, project_id:{}, url:{}, cost:{}ms, err:{}"
            MetricsLog.warn(req_id, log_format, self.project_id, url, cost, e)
            log.warning("[ByteplusSDK] fetch host from server err, url:'%s', cost %dms, err:'%s'", url, cost, e)
            return {}

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
        self._abort = True
