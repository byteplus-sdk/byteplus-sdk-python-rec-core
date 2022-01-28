from typing import Optional, Union, List

from google.protobuf.message import Message

from byteplus_rec_core.host_availabler import HostAvailabler, _PingHostAvailabler, PingHostAvailablerConfig, \
    new_ping_host_availabler
from byteplus_rec_core.http_caller import _HTTPCaller
from byteplus_rec_core.option import Option
from byteplus_rec_core.region import _REGION_UNKNOWN, _get_region_config, _get_region_hosts, _get_volc_credential_region
from byteplus_rec_core.url_center import _url_center_instance
from byteplus_rec_core.volc_auth import _Credential


class HTTPClient(object):
    def __init__(self, schema: str, http_caller: _HTTPCaller, host_availabler: HostAvailabler):
        self._schema = schema
        self._http_caller = http_caller
        self._host_availabler = host_availabler

    def do_json_request(self, path: str, request: Union[dict, list], *opts: Option) -> Union[dict, list]:
        host: str = self._host_availabler.get_host()
        url: str = _url_center_instance(self._schema, host).get_url(path)
        return self._http_caller.do_json_request(url, request, *opts)

    def do_pb_request(self, path: str, request: Message, response: Message, *opts: Option):
        host: str = self._host_availabler.get_host()
        url: str = _url_center_instance(self._schema, host).get_url(path)
        self._http_caller.do_pb_request(url, request, response, *opts)

    def shutdown(self):
        self._host_availabler.shutdown()


class _HTTPClientBuilder(object):
    def __init__(self):
        self._tenant_id: Optional[str] = None
        self._token: Optional[str] = None
        self._ak: Optional[str] = None
        self._sk: Optional[str] = None
        self._auth_service: Optional[str] = None
        self._use_air_auth: Optional[bool] = None
        self._schema: Optional[str] = None
        self._host_header: Optional[str] = None
        self._hosts: Optional[List[str]] = None
        self._region: Optional[str] = None
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

    def host_header(self, host: str):
        self._host_header = host
        return self

    def hosts(self, hosts: list):
        self._hosts = hosts
        return self

    def region(self, region: str):
        self._region = region
        return self

    def host_availabler(self, host_availabler: str):
        self._host_availabler = host_availabler
        return self

    def build(self) -> HTTPClient:
        self._check_required_field()
        self._fill_hosts()
        self._fill_default()
        http_caller: _HTTPCaller = self._new_http_caller()
        return HTTPClient(self._schema, http_caller, self._host_availabler)

    def _check_required_field(self):
        if len(self._tenant_id) == 0:
            raise Exception("Tenant id is emtpy")
        self._check_auth_required_field()
        if self._region == _REGION_UNKNOWN:
            raise Exception("Region is empty")
        if _get_region_config(self._region) is None:
            raise Exception("region({}) is not support".format(self._region))

    def _check_auth_required_field(self):
        if self._use_air_auth and self._token == "":
            raise Exception("Token is empty")

        if not self._use_air_auth and (self._sk == "" or self._ak == ""):
            raise Exception("Ak or sk is empty")

    def _fill_hosts(self):
        if self._hosts is not None:
            return
        self._hosts = _get_region_hosts(self._region)

    def _fill_default(self):
        if self._schema == "":
            self._schema = "https"
        if self._host_availabler is None:
            config: PingHostAvailablerConfig = PingHostAvailablerConfig(self._hosts, self._host_header)
            self._host_availabler: _PingHostAvailabler = new_ping_host_availabler(config)
        if self._host_availabler.hosts() is None or len(self._host_availabler.hosts()) == 0:
            self._host_availabler.set_hosts(self._hosts)
        if self._host_availabler.host_header() is None or len(self._host_availabler.host_header()) == 0:
            self._host_availabler.set_host_header(self._host_header)

    def _new_http_caller(self) -> _HTTPCaller:
        credential: _Credential = _Credential(
            self._ak,
            self._sk,
            _get_volc_credential_region(self._region),
            self._auth_service
        )
        http_caller: _HTTPCaller = _HTTPCaller(
            self._tenant_id,
            self._host_header,
            self._token,
            self._use_air_auth,
            credential
        )
        return http_caller


def new_http_client_builder() -> _HTTPClientBuilder:
    return _HTTPClientBuilder()
