from dataclasses import dataclass
from abc import ABCMeta, abstractmethod
from collections.abc import Iterable
from typing import Any

from .api import ApiModule, Client, APIdataclass, ApiData, SharecfgData, MergedSharecfgData, Module, SharecfgModule
from .Constants import Armor, Nation, Rarity, Attribute, ShipType


### GENERAL DATA CLASSES ###
@dataclass
class DataRef(metaclass=ABCMeta):
	"""
	Abstract class for module apidata references.
	"""
	id: int
	module: str

	@abstractmethod
	def _get_module(self, api: "ALJsonAPI") -> Module:
		"""
		Loads the Module referenced.
		"""

	def load(self, api: "ALJsonAPI", client: Client) -> ApiData | None:
		"""
		Loads the ApiData referenced from the module for *client*.
		"""
		module = self._get_module(api)
		return module.load_client(self.id, client)

	def load_first(self, api: "ALJsonAPI", clients: Iterable[Client]) -> ApiData | None:
		"""
		Loads the first ApiData referenced from the module for *clients*.
		"""
		module = self._get_module(api)
		return module.load_first(self.id, clients)

@dataclass
class ApiDataRef(DataRef):
	"""
	A reference to ApiData of *module* with dataid *id*.
	"""
	def _get_module(self, api: "ALJsonAPI") -> ApiModule:
		return api.get_apimodule(self.module)

@dataclass
class SharecfgDataRef(DataRef):
	"""
	A reference to SharecfgData of *module* with dataid *id*.
	"""
	def _get_module(self, api: "ALJsonAPI") -> SharecfgModule:
		return api.get_sharecfgmodule(self.module)


@dataclass
class Awardable:
	"""
	Basic class to be implemented for ApiData that can be awarded.
	"""
	name: str
	rarity: Rarity
	icon: str

@dataclass
class AwardDisplay:
	"""
	Data class for award references.
	Allows resolving that reference to the associated module using the award type.
	"""
	type: int
	refid: int

	"""
	unimplemented:
	10		DROP_TYPE_OPERATION
	13		DROP_TYPE_WORLD_COLLECTION
	19		DROP_TYPE_LOVE_LETTER
	22		DROP_TYPE_META_PT
	23		DROP_TYPE_SKIN_TIMELIMIT
	26		DROP_TYPE_DORM3D_FURNITURE
	27		DROP_TYPE_DORM3D_GIFT
	28		DROP_TYPE_DORM3D_SKIN
	29		DROP_TYPE_LIVINGAREA_COVER
	31		DROP_TYPE_COMBAT_UI_STYLE
	33		DROP_TYPE_ACTIVITY_MEDAL
	41		DROP_TYPE_ISLAND_ITEM
	42		DROP_TYPE_ISLAND_OVERFLOWITEM
	43		DROP_TYPE_ISLAND_ABILITY

	1000	DROP_TYPE_USE_ACTIVITY_DROP
	1001	DROP_TYPE_RYZA_DROP
	1002	DROP_TYPE_WORKBENCH_DROP
	1003	DROP_TYPE_FEAST_DROP
	1005	DROP_TYPE_HOLIDAY_VILLA
	"""
	# see "const.lua" for all drop types and "model/vo/drop.lua" for which the data source is
	def resolve(self) -> DataRef:
		if self.type == 1: return ApiDataRef(id=self.refid, module="player_resource_reward")
		if self.type in [2,8]: return ApiDataRef(id=self.refid, module="all_item_data_statistics")
		if self.type == 3: return SharecfgDataRef(id=self.refid, module="equip_data_statistics")
		if self.type == 4: return ApiDataRef(id=self.refid, module="ship_reward")
		if self.type == 5: return ApiDataRef(id=self.refid, module="furniture")
		if self.type == 6: return SharecfgDataRef(id=self.refid, module="strategy_data_template")
		if self.type in [7,23]: return SharecfgDataRef(id=self.refid, module="ship_skin_template")
		if self.type == 9: return SharecfgDataRef(id=self.refid, module="equip_skin_template")
		if self.type == 12: return SharecfgDataRef(id=self.refid, module="world_item_data_template")
		if self.type == 14: return SharecfgDataRef(id=self.refid, module="item_data_frame")
		if self.type == 15: return SharecfgDataRef(id=self.refid, module="item_data_chat")
		if self.type == 17: return SharecfgDataRef(id=self.refid, module="emoji_template")
		if self.type == 21: return SharecfgDataRef(id=self.refid, module="spweapon_data_statistics")
		if self.type == 24: return SharecfgDataRef(id=self.refid, module="benefit_buff_template")
		if self.type == 25: return SharecfgDataRef(id=self.refid, module="commander_data_template")
		if self.type == 100: return SharecfgDataRef(id=self.refid, module="drop_data_restore")
		raise NotImplementedError(f"Cannot resolve award of type {self.type}: Unknown or unimplemented type.")

	def load(self, api: "ALJsonAPI", client: Client) -> Awardable | None:
		dataref = self.resolve()
		awardable = dataref.load(api, client)
		return awardable
	
	def load_first(self, api: "ALJsonAPI", client: Iterable[Client]) -> Awardable | None:
		dataref = self.resolve()
		awardable = dataref.load_first(api, client)
		return awardable

