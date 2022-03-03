from abc import abstractmethod
from typing import List, Optional


class HostAvailabler(object):

    @abstractmethod
    def host_header(self) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def set_hosts(self, hosts: List[str]):
        raise NotImplementedError

    @abstractmethod
    def set_host_header(self, host_header: Optional[str]):
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

