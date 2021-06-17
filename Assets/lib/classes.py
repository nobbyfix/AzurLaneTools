from enum import Enum
from dataclasses import dataclass

Client = Enum('Client', 'EN CN JP KR TW')
CompareType = Enum('CompareType', 'New Changed Deleted')
VersionType = Enum('VersionType', 'AZL CV L2D PIC BGM')

@dataclass
class CompareResult:
	filepath: str
	size: int
	size_new: int
	md5hash: str
	md5hash_new: str
	compare_type: CompareType

@dataclass
class VersionResult:
	version: str
	vhash: str
	rawstring: str
	version_type: VersionType


@dataclass
class UserConfig:
	useragent: str
	download_isblacklist: bool
	download_filter: list
	extract_isblacklist: bool
	extract_filter: list

@dataclass
class ClientConfig:
	gateip: str
	gateport: int
	cdnurl: str