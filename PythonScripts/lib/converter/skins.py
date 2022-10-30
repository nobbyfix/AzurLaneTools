from dataclasses import dataclass
import json
from os import PathLike
from typing import Union, Optional


@dataclass
class SkinConvertResult:
	id: int
	shipname: str
	category: str
	painting: str
	prefab: str

@dataclass
class SkinsConverter:
	painting_to_data: dict[str, SkinConvertResult]

	def from_painting(self, paintingname: str) -> Optional[SkinConvertResult]:
		return self.painting_to_data.get(paintingname)

	def convert(self, key: Union[str, int]) -> Optional[SkinConvertResult]:
		"""Returns either an SkinConvertResult from the key.
		from_painting should be prefered.

		:param key: an paintingname"""
		return self.from_painting(key)

def load_converter(filepath: PathLike) -> SkinsConverter:
	"""Returns the converter using the cached converter data.

	:param filepath: path to the converter data cache file"""
	with open(filepath, 'r', encoding="utf8") as file:
		skin_data = json.load(file)

	painting_to_data = {p: SkinConvertResult(data['gameid'], data['shipname'], data['category'], p, data['prefab']) for p, data in skin_data['painting'].items()}
	return SkinsConverter(painting_to_data)
