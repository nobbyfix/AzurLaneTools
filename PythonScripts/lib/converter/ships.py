import json
from os import PathLike
from dataclasses import dataclass
from typing import Union, Optional


@dataclass
class ShipIDConverter:
	ship_to_id: dict[str, int]
	id_to_ship: dict[int, str]

	def get_groupid(self, shipname: str) -> Optional[int]:
		return self.ship_to_id.get(shipname)

	def get_shipname(self, groupid: int) -> Optional[str]:
		return self.id_to_ship.get(groupid)

	def convert(self, key: Union[str, int]) -> Union[str, int, None]:
		"""Returns either a groupid or shipname depending on the key.
		get_groupid and get_shipname should be prefered.

		:param key: a groupid or shipname"""
		groupid = self.get_groupid(key)
		shipname = self.get_shipname(key)
		return groupid or shipname

def load_converter(filepath: PathLike) -> ShipIDConverter:
	"""Returns the converter using the cached converter data.

	:param filepath: path to the converter data cache file"""
	with open(filepath, 'r') as file:
		ship_data = json.load(file)
	groupid_convert = {int(groupid): name for groupid, name in ship_data['groupid'].items()}
	return ShipIDConverter(ship_data['ship'], groupid_convert)
