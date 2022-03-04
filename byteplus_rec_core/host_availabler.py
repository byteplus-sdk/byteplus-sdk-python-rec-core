from abc import abstractmethod
from typing import List


class HostAvailabler(object):

    @abstractmethod
    def set_hosts(self, hosts: List[str]):
        raise NotImplementedError

    @abstractmethod
    def get_host(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_host_by_path(self, path: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def shutdown(self):
        raise NotImplementedError

