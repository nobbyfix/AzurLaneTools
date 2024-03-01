import logging
from dataclasses import dataclass
from typing import Union
from collections.abc import Iterable

from . import Client, SharecfgModule, Utility
from .apiclasses import (ApiDataRef, LoginRewards, SharecfgDataRef, AwardDisplay, AwardDisplayLabeled, Award, BackyardTheme,
	Chapter, Code, EquipStat, EquipStatUpgrade, Expedition, FurnitureData, Item, MetashipSkill,
	MetataskRef, Metatask, Milestone, Resource, ShipID, ShipSkin, ShipStat, ShopItem, Task)
from .Constants import Armor, Rarity, Nation, Attribute, ShipType


@dataclass
class Activity7DaySign(SharecfgModule):
	def _instantiate_client(self, dataid: str, data: dict) -> LoginRewards:
		return LoginRewards(
			json=data,
			front_drops=[Award(*awarddata) for awarddata in data["front_drops"]]
		)

@dataclass
class ActivityEventPt(SharecfgModule):
	def _instantiate_client(self, dataid: str, data: dict) -> Milestone:
		return Milestone(
			json=data,
			point=ApiDataRef(data["pt"], "player_resource_reward"),
			rewards=[Award(*awarddata) for awarddata in data["drop_client"]],
		)

@dataclass
class ActivityShopTemplate(SharecfgModule):
	def _instantiate_client(self, dataid: str, data: dict) -> ShopItem:
		return ShopItem(
			json=data,
			type=data["commodity_type"],
			refid=data["commodity_id"],
			amount=data["num"],
		)

@dataclass
class BackyardThemeTemplate(SharecfgModule):
	def _instantiate_client(self, dataid: str, data: dict) -> BackyardTheme:
		return BackyardTheme(
			json=data,
			furniture=[ApiDataRef(fid, "furniture") for fid in data["ids"]]
		)


def convert_shiptype(typeid: Union[str, int]) -> Union[ShipType, int]:
	if typeid == 0:
		return 0
	if isinstance(typeid, str):
		return ShipType.from_type(typeid)
	if typeid != 0:
		return ShipType.from_id(typeid)

@dataclass
class ChapterTemplate(SharecfgModule):
	def _instantiate_client(self, dataid: str, data: dict) -> Chapter:
		previous_chapter = None
		if pre_chapter_id := data["pre_chapter"]:
			previous_chapter = SharecfgDataRef(pre_chapter_id, "chapter_template")

		enemies = [SharecfgDataRef(enemydata[0], "expedition_data_template") for enemydata in data["expedition_id_weight_list"]]
		elites = [SharecfgDataRef(enemyid, "expedition_data_template") for enemyid in data["elite_expedition_list"]]
		sirens = [SharecfgDataRef(enemyid, "expedition_data_template") for enemyid in data["ai_expedition_list"]]

		boss = None
		if boss_id_data := data["boss_expedition_id"]:
			if len(boss_id_data) > 0:
				boss = SharecfgDataRef(boss_id_data[0], "expedition_data_template")

		chapter = Chapter(
			json=data,
			previous_chapter=previous_chapter,
			mob_list=enemies,
			mob_spawn_pattern=Utility.pop_zeros(data["enemy_refresh"]),
			elite_list=elites,
			elite_spawn_pattern=Utility.pop_zeros(data["elite_refresh"]),
			siren_list=sirens,
			siren_spawn_pattern=Utility.pop_zeros(data["ai_refresh"]),
			boss=boss,
			fleet_limitation=[[[convert_shiptype(tid) for tid in subfleet] for subfleet in fleet] for fleet in data["limitation"]],
			awards=[AwardDisplay(*award) for award in data["awards"]]
		)
		return chapter

@dataclass
class EquipDataStatistics(SharecfgModule):
	def _instantiate_client(self, dataid: str, data: dict) -> Union[EquipStat, EquipStatUpgrade]:
		if "base" in data:
			return EquipStatUpgrade(
				json=data,
				base=SharecfgDataRef(data["base"], "equip_data_statistics")
			)

		return EquipStat(
			json=data,
			rarity=Rarity.from_id(data["rarity"]-1),
			nation=Nation.from_id(data["nationality"]),
		)

@dataclass
class ExpeditionDataTemplate(SharecfgModule):
	def parse_awarddata(self, awarddata, dataid: str) -> AwardDisplay:
		if len(awarddata) == 2:
			return AwardDisplay(*awarddata)
		elif len(awarddata) == 3:
			return AwardDisplayLabeled(*awarddata)
		else:
			print(f"WARNING: Found AwardDisplay with more/less than 2 arguments (dataid: {dataid})")
			print(f"WARNING: AwardDisplay raw data <{awarddata}>")

	def _instantiate_client(self, dataid: str, data: dict) -> Expedition:
		return Expedition(
			json=data,
			icons=[icon for icon in (data["icon"].strip(), data["add_icon"].strip()) if icon],
			award_display=[self.parse_awarddata(awarddata, dataid) for awarddata in data["award_display"]],
		)

@dataclass
class FurnitureDataTemplate(SharecfgModule):
	def _instantiate_client(self, dataid: str, data: dict) -> FurnitureData:
		theme = None
		if (themeid := data["themeId"]) != 0:
			theme = SharecfgDataRef(themeid, "backyard_theme_template")

		return FurnitureData(
			json=data,
			rarity=Rarity.from_id(data["rarity"]),
			theme=theme,
		)

@dataclass
class ItemDataStatistics(SharecfgModule):
	def _instantiate_client(self, dataid: str, data: dict) -> Item:
		return Item(
			json=data,
			rarity=Rarity.from_id(data["rarity"]),
		)

