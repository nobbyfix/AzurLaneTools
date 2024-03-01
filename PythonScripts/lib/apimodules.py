import itertools
from dataclasses import dataclass
from typing import Optional
from collections.abc import Iterable

from . import Client, ApiModule
from .apiclasses import Item, ShipReward, Furniture, ExtendedEquipStat, EquipStatUpgrade


@dataclass
class PlayerResourceReward(ApiModule):
	def _load_client(self, dataid: str, client: Client) -> Optional[Item]:
		player_resource = self._getmodule("player_resource")
		resource = player_resource._load_client(dataid, client)
		if resource:
			item = resource.item.load(self._api, client)
			return item

	def all_client_ids(self, client: Client) -> Iterable[int]:
		player_resource = self._getmodule("player_resource")
		client_ids = [resource.id for resource in player_resource.all_client(client) if resource.item]
		return client_ids

@dataclass
class ShipRewardModule(ApiModule):
	def _load_client(self, dataid: str, client: Client) -> Optional[ShipReward]:
		ship_data_statistics = self._getmodule("ship_data_statistics")
		shipstat = ship_data_statistics._load_client(dataid, client)
		if shipstat:
			shipskin = shipstat.skin.load(self._api, client)
			shipreward = ShipReward(
				name=shipstat.name,
				rarity=shipstat.rarity,
				icon=shipskin.painting,
				shipid=shipstat.shipid
			)
			return shipreward

	def all_client_ids(self, client: Client) -> Iterable[int]:
		ship_data_statistics = self._getmodule("ship_data_statistics")
		client_ids = [sid for sid in ship_data_statistics.all_client_ids(client) if int(sid)%10 == 1]
		return client_ids

@dataclass
class FurnitureModule(ApiModule):
	def _load_client(self, dataid: str, client: Client) -> Optional[Furniture]:
		furniture_data_template = self._getmodule("furniture_data_template")
		furniture_shop_template = self._getmodule("furniture_shop_template")

		furniture_data = furniture_data_template.load_client(dataid, client)
		furniture_shop = furniture_shop_template.load_client(dataid, client)
		if furniture_data is not None and furniture_shop is not None:
			return Furniture(furniture_data, furniture_shop)

	def all_client_ids(self, client: Client) -> Iterable[int]:
		furniture_data_template = self._getmodule("furniture_data_template")
		return furniture_data_template.all_client_ids(client)

@dataclass
class ExtendedEquipDataStatistics(ApiModule):
	def _load_client(self, dataid: str, client: Client) -> Optional[ExtendedEquipStat]:
		equip_data_statistics = self._getmodule("equip_data_statistics")

		def_data = equip_data_statistics.load_client(dataid, client)
		if def_data is not None:
			if isinstance(def_data, EquipStatUpgrade):
				base_data = def_data.base.load(self._api, client)
				return ExtendedEquipStat(def_data, base_data)
			else:
				return ExtendedEquipStat(def_data)

	def all_client_ids(self, client: Client) -> Iterable[int]:
		equip_data_statistics = self._getmodule("equip_data_statistics")
		return equip_data_statistics.all_client_ids(client)

@dataclass
class AllItemDataStatistics(ApiModule):
	def _load_client(self, dataid: str, client: Client) -> Optional[Item]:
		item_data_statistics = self._getmodule("item_data_statistics")
		item_virtual_data_statistics = self._getmodule("item_virtual_data_statistics")

		item_data = item_data_statistics.load_client(dataid, client)
		item_virtual_data = item_virtual_data_statistics.load_client(dataid, client)
		if item_data:
			return item_data
		else:
			return item_virtual_data

	def all_client_ids(self, client: Client) -> Iterable[int]:
		item_data_statistics = self._getmodule("item_data_statistics")
		item_virtual_data_statistics = self._getmodule("item_virtual_data_statistics")
		return itertools.chain(item_data_statistics.all_client_ids(client), item_virtual_data_statistics.all_client_ids(client))


__all__ = {
	"player_resource_reward": PlayerResourceReward,
	"ship_reward": ShipRewardModule,
	"furniture": FurnitureModule,
	"extended_equip_data_statistics": ExtendedEquipDataStatistics,
	"all_item_data_statistics": AllItemDataStatistics,
}

def import_module(modulename: str) -> ApiModule:
	return __all__.get(modulename)
