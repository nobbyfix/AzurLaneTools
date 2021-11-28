from enum import Enum
from dataclasses import dataclass
from pathlib import Path
from typing import Union


Client = Enum('Client', 'EN CN JP KR TW')
CompareType = Enum('CompareType', 'New Changed Unchanged Deleted')
VersionType = Enum('VersionType', 'AZL CV L2D PIC BGM')
DownloadType = Enum('DownloadType', 'NoChange Removed Success Failed')


@dataclass
class HashRow:
	filepath: str
	size: int
	md5hash: str

@dataclass
class CompareResult:
	current_hash: HashRow
	new_hash: HashRow
	compare_type: CompareType

@dataclass
class VersionResult:
	version: str
	vhash: str
	rawstring: str
	version_type: VersionType

@dataclass
class BundlePath:
	full: Path
	inner: str

	@staticmethod
	def construct(parentdir: Path, inner: Union[Path, str]) -> "BundlePath":
		fullpath = Path(parentdir, inner)
		return BundlePath(fullpath, str(inner))

@dataclass
class UpdateResult:
	compare_result: CompareResult
	download_type: DownloadType
	path: BundlePath

@dataclass
class UserConfig:
	useragent: str
	download_isblacklist: bool
	download_filter: list
	extract_isblacklist: bool
	extract_filter: list
	asset_directory: Path

@dataclass
class ClientConfig:
	gateip: str
	gateport: int
	cdnurl: str