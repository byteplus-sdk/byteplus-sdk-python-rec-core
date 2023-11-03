from abc import abstractmethod
from typing import List, Optional

from byteplus_rec_core.abtract_host_availabler import AbstractHostAvailabler
from byteplus_rec_core.ping_host_availabler import PingHostAvailabler, Config


# Implement custom HostAvailabler by overriding HostAvailablerFactory.
class HostAvailablerFactory(object):
    @abstractmethod
    def new_host_availabler(self, hosts: List[str],
                            project_id: Optional[str] = "",
                            main_host: Optional[str] = None,
                            skip_fetch_hosts: Optional[bool] = False) -> AbstractHostAvailabler:
        return PingHostAvailabler(hosts, project_id, config=None, main_host=main_host,
                                  skip_fetch_hosts=skip_fetch_hosts)
