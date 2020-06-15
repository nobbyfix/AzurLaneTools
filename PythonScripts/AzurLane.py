from typing import List, Union, Dict
from enum import Enum
from os.path import join, dirname, abspath
import json, re

import ShipIDConverter
import WikiHelper

class Client(Enum):
	EN = 1
	CN = 2
	JP = 3
	KR = 4
	TW = 5

class Award:
	def __init__(self, data_type:int, data_id:int, amount:int, api):
		self.data_type = data_type
		self.data_id = data_id
		self.amount = amount
		# init additional data
		self.name = None
		self.rarity = None
		self.icon = None
		self.load_additional_data(api)

	def load_additional_data(self, api):
		loader_func = getattr(self, 'load'+str(self.data_type))
		loader_func(api)

	# DROP TYPE RESOURCE
	# loads player_resource (with their reference to item_data_statistics)
	def load1(self, api):
		player_resource = api.load_multi_sharecfg('player_resource', api.ALL_CLIENTS)
		resource = api.load_from_first_client(player_resource, str(self.data_id))
		item_data_statistics = api.load_multi_sharecfg('item_data_statistics', api.ALL_CLIENTS)
		item = api.load_from_first_client(item_data_statistics, str(resource.get('itemid')))
		self.name = item.get('name')
		self.rarity = item.get('rarity')

	# DROP TYPE ITEM
	# loads item_data_statistics
	def load2(self, api):
		item_data_statistics = api.load_multi_sharecfg('item_data_statistics', api.ALL_CLIENTS)
		item = api.load_from_first_client(item_data_statistics, str(self.data_id))
		self.name = item.get('name')
		self.rarity = item.get('rarity')
		# experimental icon implementation
		eqicon = item.get('icon')
		if 'Equips/' in eqicon:
			self.icon = eqicon.replace('Equips/', '')
	
	# DROP TYPE EQUIP
	# loads equip_data_statistics
	def load3(self, api):
		equip_data_statistics = api.load_multi_sharecfg('equip_data_statistics', api.ALL_CLIENTS)
		equip = api.load_from_first_client(equip_data_statistics, str(self.data_id))
		self.name = equip.get('name')
		self.rarity = equip.get('rarity')-1
		self.icon = equip.get('icon')

	# DROP TYPE SHIP
	# loads ship_data_statistics
	def load4(self, api):
		ship_data_statistics = api.load_multi_sharecfg('ship_data_statistics', api.ALL_CLIENTS)
		ship = api.load_from_first_client(ship_data_statistics, str(self.data_id))
		self.name = api.converter.get_shipname(self.data_id//10)
		self.rarity = ship.get('rarity')-1

	# DROP TYPE FURNITURE
	# loads furniture_data_template
	def load5(self, api):
		furniture_data_template = api.load_multi_sharecfg('furniture_data_template', api.ALL_CLIENTS)
		furniture = api.load_from_first_client(furniture_data_template, str(self.data_id))
		self.name = furniture.get('name')
		self.rarity = furniture.get('rarity')
		self.icon = 'FurnIcon_'+furniture.get('icon')

	# DROP TYPE STRATEGY
	# loads strategy_data_template
	def load6(self, api):
		raise NotImplementedError('Unsupported Award Type: 6 - STRATEGY')

	# DROP TYPE SKIN
	# loads ship_skin_template
	def load7(self, api):
		ship_skin_template = api.load_multi_sharecfg('ship_skin_template', api.ALL_CLIENTS)
		skin = api.load_from_first_client(ship_skin_template, str(self.data_id))
		self.name = skin.get('name')
		self.rarity = 1

	# DROP TYPE VITEM
	# loads item_data_statistics
	def load8(self, api):
		self.load2(api)
	
	# DROP TYPE EQUIPMENT_SKIN
	# loads equip_skin_template
	def load9(self, api):
		equip_skin_template = api.load_multi_sharecfg('equip_skin_template', api.ALL_CLIENTS)
		eqskin = api.load_from_first_client(equip_skin_template, str(self.data_id))
		self.name = eqskin.get('name')
		self.rarity = eqskin.get('rarity')
		self.icon = 'EquipSkinIcon_'+eqskin.get('icon')

	# DROP TYPE NPC_SHIP
	# loads ship_data_statistics
	def load10(self, api):
		raise NotImplementedError('Unsupported Award Type: 10 - NPC_SHIP')

	# DROP TYPE WORLD_ITEM
	# loads world_item_data_template (does not exist???!!!)
	def load12(self, api):
		raise NotImplementedError('Unsupported Award Type: 12 - WORLD_ITEM')

	# DROP TYPE ICON_FRAME
	# loads item_data_frame
	def load14(self, api):
		raise NotImplementedError('Unsupported Award Type: 14 - ICON_FRAME')

	# DROP TYPE CHAT_FRAME
	# loads item_data_chat
	def load15(self, api):
		raise NotImplementedError('Unsupported Award Type: 15 - CHAT_FRAME')

	# DROP TYPE EMOJI
	# loads emoji_template
	def load17(self, api):
		raise NotImplementedError('Unsupported Award Type: 17 - EMOJI')


class ALJsonAPI:
	def __init__(self, source_path:str):
		self.SOURCE_PATH = source_path
		self.DEFAULT_CLIENTS = [Client.EN, Client.CN, Client.JP]
		self.ALL_CLIENTS = [cl for cl in Client]
		self.data_pool = {cl:dict() for cl in self.ALL_CLIENTS}
		self.converter = ShipIDConverter.load_converter()
		self.NAMECODE = re.compile(r'(\{namecode:(\d+)\})')

	def load_sharecfg(self, sharecfg_name:str, client:Client) -> dict:
		"""Returns the contents of a single sharecfg json file.
		
		:param sharecfg_name: name of the sharecfg file to return contents from
		:param client: the client to load the sharecfg file from"""
		if not (sharecfg_name in self.data_pool[client]):
			with open(join(self.SOURCE_PATH, client.name, 'sharecfg', sharecfg_name+'.json'), 'r', encoding='utf8') as jfile:
				json_data = json.load(jfile)
			self.data_pool[client][sharecfg_name] = json_data
		return self.data_pool[client][sharecfg_name]

	def load_multi_sharecfg(self, sharecfg_name:str, clients:List[Client]) -> Dict[Client, dict]:
		"""Returns multiple sharecfg json files as a dict with clients as keys.
		
		:param sharecfg_name: name of the sharecfg file to return contents from
		:param clients: list of clients to return sharecfg files from """
		return {client: self.load_sharecfg(sharecfg_name, client) for client in clients}

	def load_gamecfg(self, gamecfg_name:str, client:Client) -> dict:
		with open(join(self.SOURCE_PATH, client, gamecfg_name+'.json'), 'r', encoding='utf8') as jfile:
			return json.load(jfile)

	def load_multi_gamecfg(self, gamecfg_name:str, clients:List[Client]) -> Dict[Client, dict]:
		return {client: self.load_sharecfg(gamecfg_name, client) for client in clients}

	def load_dungeon(self, dungeon_id:Union[int, str], client:Client) -> dict:
		return self.load_gamecfg(join('dungeon', str(dungeon_id)), client)

	def load_multi_dungeon(self, dungeon_id:Union[int, str], clients:List[Client]) -> Dict[Client, dict]:
		return self.load_multi_gamecfg(join('dungeon', str(dungeon_id)), clients)

	def load_buff(self, buff_id:Union[int, str], client:Client) -> dict:
		return self.load_gamecfg(join('buff', 'buff_'+str(buff_id)), client)

	def load_multi_buff(self, buff_id:Union[int, str], clients:List[Client]) -> Dict[Client, dict]:
		return self.load_multi_gamecfg(join('buff', 'buff_'+str(buff_id)), clients)

	def load_skill(self, skill_id:Union[int, str], client:Client) -> dict:
		return self.load_gamecfg(join('skill', 'skill_'+str(skill_id)), client)

	def load_multi_skill(self, skill_id:Union[int, str], clients:List[Client]) -> Dict[Client, dict]:
		return self.load_multi_gamecfg(join('skill', 'skill_'+str(skill_id)), clients)

	def load_story(self, story_name:str, client:Client) -> dict:
		return self.load_gamecfg(join('story', story_name), client)

	def load_multi_story(self, story_name:str, clients:List[Client]) -> Dict[Client, dict]:
		return self.load_multi_gamecfg(join('story', story_name), clients)

	def load_from_first_client(self, data:dict, index:Union[int, str], client_order:list=None):
		"""
		Loads the information at index from data in the first client found.

		:param data: a dict returned from load_multi_sharecfg
		:param index: the index in the sharecfg file of which data should be returnted from
		:param client_order: the order in which data should get searched in
		"""
		if client_order == None: client_order = self.DEFAULT_CLIENTS
		for client in client_order:
			if not client in data: continue
			output_data = data[client].get(index)
			if output_data == None: continue
			return output_data

	def replace_namecode(self, inputstring:str, client:Client) -> str:
		name_code = self.load_sharecfg('name_code', client)
		results = self.NAMECODE.findall(inputstring)
		for nc_replace, code in results:
			name = name_code[int(code)-1]['code']
			inputstring = inputstring.replace(nc_replace, name)
		return inputstring
	
	def load_award(self, award_type:int, award_id:int, amount:int=0) -> Award:
		return Award(award_type, award_id, amount, self)