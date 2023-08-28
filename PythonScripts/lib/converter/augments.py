import json
from os import PathLike
from dataclasses import dataclass
from typing import Union, Optional


@dataclass
class AugmentConvertResult:
	id: int
	icon: str
	shipid: int
	wikiname: str

@dataclass
class AugmentConverter:
	id_to_data: dict[int, AugmentConvertResult]
	icon_to_data: dict[str, AugmentConvertResult]
	shipid_to_data: dict[int, AugmentConvertResult]
	wikiname_to_data: dict[str, AugmentConvertResult]

	def from_augmentid(self, augmentid: int) -> Optional[AugmentConvertResult]:
		return self.id_to_data.get(augmentid)

	def from_icon(self, icon: str) -> Optional[AugmentConvertResult]:
		return self.icon_to_data.get(icon)

	def from_shipid(self, shipid: int) -> Optional[AugmentConvertResult]:
		return self.shipid_to_data.get(shipid)

	def from_wikiname(self, wikiname: str) -> Optional[AugmentConvertResult]:
		return self.wikiname_to_data.get(wikiname)

	def convert(self, key: Union[str, int]) -> Optional[AugmentConvertResult]:
		"""Returns either an AugmentConvertResult from the key.
		from_augmentid, from_shipid or from_wikiname should be prefered.

		:param key: an augmentid, shipid or wikiname"""
		return self.from_augmentid(key) or self.from_icon(key) or self.from_shipid(key) or self.from_wikiname(key)


def load_converter(filepath: PathLike) -> AugmentConverter:
	"""Returns the converter using the cached converter data.

	:param filepath: path to the converter data cache file"""
	with open(filepath, 'r', encoding="utf8") as file:
		augment_data = json.load(file)

	id_to_data = {int(augid): AugmentConvertResult(*data.values()) for augid, data in augment_data['gameid'].items()}
	icon_to_data = {icon: AugmentConvertResult(*data.values()) for icon, data in augment_data['icon'].items()}
	shipid_to_data = {int(shipid): AugmentConvertResult(*data.values()) for shipid, data in augment_data['shipid'].items()}
	wikiname_to_data = {wikiname: AugmentConvertResult(*data.values()) for wikiname, data in augment_data['wikiname'].items()}
	return AugmentConverter(id_to_data, icon_to_data, shipid_to_data, wikiname_to_data)
