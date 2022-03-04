from typing import Optional, Union, List
import logging

from google.protobuf.message import Message
from byteplus_rec_core.host_availabler import HostAvailabler
from byteplus_rec_core.ping_host_availabler import _PingHostAvailabler, PingHostAvailablerConfig, \
    new_ping_host_availabler
from byteplus_rec_core.http_caller import _HTTPCaller
from byteplus_rec_core.option import Option
from byteplus_rec_core.abstract_region import AbstractRegion
from byteplus_rec_core.volc_auth import _Credential
from byteplus_rec_core import utils

log = logging.getLogger(__name__)


class HTTPClient(object):
    def __init__(self, http_caller: _HTTPCaller, host_availabler: HostAvailabler, schema: str, project_id: str):
        self._http_caller = http_caller
        self._host_availabler = host_availabler
        self._schema = schema
        self._project_id = project_id

    def do_pb_request(self, path: str, request: Message, response: Message, *opts: Option):
        self._http_caller.do_pb_request(self._build_url(path), request, response, *opts)

    def do_json_request(self, path: str, request: Union[dict, list], *opts: Option) -> Union[dict, list]:
        return self._http_caller.do_json_request(self._build_url(path), request, *opts)

    def _build_url(self, path: str):
        host: str = self._host_availabler.get_host_by_path(path)
        return utils.build_url(self._schema, host, path)

    def shutdown(self):
        self._host_availabler.shutdown()


class _HTTPClientBuilder(object):
    def __init__(self):
        self._tenant_id: Optional[str] = None
        self._project_id: Optional[str] = None
        self._use_air_auth: Optional[bool] = None
        self._token: Optional[str] = None
        self._ak: Optional[str] = None
        self._sk: Optional[str] = None
        self._auth_service: Optional[str] = None
        self._schema: Optional[str] = None
        self._hosts: Optional[List[str]] = None
        self._region: Optional[AbstractRegion] = None
        self._host_availabler: Optional[HostAvailabler] = None

    def tenant_id(self, tenant_id: str):
        self._tenant_id = tenant_id
        return self

    def token(self, token: str):
        self._token = token
        return self

    def ak(self, ak: str):
        self._ak = ak
        return self

    def sk(self, sk: str):
        self._sk = sk
        return self

    def auth_service(self, auth_service: str):
        self._auth_service = auth_service
        return self

    def use_air_auth(self, use_air_auth: bool):
        self._use_air_auth = use_air_auth
        return self

    def schema(self, schema: str):
        self._schema = schema
        return self

    def project_id(self, project_id: str):
        self._project_id = project_id
        return self

    def hosts(self, hosts: list):
        self._hosts = hosts
        return self

    def region(self, region: AbstractRegion):
        self._region = region
        return self

    def host_availabler(self, host_availabler: str):
        self._host_availabler = host_availabler
        return self

    def build(self) -> HTTPClient:
        self._check_required_field()
        self._fill_default()
        return HTTPClient(self._new_http_caller(), self._host_availabler, self._schema, self._project_id)

    def _check_required_field(self):
        if len(self._tenant_id) == 0:
            raise Exception("tenant id is null")
        self._check_auth_required_field()
        if self._region is None:
            raise Exception("region is null")

    def _check_auth_required_field(self):
        if self._use_air_auth:
            if self._token == "":
                raise Exception("token cannot be null")
            return

        if self._sk == "" or self._ak == "":
            raise Exception("ak and sk cannot be null")

    def _fill_default(self):
        if self._schema == "":
            self._schema = "https"
        if self._host_availabler is None:
            if self._hosts is not None and len(self._hosts) > 0:
                config: PingHostAvailablerConfig = PingHostAvailablerConfig(default_hosts=self._hosts)
            else:
                config: PingHostAvailablerConfig = PingHostAvailablerConfig(default_hosts=self._region.get_hosts(),
                                                                            project_id=self._project_id)
            self._host_availabler: _PingHostAvailabler = new_ping_host_availabler(config)

    def _new_http_caller(self) -> _HTTPCaller:
        credential: _Credential = _Credential(
            self._ak,
            self._sk,
            self._auth_service,
            self._region.get_auth_region(),
        )
        http_caller: _HTTPCaller = _HTTPCaller(
            self._tenant_id,
            self._token,
            self._use_air_auth,
            credential
        )
        return http_caller


def new_http_client_builder() -> _HTTPClientBuilder:
    return _HTTPClientBuilder()
