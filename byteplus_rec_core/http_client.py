from google.protobuf.message import Message

from byteplus_rec_core.host_availabler import HostAvailabler, PingHostAvailabler, PingHostAvailablerConfig
from byteplus_rec_core.http_caller import HTTPCaller
from byteplus_rec_core.option import Option
from byteplus_rec_core.region import REGION_UNKNOWN, get_region_config, get_region_hosts, get_volc_credential_region
from byteplus_rec_core.url_center import _url_center_instance
from byteplus_rec_core.volcauth.volcauth import Credential


class HTTPClient(object):
    def __init__(self, schema: str, http_caller: HTTPCaller, host_availabler: HostAvailabler):
        self._schema = schema
        self._http_caller = http_caller
        self._host_availabler = host_availabler

    def do_json_request(self, path: str, request, response: Message, *opts: Option) -> None:
        host: str = self._host_availabler.get_host()
        url: str = _url_center_instance(self._schema, host).get_url(path)
        return self._http_caller.do_json_request(url, request, response, *opts)

    def do_pb_request(self, path: str, request: Message, response: Message, *opts: Option):
        host: str = self._host_availabler.get_host()
        url: str = _url_center_instance(self._schema, host).get_url(path)
        self._http_caller.do_pb_request(url, request, response, *opts)

    def shutdown(self):
        self._host_availabler.shutdown()


class HTTPClientBuilder(object):
    def __init__(self):
        self._tenant_id: str = ""
        self._token: str = ""
        self._ak: str = ""
        self._sk: str = ""
        self._auth_service: str = ""
        self._use_air_auth: bool = False
        self._schema: str = ""
        self._hosts: list[str] = None
        self._region: str = ""
        self._host_availabler: HostAvailabler = None

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
        credential: Credential = self._build_volc_credential()
        http_caller: HTTPCaller = HTTPCaller(self._tenant_id, self._token, self._use_air_auth, credential)
        return HTTPClient(self._schema, http_caller, self._host_availabler)

    def _check_required_field(self):
        if len(self._tenant_id) == 0:
            raise Exception("Tenant id is emtpy")
        self._check_auth_required_field()
        if self._region == REGION_UNKNOWN:
            raise Exception("Region is empty")
        if get_region_config(self._region) is None:
            raise Exception("region({}) is not support".format(self._region))

    def _check_auth_required_field(self):
        if self._use_air_auth and self._token == "":
            raise Exception("Token is empty")

        if not self._use_air_auth and (self._sk == "" or self._ak == ""):
            raise Exception("Ak or sk is empty")

    def _fill_hosts(self):
        if self._hosts is None:
            self._hosts = get_region_hosts(self._region)

    def _fill_default(self):
        if self._schema == "":
            self._schema = "https"
        if self._host_availabler is None:
            config: PingHostAvailablerConfig = PingHostAvailablerConfig(self._hosts)
            self._host_availabler = PingHostAvailabler(config)
        if self._host_availabler.hosts() is None or len(self._host_availabler.hosts()) == 0:
            self._host_availabler.set_hosts(self._hosts)

    def _build_volc_credential(self) -> Credential:
        return Credential(self._ak, self._sk, get_volc_credential_region(self._region), self._auth_service)
