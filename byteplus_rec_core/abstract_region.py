from abc import abstractmethod
from typing import List
from enum import Enum


class AbstractRegion(Enum):

    @abstractmethod
    def get_hosts(self) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def get_auth_region(self) -> str:
        raise NotImplementedError