@dataclass
class AwardDisplayLabeled(AwardDisplay):
	label: str

@dataclass
class Award(AwardDisplay):
	"""
	An AwardDisplay that also specifies that amount of the items awarded.
	"""
	amount: int


### GENERAL CLASSES ###
class ShipID:
	"""
	Helper class that automatically converts shipids into the the three useful formats.
	"""
	fullid: int | None
	groupid: int
	singleid: int | None

	def __init__(self, groupid: int = 0, fullid: int = 0):
		if groupid and fullid:
			self.fullid = fullid
			self.groupid = groupid
			self.singleid = fullid%10
		elif fullid:
			self.fullid = fullid
			self.groupid = fullid//10
			self.singleid = fullid%10
		elif groupid:
			self.fullid = None
			self.groupid = groupid
			self.singleid = None
		else:
			raise ValueError("ShipID needs either groupid or fullid to be set.")

	def __str__(self):
		maxid = self.fullid if self.fullid else self.groupid
		diffgroupid = self.groupid if self.fullid and self.fullid//10 != self.groupid else None
		return self.__class__.__name__ + f"({maxid}{f', {diffgroupid}' if diffgroupid else ''})"

class CachedAPILoader():
	_cache: dict
	_api: "ALJsonAPI"

	def __init__(self, api: "ALJsonAPI") -> None:
		self._cache = {}
		self._api = api
		self._generate_cache()

	def _regenerate_cache(self) -> None:
		self._cache.clear()
		self._generate_cache()

	@abstractmethod
	def _generate_cache(self) -> None: pass

	def get(self, key) -> Any:
		return self._cache.get(key)

### SHARECFG DATA CLASSES ###
@APIdataclass
class Milestone(SharecfgData):
	point: ApiDataRef
	rewards: list[Award]

@APIdataclass
class ShopItem(SharecfgData, Award): pass

@APIdataclass
class Chapter(SharecfgData):
	type: int
	previous_chapter: list[SharecfgDataRef]
	mob_list: list[SharecfgDataRef]
	mob_spawn_pattern: list[int]
	elite_list: list[SharecfgDataRef]
	elite_spawn_pattern: list[int]
	siren_list: list[SharecfgDataRef]
	siren_spawn_pattern: list[int]
	boss: SharecfgDataRef | None
	fleet_limitation: list[list[list[ShipType | int]]]
	awards: list[AwardDisplay]

@APIdataclass
class EquipStat(SharecfgData, Awardable):
	nation: Nation

@APIdataclass
class EquipStatUpgrade(SharecfgData):
	base: SharecfgDataRef

@APIdataclass
class Expedition(SharecfgData):
	icons: list[str]
	award_display: list[AwardDisplay]

@APIdataclass
class FurnitureData(SharecfgData, Awardable):
	theme: SharecfgDataRef | None

@APIdataclass
class Item(SharecfgData, Awardable): pass

@APIdataclass
class Code(SharecfgData): pass

@APIdataclass
class Resource(SharecfgData):
	name: str
	item: ApiDataRef | None

@APIdataclass
class ShipStat(SharecfgData):
	shipid: ShipID
	name: str
	rarity: Rarity
	nation: Nation
	type: ShipType
	armor: Armor
	attributes: dict[Attribute, int]
	attributes_growth: dict[Attribute, int]
	skin: SharecfgDataRef

@APIdataclass
class ShipSkin(SharecfgData):
	shipid: ShipID
	background: int | None
	background_special: int | None

@APIdataclass
class Task(SharecfgData):
	awards: list[Award]
	target_id: int | list[int] | list[tuple[int, int]]

@APIdataclass
class Metatask(SharecfgData): pass

@dataclass
class MetataskRef(SharecfgDataRef):
	repeat_limit: int
	xp_gain: int

@APIdataclass
class MetashipSkill(SharecfgData):
	skill: SharecfgDataRef
	item_consume: list[Award]
	tasks: list[MetataskRef]

@APIdataclass
class BackyardTheme(SharecfgData):
	name: str
	icon: str
	desc: str
	furniture: list[ApiDataRef]

@APIdataclass
class LoginRewards(SharecfgData):
	front_drops: list[Award]

### APIMODULE DATA CLASSES ###
@dataclass
class ShipReward(Awardable):
	shipid: ShipID

@APIdataclass
class Furniture(MergedSharecfgData, Awardable):
	theme: SharecfgDataRef | None

@APIdataclass
class ExtendedEquipStat(MergedSharecfgData): pass
