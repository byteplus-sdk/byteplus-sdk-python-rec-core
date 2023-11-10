import threading
from typing import Optional, Union, List
import logging

from google.protobuf.message import Message

from byteplus_rec_core.abtract_host_availabler import AbstractHostAvailabler
from byteplus_rec_core.host_availabler_factory import HostAvailablerFactory
from byteplus_rec_core.http_caller import Config as HTTPCallerConfig
from byteplus_rec_core.http_caller import _HTTPCaller
from byteplus_rec_core.metrics.metrics_collector import MetricsCollector
from byteplus_rec_core.metrics.metrics_option import MetricsCfg
from byteplus_rec_core.option import Option
from byteplus_rec_core.abstract_region import AbstractRegion
from byteplus_rec_core.auth import _Credential
from byteplus_rec_core import utils

log = logging.getLogger(__name__)


class HTTPClient(object):
    def __init__(self, http_caller: _HTTPCaller, host_availabler: AbstractHostAvailabler, schema: str, project_id: str):
        self._http_caller = http_caller
        self._host_availabler = host_availabler
        self._schema = schema
        self._project_id = project_id

    def do_pb_request(self, path: str, request: Message, response: Message, *opts: Option):
        self._http_caller.do_pb_request(self._build_url(path), request, response, *opts)

    def do_json_request(self, path: str, request: Union[dict, list], *opts: Option) -> Union[dict, list]:
        return self._http_caller.do_json_request(self._build_url(path), request, *opts)

    def _build_url(self, path: str):
        host: str = self._host_availabler.get_host(path)
        return utils.build_url(self._schema, host, path)

    def shutdown(self):
        self._host_availabler.shutdown()
        self._http_caller.shutdown()


_global_host_availabler_lock = threading.Lock()
_global_host_availabler: Optional[AbstractHostAvailabler] = None


class _HTTPClientBuilder(object):
    def __init__(self):
        self._tenant_id: Optional[str] = None
        self._project_id: Optional[str] = None
        self._use_air_auth: Optional[bool] = False
        self._air_auth_token: Optional[str] = None
        self._auth_ak: Optional[str] = None
        self._auth_sk: Optional[str] = None
        self._auth_service: Optional[str] = None
        self._schema: Optional[str] = None
        self._hosts: Optional[List[str]] = None
        self._main_host: Optional[str] = None
        self._region: Optional[AbstractRegion] = None
        self._host_availabler_factory: Optional[HostAvailablerFactory] = None
        self._keep_alive: Optional[bool] = False
        self._caller_config: Optional[HTTPCallerConfig] = None
        self._host_availabler: Optional[AbstractHostAvailabler] = None
        self._metrics_cfg: Optional[MetricsCfg] = None

    def tenant_id(self, tenant_id: str):
        self._tenant_id = tenant_id
        return self

    def project_id(self, project_id: str):
        self._project_id = project_id
        return self

    def use_air_auth(self, use_air_auth: bool):
        self._use_air_auth = use_air_auth
        return self

    def air_auth_token(self, air_auth_token: str):
        self._air_auth_token = air_auth_token
        return self

    def auth_ak(self, ak: str):
        self._auth_ak = ak
        return self

    def auth_sk(self, sk: str):
        self._auth_sk = sk
        return self

    def auth_service(self, auth_service: str):
        self._auth_service = auth_service
        return self

    def schema(self, schema: str):
        self._schema = schema
        return self

    def hosts(self, hosts: list):
        self._hosts = hosts
        return self

    def main_host(self, main_host: str):
        self._main_host = main_host
        return self

    def region(self, region: AbstractRegion):
        self._region = region
        return self

    def host_availabler_factory(self, host_availabler_factory: HostAvailablerFactory):
        self._host_availabler_factory = host_availabler_factory
        return self

    def keep_alive(self, keep_alive: bool):
        self._keep_alive = keep_alive
        return self

    def caller_config(self, caller_config: HTTPCallerConfig):
        self._caller_config = caller_config
        return self

    def metrics_cfg(self, metrics_cfg: MetricsCfg):
        self._metrics_cfg = metrics_cfg
        return self

    def build(self) -> HTTPClient:
        global _global_host_availabler

        self._check_required_field()
        self._fill_default()
        if not MetricsCollector.is_initialed() and self._metrics_cfg is not None:
            if self._metrics_cfg.enable_metrics or self._metrics_cfg.enable_metrics_log:
                self._init_global_host_availabler()
        MetricsCollector.init(self._metrics_cfg, _global_host_availabler)
        return HTTPClient(self._new_http_caller(), self._host_availabler, self._schema, self._project_id)

    def _check_required_field(self):
        if self._tenant_id is None or len(self._tenant_id) == 0:
            raise Exception("tenant id is null")
        self._check_auth_required_field()
        if self._region is None:
            raise Exception("region is null")

    def _check_auth_required_field(self):
        if self._use_air_auth:
            if utils.is_empty_str(self._air_auth_token):
                raise Exception("token cannot be null")
            return

        if utils.is_all_empty_str([self._auth_ak, self._auth_sk]):
            raise Exception("ak and sk cannot be null")

    def _fill_default(self):
        if utils.is_empty_str(self._schema):
            self._schema = "https"
        # # fill hostAvailabler.
        if self._host_availabler_factory is None:
            self._host_availabler_factory = HostAvailablerFactory()
        self._host_availabler: AbstractHostAvailabler = self._new_host_availabler()

        # fill default caller config.
        if self._caller_config is None:
            self._caller_config = HTTPCallerConfig()

    def _new_host_availabler(self) -> AbstractHostAvailabler:
        if self._hosts is not None and len(self._hosts) > 0:
            return self._host_availabler_factory.new_host_availabler(hosts=self._hosts,
                                                                     project_id=self._project_id,
                                                                     main_host=self._main_host,
                                                                     skip_fetch_hosts=True)
        return self._host_availabler_factory.new_host_availabler(hosts=self._region.get_hosts(),
                                                                 project_id=self._project_id,
                                                                 main_host=self._main_host,
                                                                 skip_fetch_hosts=False)

    def _init_global_host_availabler(self):
        global _global_host_availabler
        global _global_host_availabler_lock

        _global_host_availabler_lock.acquire()
        if _global_host_availabler is not None:
            _global_host_availabler_lock.release()
            return
        _global_host_availabler = self._new_host_availabler()
        _global_host_availabler_lock.release()

    def _new_http_caller(self) -> _HTTPCaller:
        if self._use_air_auth:
            return _HTTPCaller(
                self._project_id,
                self._tenant_id,
                self._air_auth_token,
                self._host_availabler,
                self._caller_config,
                self._schema,
                self._keep_alive
            )
        credential: _Credential = _Credential(
            self._auth_ak,
            self._auth_sk,
            self._auth_service,
            self._region.get_auth_region(),
        )
        _http_caller: _HTTPCaller = _HTTPCaller(
            self._project_id,
            self._tenant_id,
            self._air_auth_token,
            self._host_availabler,
            self._caller_config,
            self._schema,
            self._keep_alive,
            credential
        )
        return _http_caller


def new_http_client_builder() -> _HTTPClientBuilder:
    return _HTTPClientBuilder()
