from abc import abstractmethod
from typing import List, Optional

from byteplus_rec_core.abtract_host_availabler import AbstractHostAvailabler
from byteplus_rec_core.ping_host_availabler import PingHostAvailabler, Config


# Implement custom HostAvailabler by overriding HostAvailablerFactory.
class HostAvailablerFactory(object):
    @abstractmethod
    def new_host_availabler(self, hosts: List[str],
                            project_id: Optional[str] = "") -> AbstractHostAvailabler:
        return PingHostAvailabler(hosts, project_id, config=None)


