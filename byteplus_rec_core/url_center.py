import copy
import threading

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
        url: str = None
        if path in self._path_url_map:
            url = self._path_url_map[path]
        if url is not None:
            return url

        # ab + clone
        self._lock.acquire()
        if path in self._path_url_map:
            url = self._path_url_map[path]
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
    url_center: _URLCenter = None
    if key in _host_url_center_map:
        url_center = _host_url_center_map[key]
    _url_center_lock.release()
    if url_center is not None:
        return url_center

    _url_center_lock.acquire()
    if key in _host_url_center_map:
        url_center = _host_url_center_map[key]
    if url_center is None:
        url_center: _URLCenter = _URLCenter(schema, host)
        _host_url_center_map[key] = url_center
    _url_center_lock.release()
    return url_center