@dataclass
class ItemVirtualDataStatistics(ItemDataStatistics): pass

@dataclass
class NameCode(SharecfgModule):
	# cjson converts the lua table into a json array, not a dict
	# SharecfgModule expects a dict (to use the get function)
	# so the array needs to be converted into a dict
	def _process_data(self, client: Client, jsondata) -> None:
		# start enumeration at one, since lua tables start keys at one
		# the key also needs to be converted into a string to comply with SharecfgModule behaviour
		#jsondata = {str(i): data for i, data in enumerate(jsondata, 1)}
		if isinstance(jsondata, dict):
			jsondata = jsondata.values()
		jsondata = {str(data['id']): data for data in jsondata}
		super()._process_data(client, jsondata)

	def _instantiate_client(self, dataid: str, data: dict) -> Code:
			return Code(json=data)

	# needs custom implementation, because name_code has no "all" field
	def all_client_ids(self, client: Client) -> Iterable[int]:
		self._load_data(client)
		return self._data[client].keys()

@dataclass
class PlayerResource(SharecfgModule):
	def _instantiate_client(self, dataid: str, data: dict) -> Resource:
			item = None
			if (itemid := data["itemid"]) != 0:
				item = ApiDataRef(itemid, "all_item_data_statistics")

			return Resource(
				json=data,
				item=item,
			)

@dataclass
class ShipDataStatistics(SharecfgModule):
	def _instantiate_client(self, dataid: str, data: dict) -> ShipStat:
		attributes = {}
		attributes_growth = {}
		for attr in Attribute:
			attributes[attr] = data["attrs"][attr.pos]
			attributes_growth[attr] = data["attrs_growth"][attr.pos]

		return ShipStat(
			json=data,
			shipid=ShipID(fullid=data["id"]),
			rarity=Rarity.from_id(data["rarity"]-1),
			nation=Nation.from_id(data["nationality"]),
			type=ShipType.from_id(data["type"]),
			armor=Armor.from_id(data["armor_type"]),
			attributes=attributes,
			attributes_growth=attributes_growth,
			skin=SharecfgDataRef(data["skin_id"], "ship_skin_template"),
		)

@dataclass
class ShipMetaSkilltask(SharecfgModule):
	def _instantiate_client(self, dataid: str, data: dict) -> MetashipSkill:
		tasks = []
		for taskdata in data["skill_levelup_task"]:
			taskref = MetataskRef(id=taskdata[0], module="task_meta_data_template",
				repeat_limit=taskdata[1], xp_gain=taskdata[2])
			tasks.append(taskref)

		return MetashipSkill(
			json=data,
			skill=SharecfgDataRef(data["skill_ID"], "skill_data_template"),
			item_consume=[Award(*awarddata) for awarddata in data["skill_unlock"]],
			tasks=tasks,
		)

@dataclass
class ShipSkinExpression(SharecfgModule):
	def all_client_ids(self, client: Client) -> Iterable[Union[int, str]]:
		if clientdata := self._load_data(client):
			return clientdata.keys()

@dataclass
class ShipSkinTemplate(SharecfgModule):
	def _instantiate_client(self, dataid: str, data: dict) -> ShipSkin:
		shipid = ShipID(fullid=data["id"])
		if data["ship_group"] != shipid.groupid:
			shipid = ShipID(fullid=data["id"], groupid=data["ship_group"])

		background = int(data["bg"]) if data["bg"] else None
		background_special = int(data["bg_sp"]) if data["bg_sp"] else None

		return ShipSkin(
			json=data,
			shipid=shipid,
			background=background,
			background_special=background_special,
		)

@dataclass
class TaskDataTemplate(SharecfgModule):
	def _instantiate_client(self, dataid: str, data: dict) -> Task:
		award_display = data["award_display"]
		# alert when a badly converted award_display property is found
		# (this is true for only one task across all clients except TW)
		if isinstance(award_display, str):
			logging.debug(f"Malformatted awarddisplay {award_display} for task {dataid}. (ignoring task)")
			return

		targetid_data = data["target_id"]
		targetid = int(targetid_data) if isinstance(targetid_data, str) else targetid_data

		return Task(
			json=data,
			awards=[Award(*awarddata) for awarddata in award_display],
			target_id=targetid,
		)

@dataclass
class TaskMetaDataTemplate(SharecfgModule):
	def _instantiate_client(self, dataid: str, data: dict) -> Metatask:
		return Metatask(json=data)


__all__ = {
	"activity_7_day_sign": Activity7DaySign,
	"activity_event_pt": ActivityEventPt,
	"activity_shop_template": ActivityShopTemplate,
	"backyard_theme_template": BackyardThemeTemplate,
	"chapter_template": ChapterTemplate,
	"equip_data_statistics": EquipDataStatistics,
	"expedition_data_template": ExpeditionDataTemplate,
	"furniture_data_template": FurnitureDataTemplate,
	"item_data_statistics": ItemDataStatistics,
	"item_virtual_data_statistics": ItemVirtualDataStatistics,
	"name_code": NameCode,
	"player_resource": PlayerResource,
	"ship_data_statistics": ShipDataStatistics,
	"ship_meta_skilltask": ShipMetaSkilltask,
	"ship_skin_expression": ShipSkinExpression,
	"ship_skin_template": ShipSkinTemplate,
	"task_data_template": TaskDataTemplate,
	"task_meta_data_template": TaskMetaDataTemplate,
}

def import_module(modulename: str) -> SharecfgModule:
	return __all__.get(modulename)
