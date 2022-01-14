import copy
import threading
from typing import Optional

_host_url_center_map: dict = {}
_url_center_lock = threading.Lock()


class _URLCenter(object):
    def __init__(self, schema: str, host: str):
        self._url_format: str = "{}://{}".format(schema, host)
        self._path_url_map: dict = {}
        self._lock = threading.Lock()

    def get_url(self, path: str) -> str:
        while path.startswith("/"):
            path = path[1:]
        url: Optional[str] = self._path_url_map.get(path)
        if url is not None:
            return url

        # ab + clone
        self._lock.acquire()
        url: Optional[str] = self._path_url_map.get(path)
        if url is None:
            url = "{}/{}".format(self._url_format, path)
            path_url_map_copy = copy.deepcopy(self._path_url_map)
            path_url_map_copy[path] = url
            self._path_url_map = path_url_map_copy
        self._lock.release()
        return url


def _url_center_instance(schema: str, host: str) -> _URLCenter:
    global _host_url_center_map
    key: str = "{}_{}".format(schema, host)
    _url_center_lock.acquire()
    url_center: Optional[_URLCenter] = _host_url_center_map.get(key)
    _url_center_lock.release()
    if url_center is not None:
        return url_center

    _url_center_lock.acquire()
    url_center: Optional[_URLCenter] = _host_url_center_map.get(key)
    if url_center is None:
        url_center: _URLCenter = _URLCenter(schema, host)
        _host_url_center_map[key] = url_center
    _url_center_lock.release()
    return url_center
