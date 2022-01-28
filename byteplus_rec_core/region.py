from typing import Optional, List

_REGION_UNKNOWN = ""


class RegionConfig(object):
    def __init__(self, hosts: List[str], volc_credential_region: str):
        self._hosts = hosts
        self._volc_credential_region = volc_credential_region

    @property
    def hosts(self):
        return self._hosts

    @property
    def volc_credential_region(self):
        return self._volc_credential_region


_region_config_map: dict = {}


def register_region(region: str, region_config: RegionConfig):
    global _region_config_map
    if region in _region_config_map:
        raise Exception("region has already exist: {}".format(region))
    _region_config_map[region] = region_config


def _get_region_config(region: str) -> Optional[RegionConfig]:
    global _region_config_map
    if region in _region_config_map:
        return _region_config_map[region]
    return None


def _get_region_hosts(region: str) -> List[str]:
    global _region_config_map
    return _region_config_map[region].hosts


def _get_volc_credential_region(region: str) -> str:
    global _region_config_map
    return _region_config_map[region].volc_credential_region
