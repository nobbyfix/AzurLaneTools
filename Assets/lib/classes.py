from enum import Enum
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union


CompareType = Enum('CompareType', 'New Changed Unchanged Deleted')
VersionType = Enum('VersionType', 'AZL CV L2D PIC BGM CIPHER MANGA PAINTING')
DownloadType = Enum('DownloadType', 'NoChange Removed Success Failed')


class AbstractClient(Enum):
	active: bool
	locale_code: str
	package_name: str

	def __new__(cls, value, active, locale, package_name):
		# this should be done differently, but i am too lazy to do that now
		# TODO: change it
		if not hasattr(cls, "package_names"):
			cls.package_names = {}

		obj = object.__new__(cls)
		obj._value_ = value
		obj.active = active
		obj.locale_code = locale
		obj.package_name = package_name
		cls.package_names[package_name] = obj
		return obj

	@classmethod
	def from_package_name(cls, package_name) -> Optional['AbstractClient']:
		return cls.package_names.get(package_name)


class Client(AbstractClient):
	EN = (1, True, 'en-US', 'com.YoStarEN.AzurLane')
	JP = (2, True, 'ja-JP', 'com.YoStarJP.AzurLane')
	CN = (3, True, 'zh-CN', '')
	KR = (4, True, 'ko-KR', 'kr.txwy.and.blhx')
	TW = (5, True, 'zh-TW', 'com.hkmanjuu.azurlane.gp')


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
	extract_directory: Path

@dataclass
class ClientConfig:
	gateip: str
	gateport: int
	cdnurl: str
