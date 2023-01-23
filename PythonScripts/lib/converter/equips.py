import json
from os import PathLike
from dataclasses import dataclass
from typing import Union, Optional


@dataclass
class EquipConvertResult:
	id: int
	icon: int
	gamename: str
	wikiname: str

@dataclass
class EquipConverter:
	id_to_data: dict[int, EquipConvertResult]
	icon_to_data: dict[int, EquipConvertResult]
	gamename_to_data: dict[str, EquipConvertResult]
	wikiname_to_data: dict[str, EquipConvertResult]

	def from_equipid(self, equipid: int) -> Optional[EquipConvertResult]:
		return self.id_to_data.get(equipid)

	def from_icon(self, icon: int) -> Optional[EquipConvertResult]:
		return self.icon_to_data.get(icon)

	def from_gamename(self, gamename: str) -> Optional[EquipConvertResult]:
		return self.gamename_to_data.get(gamename)

	def from_wikiname(self, wikiname: str) -> Optional[EquipConvertResult]:
		return self.wikiname_to_data.get(wikiname)

	def convert(self, key: Union[str, int]) -> Optional[EquipConvertResult]:
		"""Returns either an EquipConvertResult from the key.
		from_equipid, from_gamename or from_wikiname should be prefered.

		:param key: an equipid, gamename or wikiname"""
		return self.from_equipid(key) or self.from_icon(key) or self.from_gamename(key) or self.from_wikiname(key)


def load_converter(filepath: PathLike) -> EquipConverter:
	"""Returns the converter using the cached converter data.

	:param filepath: path to the converter data cache file"""
	with open(filepath, 'r', encoding="utf8") as file:
		equip_data = json.load(file)

	id_to_data = {int(eqid): EquipConvertResult(*data.values()) for eqid, data in equip_data['gameid'].items()}
	icon_to_data = {int(icon): EquipConvertResult(*data.values()) for icon, data in equip_data['icon'].items()}
	gamename_to_data = {gamename: EquipConvertResult(*data.values()) for gamename, data in equip_data['gamename'].items()}
	wikiname_to_data = {wikiname: EquipConvertResult(*data.values()) for wikiname, data in equip_data['wikiname'].items()}
	return EquipConverter(id_to_data, icon_to_data, gamename_to_data, wikiname_to_data)
