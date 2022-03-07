import datetime
import hashlib
import hmac
from typing import Dict, Optional, List, Tuple
from urllib.parse import urlparse, parse_qsl, urlencode, quote

from byteplus_rec_core.utils import HTTPRequest

_TIME_FORMAT_V4 = "%Y%m%dT%H%M%SZ"


class _Credential(object):
    def __init__(self, ak: str, sk: str, service: str, region: str, session_token: Optional[str] = None):
        self.access_key_id = ak
        self.secret_access_key = sk
        self.service = service
        self.region = region
        self.session_token = session_token


class _Metadata(object):
    def __init__(self,
                 service: str,
                 region: str,
                 algorithm: Optional[str] = None,
                 credential_scope: Optional[str] = None,
                 signed_headers: Optional[str] = None,
                 date: Optional[str] = None):
        self.service = service
        self.region = region
        self.algorithm = algorithm
        self.credential_scope = credential_scope
        self.signed_headers = signed_headers
        self.date = date


def _now() -> datetime.datetime:
    return datetime.datetime.utcnow()


def _timestamp_v4() -> str:
    return _now().strftime(_TIME_FORMAT_V4)


def _prepare_request_v4(req: HTTPRequest):
    necessary_defaults: Dict[str, str] = {
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        "X-Date": _timestamp_v4()
    }
    for header, value in necessary_defaults.items():
        if len(req.header.get(header, "")) == 0:
            req.header[header] = value

    path = urlparse(req.url).path
    if len(path) == 0:
        req.url = req.url + "/"


def _sign(req: HTTPRequest, cred: _Credential):
    _prepare_request_v4(req)
    meta: _Metadata = _Metadata(cred.service, cred.region)

    # Task1
    hashed_canon_req: str = _hashed_canonical_request_v4(req, meta)

    # Task2
    string_to_sign_ret: str = _string_to_sign(req.header, hashed_canon_req, meta)

    # Task3
    signing_key_ret = _signing_key(cred.secret_access_key, meta.date, meta.region, meta.service)
    signature_ret = _signature(signing_key_ret, string_to_sign_ret)

    req.header["Authorization"] = _build_auth_header(signature_ret, meta, cred)

    if cred.session_token:
        req.header['X-Security-Token'] = cred.session_token


def _build_auth_header(signature_ret: str, meta: _Metadata, cred: _Credential) -> str:
    credential: str = cred.access_key_id + "/" + meta.credential_scope
    return meta.algorithm + \
           " Credential=" + credential + \
           ", SignedHeaders=" + meta.signed_headers + \
           ", Signature=" + \
           signature_ret


def _hashed_canonical_request_v4(req: HTTPRequest, meta: _Metadata) -> str:
    parse_result = urlparse(req.url)
    # encode body and generate body hash
    if req.req_bytes is not None:
        content_hash = hashlib.sha256(req.req_bytes)
    else:
        content_hash = hashlib.sha256(b'')
    req.header["X-Content-Sha256"] = content_hash.hexdigest()
    req.header["Host"] = parse_result.netloc

    sorted_headers: List[Tuple[str, str]] = []
    allowed_headers = ("content-type", "content-md5", "host")
    for key, value in req.header.items():
        key_lower = key.lower()
        if key_lower in allowed_headers or key_lower.startswith("x-"):
            sorted_headers.append((key_lower, value.strip()))
    sorted_headers.sort(key=lambda x: x[0])

    headers_to_sign: str = ""
    sorted_header_keys: List[str] = []
    for key_lower, value in sorted_headers:
        if key_lower == "host":
            split = value.split(":")
            # host is ip:port, make value = ip
            if len(split) == 2 and (split[1] == "80" or split[1] == "443"):
                value = split[0]
        headers_to_sign += key_lower + ":" + value + "\n"
        sorted_header_keys.append(key_lower)
    meta.signed_headers = ";".join(sorted_header_keys)

    # keep k,v order with server
    sorted_queries: List = parse_qsl(parse_result.query)
    sorted_queries.sort(key=lambda x: x[0])
    query_str: str = urlencode(sorted_queries)

    safe_chars = '/~'
    req_parts = [req.method.upper(), quote(parse_result.path, safe_chars), _normal_query(query_str), headers_to_sign,
                 meta.signed_headers, content_hash.hexdigest()]
    canonical_request = '\n'.join(req_parts)

    return hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()


def _normal_query(query_str: str) -> str:
    return query_str.replace("+", "%20", -1)


def _string_to_sign(header: dict, hashed_canon_req: str, meta: _Metadata) -> str:
    request_ts = header.get("X-Date")
    meta.algorithm = "HMAC-SHA256"
    meta.date = _ts_date(request_ts)
    meta.credential_scope = "/".join([meta.date, meta.region, meta.service, "request"])
    return "\n".join([meta.algorithm, request_ts, meta.credential_scope, hashed_canon_req])


def _ts_date(timestamp: str) -> str:
    return timestamp[:8]


def _signing_key(secret_access_key: str, date: str, region: str, service: str) -> bytes:
    k_date = hmac.new(secret_access_key.encode('utf-8'), date.encode('utf-8'), hashlib.sha256).digest()
    k_region = hmac.new(k_date, region.encode('utf-8'), hashlib.sha256).digest()
    k_service = hmac.new(k_region, service.encode('utf-8'), hashlib.sha256).digest()
    k_signing = hmac.new(k_service, "request".encode('utf-8'), hashlib.sha256).digest()
    return k_signing


def _signature(signing_key_ret: bytes, string_to_sign_ret: str) -> str:
    hsh = hmac.new(signing_key_ret, string_to_sign_ret.encode('utf-8'), hashlib.sha256)
    return hsh.hexdigest()
