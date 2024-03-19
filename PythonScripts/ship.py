from argparse import ArgumentParser
import math
from typing import Iterable, Union
import mwparserfromhell
import re

from lib import ALJsonAPI, Client, DEFAULT_CLIENTS, Constants, WikiHelper, Utility
from lib.apiclasses import CachedAPILoader
from lib.Constants import ShipType


SKILL_TYPE = {
	1: 'Offense',
	2: 'Defense',
	3: 'Support',
}

augment_defaults = {
	ShipType.DD: "[[{}]], [[Hammer]], [[Dual Swords]]",
	ShipType.CL: "[[{}]], [[Crossbow]], [[Sword]]",
	ShipType.CA: "[[{}]], [[Lance]], [[Greatsword]]",
	ShipType.BC: "[[{}]], [[Bowgun]], [[Officer's Sword]]",
	ShipType.BB: "[[{}]], [[Bowgun]], [[Officer's Sword]]",
	ShipType.CVL: "[[{}]], [[Scepter]], [[Hunting Bow]]",
	ShipType.CV: "[[{}]], [[Scepter]], [[Hunting Bow]]",
	ShipType.SS: "[[{}]], [[Kunai]], [[Dagger]]",
	ShipType.BBV: "[[{}]], [[Bowgun]], [[Officer's Sword]]",
	ShipType.AR: "[[{}]], [[Crossbow]]",
	ShipType.BM: "[[{}]], [[Lance]]",
	ShipType.SSV: "[[{}]], [[Kunai]], [[Dagger]]",
	ShipType.CB: "[[{}]], [[Lance]], [[Greatsword]]",
	ShipType.AE: "[[{}]], [[Lance]], [[Greatsword]]",
	ShipType.IX_S: "[[{}]]",
	ShipType.IX_V: "[[{}]]",
	ShipType.IX_M: "[[{}]]",
}

tech_type_defaults = {
	ShipType.DD: {1,20,21},
	ShipType.CL: {2},
	ShipType.CA: {3, 13, 18},
	ShipType.BC: {4, 5, 10},
	ShipType.BB: {4, 5, 10},
	ShipType.CVL: {6, 7},
	ShipType.CV: {6, 7},
	ShipType.SS: {8, 17},
	ShipType.BBV: {4, 5, 10},
	ShipType.AR: {12},
	ShipType.BM: {3, 13, 18},
	ShipType.SSV: {8, 17},
	ShipType.CB: {3, 13, 18},
	ShipType.AE: {19},
	ShipType.IX_S: {22,23,24},
	ShipType.IX_V: {22,23,24},
	ShipType.IX_M: {22,23,24}
}
allowed_tech_types = set(tech_type_defaults.keys())

def get_tech_override(shiptype, tech_shiptypes):
	#if shiptype not in allowed_tech_types: return
	#self_techtypes = set([ShipType.from_id(i) for i in tech_type_defaults[shiptype]])
	#tech_shiptypes_set = set([ShipType.from_id(i) for i in tech_shiptypes])
	#tech_shipresult = tech_shiptypes_set & allowed_tech_types
	if not (self_techtypes := tech_type_defaults.get(shiptype)):
		print(f'Warning: Unknown ship type {shiptype}!')
		return
	tech_shipresult = set(tech_shiptypes)
	if self_techtypes != tech_shipresult:
		return ' '.join(['{{'+ShipType.from_id(shiptype_).templatename+'}}' for shiptype_ in tech_shipresult])

# attribute code, parameter name, stat pos, templatename
attributes = {
	'durability':	['Health',		0,	'Health'],
	'cannon':	['Fire',		1,	'Firepower'],
	'torpedo':	['Torp',		2,	'Torpedo'],
	'antiaircraft':	['AA',			3,	'AA'],
	'air':		['Air',			4,	'Aviation'],
	'reload':	['Reload',		5,	'Reload'],
	'armor':	['ArmorDebug',		6,	'Armor'],
	'hit':		['Acc',			7,	'Accuracy'],
	'dodge':	['Evade',		8,	'Evasion'],
	'speed':	['Speed',		9,	'Speed'],
	'luck':		['Luck',		10,	'Luck'],
	'antisub':	['ASW',			11,	'ASW']
}

research_rarity = {
	"Super Rare": "Priority",
	"Ultra Rare": "Decisive"
}

# attr, enhance pos
attribute_enhance = {
	Constants.Attribute.CANNON:		0,
	Constants.Attribute.TORPEDO:		1,
	Constants.Attribute.AIR:		3,
	Constants.Attribute.RELOAD:		4,
}

attributes_retro = {
	'equipment_proficiency_1': 'Equip 1 Efficiency',
	'equipment_proficiency_2': 'Equip 2 Efficiency',
	'equipment_proficiency_3': 'Equip 3 Efficiency',
	'skill_id': ''
}

attribute_research = {
	'HP':'{{Health}}',
	'AA':'{{AA}}',
	'EVA':'{{Evasion}}'
}

equipment_slots = {
	1: 'DD Main Guns',
	2: 'CL Main Guns',
	3: 'CA Main Guns',
	4: 'BB Main Guns',
	5: 'Torpedoes',
	6: 'Anti-Air Guns',
	7: 'Fighters',
	8: 'Torpedo Bombers',
	9: 'Dive Bombers',
	10: 'Auxiliary Equipment',
	11: 'CB Main Guns',
	12: 'Seaplanes',
	13: 'Submarine Torpedoes',
	14: 'Auxiliary Equipment',
	15: 'ASW Bombers',
#	17: 'Helicopter', # NOT EXISTING (outside aux slots)
	18: 'Goods',
	21: 'Fuze AA guns', #No one rly cares
#	[1, 7]: 'DD Guns/Fighters on first Limit Break',
#	['??']: 'Submarine-mounted 203mm Gun',
#	[7, 8]: 'Fighters / Torpedo Bombers (MLB)',
}

retroicon_convert = {
	'cn_1': 'shell_1',
	'cn_2': 'shell_2',
	'cn_3': 'shell_3'
}

retroicon_class = {
	'hp_1': 'Defense',
	'hp_2': 'Defense',
	'hp_3': 'Defense',
	'as_1': 'Defense',
	'as_2': 'Defense',
	'as_3': 'Defense',
	'aa_1': 'Defense',
	'aa_2': 'Defense',
	'aa_3': 'Defense',
	'aaup_1': 'Defense',
	'aaup_2': 'Defense',
	'ffup_1': 'Defense',
	'ffup_2': 'Defense',
	'mt_blue': 'Defense',
	'skill_blue': 'Defense',
	'shell_1': 'Offense',
	'shell_2': 'Offense',
	'shell_3': 'Offense',
	'mgup_1': 'Offense',
	'mgup_2': 'Offense',
	'sgup_1': 'Offense',
	'sgup_2': 'Offense',
	'tp_1': 'Offense',
	'tp_2': 'Offense',
	'tp_3': 'Offense',
	'tpup_1': 'Offense',
	'tpup_2': 'Offense',
	'air_1': 'Offense',
	'air_2': 'Offense',
	'air_3': 'Offense',
	'bfup_1': 'Offense',
	'bfup_2': 'Offense',
	'tfup_1': 'Offense',
	'tfup_2': 'Offense',
	'mt_red': 'Offense',
	'skill_red': 'Offense',
	'rl_1': 'Support',
	'rl_2': 'Support',
	'dd_1': 'Support',
	'dd_2': 'Support',
	'hit_1': 'Support',
	'hit_2': 'Support',
	'sp_1': 'Support',
	'mt_yellow': 'Support',
	'skill_yellow': 'Support'
}

retro_plate = {
	17003: ['T3', 'Aux'],
	17013: ['T3', 'Gun'],
	17023: ['T3', 'Torp'],
	17033: ['T3', 'AA'],
	17043: ['T3', 'Plane']
}

retro_blueprint = {
	18001: ['T1', 'Destroyer'],
	18002: ['T2', 'Destroyer'],
	18003: ['T3', 'Destroyer'],
	18011: ['T1', 'Cruiser'],
	18012: ['T2', 'Cruiser'],
	18013: ['T3', 'Cruiser'],
	18021: ['T1', 'Battleship'],
	18022: ['T2', 'Battleship'],
	18023: ['T3', 'Battleship'],
	18031: ['T1', 'Carrier'],
	18032: ['T2', 'Carrier'],
	18033: ['T3', 'Carrier']
}

DD_buffs = {
	'GNR': 'Main gun shots required to trigger All-Out Assault halved',
	'AUX': 'Boosts stats given by [[List of Auxiliary Equipment|Aux Gear]] by 30%',
	'TORP': 'Spread of normal torpedo launches reduced'
}

#Could make a class_fix table to change wrong classes, then check sub_class table to check for subclass

def equip_string(eqlist):
	if len(eqlist) == 1: return equipment_slots[eqlist[0]]
	if (3 in eqlist) and (4 in eqlist): return 'CA/CB Main Guns'
	if (3 in eqlist) and (11 in eqlist): return 'CA/CB Main Guns'
	if (3 in eqlist) and (2 in eqlist): return 'CA/CL Main Guns'
	#if (2 in eqlist) and (1 in eqlist) and (12 in retrolist): return 'CL/DD Main Guns (Seaplanes on retrofit)'
	if (2 in eqlist) and (1 in eqlist): return 'CL/DD Main Guns'
	#if (2 in eqlist) and (3 in retrolist): return 'CL Main Guns (CA Main Guns on retrofit)'
	if (1 in eqlist) and (6 in eqlist): return 'DD Main Guns/Anti-Air Guns'
	if (2 in eqlist) and (6 in eqlist): return 'CL Main Guns/Anti-Air Guns'
	if (2 in eqlist) and (9 in eqlist): return 'CL Main Guns/Dive Bombers'
	#if (5 in eqlist) and (1 in retrolist): return 'Torpedoes/DD Main Guns (retrofit)'
	if (10 in eqlist) and (18 in eqlist): return 'Auxiliary Equipment/Cargo'
	if (2 in eqlist) and (10 in eqlist): return 'CL Main Guns/Auxiliary Equipment'
	if (5 in eqlist) and (10 in eqlist): return 'Torpedoes/Auxiliary Equipment'
	if (6 in eqlist) and (10 in eqlist): return 'Anti-Air Guns/Auxiliary Equipment'
	if (6 in eqlist) and (21 in eqlist): return 'Anti-Air Guns'
	if (6 in eqlist) and (15 in eqlist): return 'Anti-Air Guns/ASW Bombers'
	raise ValueError(f'Equipment types {eqlist} are unknown.')

def oil_consumption(start, end, level, api):
	ship_level = api.get_sharecfgmodule("ship_level")
	fight_oil_ratio = ship_level.load_first(level, DEFAULT_CLIENTS)['fight_oil_ratio']
	return start + math.floor(end * fight_oil_ratio / 10000)

def calculate_stat(base_stat, growth, level, enhance, affinity=1.06):
	#return (base_stat + ((level-1) * growth/1000) + enhance) * affinity
	return math.floor((base_stat + ((level-1) * growth/1000) + enhance) * affinity)

class OldIDLoader(CachedAPILoader):
	def _generate_cache(self) -> None:
		ship_data_group = self._api.get_sharecfgmodule("ship_data_group") 
		for entry in ship_data_group.load_all(DEFAULT_CLIENTS):
			self._cache[entry.group_type] = f'{entry.code:03}'
	
	def oldid_from_groupid(self, groupid: Union[int, str]) -> int:
		return self._cache.get(groupid)


def attributecode_from_id(param_id, api: ALJsonAPI, clients: Iterable[Client]):
	attribute_info_by_type = api.get_sharecfgmodule("attribute_info_by_type")
	return attribute_info_by_type.load_first(param_id, clients)['name']

def get_skilldesc(skill_data_main,max_level):
	desc = skill_data_main['desc']
	desc_add = skill_data_main['desc_add']
	for n,da in enumerate(desc_add):
		#Find letters directly before and after each $n+1 in desc for the current n, eg 'foo a$2b bar' -> [['a','b']]
		#This is to get a final skill desc of the form 'foo a1b (a10b) bar' instead of 'foo a1 (10)b bar'
		add_str = [s.split('$'+str(n+1)) for s in re.findall(r'[^ (]*\$'+str(n+1)+r'.*?\b', desc)]
		if (da_base := da[0][0]) != (da_max := da[max_level-1][0]):
			if da_base == '':
				lvl = 1
				while da_base == '':
					lvl += 1
					da_base = da[lvl-1][0]
				da_base = da_base.split(' ')
				da_max = da_max.split(' ')
				for m,word in enumerate(da_base):
					if da_max[m] != word:
						da_base[m] += ' (' + da_max[m] + ')'
				da_base = ' '.join(da_base)
				replacement = '. {} starting at skill level {}'.format(re.sub(r'^[^\w]*','',da_base),lvl)
				desc = desc.replace('$'+str(n+1), replacement,1)
			else:
				for o in add_str:
					desc = desc.replace('$'+str(n+1)+o[1], da_base+o[1]+' ('+o[0]+da_max+o[1]+')',1)
		else:
			desc = desc.replace('$'+str(n+1),da_base)
	desc = re.sub(r'\.0([^\d])',r'\1',desc)
	desc = desc.replace('Ⅰ', 'I').replace('Ⅱ', 'II').replace('Ⅲ', 'III')
	return desc


def getGameData(ship_groupid, api: ALJsonAPI, clients: Iterable[Client]):
	ship_data_group = api.get_sharecfgmodule("ship_data_group")
	ship_data_statistics = api.get_sharecfgmodule("ship_data_statistics")
	ship_data_template = api.get_sharecfgmodule("ship_data_template")
	ship_skin_template = api.get_sharecfgmodule("ship_skin_template")
	fleet_tech_ship_template = api.get_sharecfgmodule("fleet_tech_ship_template")
	fleet_tech_ship_class = api.get_sharecfgmodule("fleet_tech_ship_class")
	ship_data_blueprint = api.get_sharecfgmodule("ship_data_blueprint")
	ship_strengthen_blueprint = api.get_sharecfgmodule("ship_strengthen_blueprint")
	ship_data_trans = api.get_sharecfgmodule("ship_data_trans")
	transform_data_template = api.get_sharecfgmodule("transform_data_template")
	ship_data_strengthen = api.get_sharecfgmodule("ship_data_strengthen")
	ship_strengthen_meta = api.get_sharecfgmodule("ship_strengthen_meta")
	ship_meta_repair = api.get_sharecfgmodule("ship_meta_repair")
	ship_meta_repair_effect = api.get_sharecfgmodule("ship_meta_repair_effect")
	ship_data_breakout = api.get_sharecfgmodule("ship_data_breakout")
	ship_meta_breakout = api.get_sharecfgmodule("ship_meta_breakout")
	skill_data_template = api.get_sharecfgmodule("skill_data_template")
	skill_world_display = api.get_sharecfgmodule("skill_world_display")
	item_data_statistics = api.get_apimodule("all_item_data_statistics")
	ship_data_by_star = api.get_sharecfgmodule("ship_data_by_star")
	spweapon_data_statistics = api.get_sharecfgmodule("spweapon_data_statistics")
	ShipConverter = api.ship_converter

	# load first important ship data
	shipstat = [ ship_data_statistics.load_first(f"{ship_groupid}{i}", clients) for i in range(1, 4+1) ]
	shipvals = [ ship_data_template.load_first(f"{ship_groupid}{i}", clients) for i in range(1, 4+1) ]
	research_data = ship_data_blueprint.load_first(ship_groupid, clients)
	ship_data = dict()

	if not shipstat[0]:
		raise ValueError(f'Error: Ship "{ShipConverter.get_shipname(ship_groupid)}" does not exist on the given clients.')

	if not shipstat[3]:
		shipstat[3] = shipstat[0]
		shipvals[3] = shipvals[0]

	ship_data['GroupID'] = ship_groupid
	ship_data['ID'] = OldIDLoader(api).oldid_from_groupid(ship_groupid)
	for client in [Client.CN, Client.JP]:
		if ship0 := ship_data_statistics.load_client(f"{ship_groupid}1", client):
			ship_data[client.name+'Name'] = api.replace_namecode(ship0.name, client)


	if "special" in shipstat[0].tag_list:
		ship_data['NameOverride'] = '[['+shipstat[0].english_name.strip().split(" ",1)[1]+']]'
		ship_baseid = api.ship_converter.get_groupid(ship_data['NameOverride'][2:-2])
		if fleet_tech_data := fleet_tech_ship_template.load_client(ship_baseid, Client.EN):
			fleet_class_data = fleet_tech_ship_class.load_client(fleet_tech_data['class'], Client.EN)
			ship_data['Class'] = fleet_class_data['name'].split('-Class')[0].strip().split(' Class')[0].strip()
		if shipstat[0].name[-1:] != "μ":
			ship_data['ShipGroup'] = 'Child'
	if shipstat[0].nation._value_ > 100:
		ship_data['ShipGroup'] = 'Collab'
	ship_data['Nationality'] = shipstat[0].nation.label
	if shipstat[0].nation == Constants.Nation.META:
		ship_data['ConstructTime'] = 'META'
		ship_data['ShipGroup'] = 'META'
	ship_data['Type'] = shipstat[0].type.typename
	ship_data['Rarity'] = shipstat[0].rarity.label
	if research_data:
		ship_data['Rarity'] = research_rarity.get(ship_data['Rarity'])
	for i in shipstat[0].tag_list:
		if i[-4:] == "lass" and i[:4] != "Plan":
			ship_data['Class'] = i[:-6]
	base_star = shipstat[0].star

	# BASE STAT CALCULATION
	base_attr_val = shipstat[0].attributes
	ship_data['Armor'] = shipstat[0].armor.label
	ship_data['ConsumptionInitial'] = oil_consumption(shipvals[0].oil_at_start, shipvals[0].oil_at_end, 1, api)
	#initialise hunting range table
	if ship_data['Type'] in ('Submarine', 'Submarine Carrier', 'Sailing Frigate'):
		ship_data['Ammo'] = shipstat[0].ammo
		ship_data['Oxygen'] = shipstat[0].oxy_max
		hunt = shipstat[0].hunting_range
		x = [[' ' for i in range(7)] for i in range(7)]
		for i in range(len(hunt)):
			for j in hunt[i]:
				x[j[0]+3][j[1]+3]=str(i+1)
		x[3][3]='x'
		ship_data['Range'] = '{{HuntingRange/Alternative\n    |' + '|\n    |'.join(['|'.join(i) for i in x]) + '|\n  }}'
	for attr, val in base_attr_val.items():
		if attr in [Constants.Attribute.SPEED, Constants.Attribute.LUCK]:
			#ship_data[attr.wiki_param_name] = val
			ship_data[attr.wiki_param_name] = math.floor(val)
		else:
			#ship_data[attr.wiki_param_name + "Initial"] = val
			ship_data[attr.wiki_param_name + "Initial"] = math.floor(val)

	# LVL 100/120 STAT CALCULATION
	attr_dicts = [shipstat[3].attributes, shipstat[3].attributes_growth]
	lb3_attrs = {k: [d[k] for d in attr_dicts] for k in attr_dicts[0]}
	if shipstat[0].nation == Constants.Nation.META:
		enhance_json = ship_strengthen_meta.load_first(ship_groupid, clients)
		enhance_data = {}
		for k in ["cannon", "air", "reload", "torpedo"]:
			enhance_data[k] = 0
			for i in enhance_json["repair_" + k]:
				repair = ship_meta_repair.load_first(str(i), clients)
				attrlist = repair.effect_attr.copy()
				if type(attrlist) is list:
					enhance_data[attrlist[0]] += attrlist[1]
		for i in enhance_json["repair_effect"]:
			repair_extra = ship_meta_repair_effect.load_first(str(i[1]), clients)
			attrlist = repair_extra.effect_attr.copy()
			if type(attrlist) is list:
				for j in attrlist:
					try:
						enhance_data[j[0]] += j[1]
					except:
						enhance_data[j[0]] = j[1]
	else:
		enhance_data = ship_data_strengthen.load_first(ship_groupid, clients)
		
	# DEV LEVELS
	if research_data:
		ship_data['ShipGroup'] = 'Research'
		ship_data['ConstructTime'] = 'Research'
		strengthen_data = {}
		extra_eff = {}
		enhance_list = [0,0,0,0,0]
		for i in research_data.strengthen_effect:
			strengthen = ship_strengthen_blueprint.load_first(str(i), clients)
			attr = strengthen.effect_attr
			enhance = strengthen.effect
			if i%5 == 0:
				# EXTRA EQUIP EFF
				if strengthen.effect_equipment_proficiency:
					try:
						extra_eff[strengthen.effect_equipment_proficiency[0]] += strengthen.effect_equipment_proficiency[1]
					except:
						extra_eff[strengthen.effect_equipment_proficiency[0]] = strengthen.effect_equipment_proficiency[1]
				# DEV LEVEL DESC
				dev_list = list(strengthen.effect_desc.split('|'))
				for j in strengthen.extra_desc:
					dev_list.append(j)
				dev_clone = dev_list.copy()
				for j in range(len(dev_clone)):
					if dev_clone[j][:2] in attribute_research and dev_clone[j].strip()[-1] != '%':
						if j == 0:
							dev_list[0] = attribute_research[dev_clone[j][:2]] + ' ' + dev_clone[j][2:].replace(' ','')
						else: 
							dev_list[0] += ', ' + attribute_research[dev_clone[j][:2]] + ' ' + dev_clone[j][2:].replace(' ','')
							dev_list.remove(dev_clone[j])
					if dev_clone[j][:3] in attribute_research:
						if j == 0:
							dev_list[0] = attribute_research[dev_clone[j][:3]] + ' ' + dev_clone[j][3:].replace(' ','')
						else: 
							dev_list[0] += ', ' + attribute_research[dev_clone[j][:3]] + ' ' + dev_clone[j][3:].replace(' ','')
							dev_list.remove(dev_clone[j])
					if 'Limit' in dev_clone[j] or 'Unlock' in dev_clone[j]:
						dev_list.remove(dev_clone[j])
				for j in range(len(dev_list)):
					dev_list[j] = dev_list[j].replace('base','Mount')
				ship_data['B'+str(i%100)] = '<li>'+'</li><li>'.join(dev_list)+'</li>'
			# EXTRA STATS (Not really how it works, but adding to enhance values is easier)
			if type(attr) is list:
				for j in attr:
					try:
						strengthen_data[j[0]] += j[1]
					except:
						strengthen_data[j[0]] = j[1]
			for j in range(len(enhance)):
				enhance_list[j] += enhance[j]
				
		# FATE SIM
		luck_max = 0
		change_skill_list = []
		for i in research_data.fate_strengthen:
			strengthen = ship_strengthen_blueprint.load_first(str(i), clients)
			attrlist = strengthen.effect_attr
			change_skill = strengthen.change_skill
			if type(attrlist) is list:
				for j in attrlist:
					luck_max += j[1]
			if type(change_skill) is list:
				change_skill_list.append(change_skill)
		ship_data['LuckMax'] = str(luck_max)
	ship_data['ConsumptionMax'] = oil_consumption(shipvals[3].oil_at_start, shipvals[3].oil_at_end, 100, api)
	ship_data['ReinforcementValue'] = ''
	for attr, attr_vals in lb3_attrs.items():
		attr_val, attr_growth = attr_vals
		enhance_val = 0
		if shipstat[0].nation != Constants.Nation.META:
			if (enhanceslot := attribute_enhance.get(attr)) is not None:
				enhance_val = enhance_data.durability[enhanceslot]
				if research_data:
					enhance_val = enhance_list[enhanceslot]/100
				else:
					ship_data['ReinforcementValue'] += ' {{'+attr.wiki_template_name+'}} ' + str(enhance_data.attr_exp[enhanceslot])
			if research_data:
				enhance_val += strengthen_data.get(str(attr).lower(),0)#Dirty, but works
		else:
			try:
				enhance_val = enhance_data[str(attr).lower()]
			except:
				pass
		
		if attr.wiki_param_name == 'Luck':
			continue

		ship_data[attr.wiki_param_name+'Max'] = calculate_stat(attr_val, attr_growth, 100, enhance_val)
		ship_data[attr.wiki_param_name+'120'] = calculate_stat(attr_val, attr_growth, 120, enhance_val)
		ship_data[attr.wiki_param_name+'125'] = calculate_stat(attr_val, attr_growth, 125, enhance_val)
	ship_data['ReinforcementValue'] = ship_data['ReinforcementValue'].strip()


	# TECH POINTS
	if fleet_tech_data := fleet_tech_ship_template.load_first(ship_groupid, DEFAULT_CLIENTS):
		ship_data['TechPointCollect'] = fleet_tech_data['pt_get']
		ship_data['TechPointMLB'] = fleet_tech_data['pt_upgrage']
		ship_data['TechPoint120'] = fleet_tech_data['pt_level']

		ship_data['StatBonusCollectOverride'] = get_tech_override(shipstat[0].type, fleet_tech_data['add_get_shiptype'])
		ship_data['StatBonusCollectType'] = attributes[attributecode_from_id(fleet_tech_data['add_get_attr'], api, clients)][2]
		ship_data['StatBonusCollect'] = fleet_tech_data['add_get_value']
		ship_data['StatBonus120Override'] = get_tech_override(shipstat[0].type, fleet_tech_data['add_level_shiptype'])
		ship_data['StatBonus120Type'] =  attributes[attributecode_from_id(fleet_tech_data['add_level_attr'], api, clients)][2]
		ship_data['StatBonus120'] = fleet_tech_data['add_level_value']
		fleet_class_data = fleet_tech_ship_class.load_first(fleet_tech_data['class'], DEFAULT_CLIENTS)
		ship_data['Class'] = fleet_class_data['name'].split('-Class')[0].strip().split(' Class')[0].strip()

	# LIMIT BREAK, DEV LEVELS WITHOUT FORMATTING
	if not research_data:
		if shipstat[0].nation == Constants.Nation.META:
			ship_data_breakout = ship_meta_breakout
		for i in range(1, 4):
			lb_data = ship_data_breakout.load_first(ship_groupid*10+i, DEFAULT_CLIENTS)
			if lb_data:
				ship_data['LB'+str(i)] = lb_data['breakout_view'].replace('/',' / ')
		if ship_data['Type'] == "Destroyer" and shipstat[0].nation != Constants.Nation.UNIVERSAL2:
			DD_buff = shipvals[3].specific_type[0]
			ship_data['LB3'] += ' / '+DD_buffs[DD_buff]

	# EQUIPMENT SLOTS, CHANGES AT LB HALF IMPLEMENTED
	equip_percent_base = shipstat[0]['equipment_proficiency']
	equip_percent_max = shipstat[3]['equipment_proficiency']
	for i in range(3):
		ship_data[f'Eq{i+1}EffInit'] = format(equip_percent_base[i], '.0%')
		ship_data[f'Eq{i+1}BaseMax'] = shipstat[3]['base_list'][i]
		ship_data[f'Eq{i+1}EffInitMax'] = format(equip_percent_max[i], '.0%')
		if research_data:
			if i+1 in extra_eff.keys(): ship_data[f'Eq{i+1}EffInitMax'] = format(equip_percent_max[i] + extra_eff[i+1], '.0%')
			

	equip_type = {
		1: shipvals[0]['equip_1'],
		2: shipvals[0]['equip_2'],
		3: shipvals[0]['equip_3']
	}
	equip_type_old = equip_type.copy()
	for i, shipval in enumerate(shipvals):
		if not shipval: continue
		for j in range(1, 4):
			equip_type_new = shipval['equip_'+str(j)]
			if set(equip_type_new) != set(equip_type_old[j]):
				print(f'{shipstat[0].name}: Changed equipment @ {i}LB and {j} Slot: from {equip_type_old[j]} to {equip_type_new}.')
			equip_type_old[j] = equip_type_new
				
	for i in range(1, 4):
		ship_data['Eq'+str(i)+'Type'] = equip_string(equip_type[i])
		if 4 in shipvals[0]['equip_'+str(i)]:
			ship_data[f'Eq{i}BaseMax'] += shipvals[3]['hide_buff_list'][0]
	
	ghost_equip = []
	for i, stat in enumerate(shipstat):
		if stat and stat['fix_equip_list'] != ghost_equip:
			ghost_equip = stat['fix_equip_list']
			print(f"Equip ghost equip {ghost_equip} @ LB{i}")

	augment = api.augment_converter.from_shipid(ship_groupid)
	if augment:
		ship_data['MeleeOverride'] = augment_defaults[shipstat[0].type].format(augment.wikiname)
		aug10_id = int(augment.id)+10
		aug10 = spweapon_data_statistics.load_first(aug10_id,clients)
		augment_skill = aug10.skill_upgrade[0]

	# RETROFIT
	retrofit_data = ship_data_trans.load_first(ship_groupid, DEFAULT_CLIENTS)
	if retrofit_data:
		retro_stats = {}
		retro_effs = {}
		retro_ship_id = None
		retro_skill = None
		ship_data['Remodel'] = 1
		letters = list('ABCDEFGHIJKL')
		traversed_nodes = 0
		retromap = ['', '', '']
		nodeid_to_letter = dict()
		for retro_col in retrofit_data['transform_list']:
			used_heights = []
			for retro_node in retro_col:
				height = retro_node[0]-2
				letter = letters[traversed_nodes]
				retromap[height] += letter
				used_heights.append(height)

				retro_node_id = retro_node[1]
				nodeid_to_letter[retro_node_id] = letter
				retro_node_data = transform_data_template.load_first(retro_node_id, DEFAULT_CLIENTS)

				ship_data['Index'+letter] = letter
				icon = retro_node_data['icon'].lower()
				if icon[:5] == "mode_": continue
				if icon in retroicon_convert: icon = retroicon_convert[icon]
				ship_data['RetrofitImage'+letter] = icon
				ship_data['ProjName'+letter] = retro_node_data['name']
				ship_data['ProjType'+letter] = retroicon_class[icon]
				
				# RETROFIT INTO DIFFERENT SHIP_ID
				if retro_node_data['ship_id']: # (Only entered once at most)
					retro_ship_id = retro_node_data['ship_id'][0][1]
					retrostat = ship_data_statistics.load_first(retro_ship_id, clients)
					retrovals = ship_data_template.load_first(retro_ship_id, clients)
					retro_type = retrostat.type.typename
					if retro_type != ship_data['Type']:
						ship_data['SubtypeRetro'] = retro_type
					attr_dicts = [retrostat.attributes, retrostat.attributes_growth]
					retro_attrs = {k: [d[k] for d in attr_dicts] for k in attr_dicts[0]}
					retro_enhance_id = retrovals.strengthen_id
					retro_enhance_data = ship_data_strengthen.load_first(retro_enhance_id, clients)
					
					for attr, attr_vals in retro_attrs.items():
						attr_val, attr_growth = attr_vals
						enhance_val = 0
						if (enhanceslot := attribute_enhance.get(attr)) is not None:
							enhance_val = retro_enhance_data.durability[enhanceslot]
						ship_data[attr.wiki_param_name+'Kai'] = calculate_stat(attr_val, attr_growth, 100, enhance_val)
						ship_data[attr.wiki_param_name+'Kai120'] = calculate_stat(attr_val, attr_growth, 120, enhance_val)
						ship_data[attr.wiki_param_name+'Kai125'] = calculate_stat(attr_val, attr_growth, 125, enhance_val)
						if attr.wiki_param_name == 'Speed':
							ship_data['SpeedKai'] = math.floor(attr_val)
					
					for i in range(3):
						ship_data[f'Eq{i+1}BaseKai'] = retrostat['base_list'][i]
						equip_percent_retro = retrostat['equipment_proficiency']
						ship_data[f'Eq{i+1}EffInitKai'] = format(equip_percent_retro[i], '.0%')
						
						if 4 in retrovals['equip_'+str(i+1)]:
							ship_data[f'Eq{i+1}BaseKai'] += retrovals['hide_buff_list'][0]
						equip_type_new = retrovals['equip_'+str(i+1)]
						if set(equip_type_new) != set(equip_type_old[i+1]):
							print(f'{shipstat[0].name}: Changed equipment @ Retrofit and {i+1} Slot: from {equip_type_old[i+1]} to {equip_type_new}.')
						equip_type_old[i+1] = equip_type_new
					#Equip slots that change at retrofit not implemented
				
				if retro_node_data.descrip:
					print(f'{retro_node_data.name} Description: "{retro_node_data.descrip}"')

				attribute = ''
				attribute_data = dict()
				for effect in retro_node_data['effect']:
					for attribute_code, value in effect.items():
						if not attribute_code in attribute_data:
							attribute_data[attribute_code] = list()
						attribute_data[attribute_code].append(value)
				firstattr = True
				for attribute_code, values in attribute_data.items():
					if firstattr: firstattr = False
					else: attribute += ', '
					valtype = 'Normal'
					if attribute_code == 'skill_id': #Will break if this is entered more than once
						retro_skill = skill_data_template.load_client(values[0], Client.EN)
						attribute += f'Unlock Skill "{retro_skill.name}"'
						continue
					elif attribute_code in attributes:
						try: retro_stats[attributes[attribute_code][2]] += sum(values)
						except: retro_stats[attributes[attribute_code][2]] = sum(values)
						attribute_name = '{{'+attributes[attribute_code][2]+'}}'
					elif attribute_code in attributes_retro:
						try: retro_effs[attributes_retro[attribute_code]] += sum(map(lambda x: int(str(x)[2:]),values))
						except: retro_effs[attributes_retro[attribute_code]] = sum(map(lambda x: int(str(x)[2:]),values))
						attribute += retro_node_data.name.split('Improvement')[0] + 'Efficiency '
						#print(attributes_retro[attribute_code], values) #Useful to check which retro Eff upgrade has a wrong name if there is one
						valtype = 'Eff'
					else:
						raise NotImplementedError(f"not implemented retro attribute '{attribute_code}'")

					firstval = True
					for value in values:
						if firstval: firstval = False
						else: attribute += ' / '

						if valtype == 'Eff': value = str(int(value*100))+'%'
						else: attribute += attribute_name + ' '
						attribute += '+' + str(value)

				ship_data['Attribute'+letter] = attribute

				bps = list()
				plates = list()
				otheritems = list()
				for stage in retro_node_data['use_item']:
					for item in stage:
						itemid = item[0]
						if itemid in retro_blueprint: bps.append(item)
						elif itemid in retro_plate: plates.append(item)
						else: otheritems.append(item)

				bpnum_str = ''
				for bpitem in bps:
					bpitem_res = retro_blueprint[bpitem[0]]
					ship_data['BPRarity'+letter] = bpitem_res[0]
					if bpnum_str: bpnum_str += ' / '+str(bpitem[1])
					else: bpnum_str = str(bpitem[1])
				ship_data['BPNum'+letter] = bpnum_str

				platenum_str = ''
				for plateitem in plates:
					plateitem_res = retro_plate[plateitem[0]]
					ship_data['PlateTier'+letter] = plateitem_res[0]
					ship_data['PlateType'+letter] = plateitem_res[1]
					if platenum_str: platenum_str += ' / '+str(plateitem[1])
					else: platenum_str = str(plateitem[1])
				ship_data['PlateNum'+letter] = platenum_str

				ship_data['Coin'+letter] = retro_node_data['use_gold']
				ship_data['LV'+letter] = retro_node_data['level_limit']
				ship_data['LimitBreak'+letter] = retro_node_data['star_limit'] - base_star
				ship_data['Repeat'+letter] = retro_node_data['max_level']

				req = ''
				for req_nodeid in retro_node_data['condition_id']:
					if req: req += ', '
					req += nodeid_to_letter[req_nodeid]
				ship_data['Requirements'+letter] = req

				traversed_nodes += 1

			for i in range(3):
				if i not in used_heights:
					retromap[i] += '-'

		ship_data['RetrofitMap'] = ''
		for retromappart in retromap:
			ship_data['RetrofitMap'] += '['+retromappart+']'
		# RETROFIT STATS
		for attr, attr_vals in lb3_attrs.items():
			if attr.wiki_param_name == 'Luck':
				continue
			if retro_ship_id:
				try:
					ship_data[attr.wiki_param_name+'Kai'] = ship_data[attr.wiki_param_name+'Kai'] + retro_stats[attr.wiki_template_name]
					ship_data[attr.wiki_param_name+'Kai120'] = ship_data[attr.wiki_param_name+'Kai120'] + retro_stats[attr.wiki_template_name]
					ship_data[attr.wiki_param_name+'Kai125'] = ship_data[attr.wiki_param_name+'Kai125'] + retro_stats[attr.wiki_template_name]
				except: continue
			else:
				try:
					ship_data[attr.wiki_param_name+'Kai'] = ship_data[attr.wiki_param_name+'Max'] + retro_stats[attr.wiki_template_name]
					ship_data[attr.wiki_param_name+'Kai120'] = ship_data[attr.wiki_param_name+'120'] + retro_stats[attr.wiki_template_name]
					ship_data[attr.wiki_param_name+'Kai125'] = ship_data[attr.wiki_param_name+'125'] + retro_stats[attr.wiki_template_name]
				except:
					ship_data[attr.wiki_param_name+'Kai'] = ship_data[attr.wiki_param_name+'Max']
					ship_data[attr.wiki_param_name+'Kai120'] = ship_data[attr.wiki_param_name+'120']
					ship_data[attr.wiki_param_name+'Kai125'] = ship_data[attr.wiki_param_name+'125']
				try:
					ship_data['SpeedKai'] = ship_data['Speed'] + retro_stats['Speed']
				except: pass
		# RETROFIT EQUIP
		for i in range(1,4):
			if retro_ship_id:
				try: ship_data[f'Eq{i}EffInitKai'] = f"{int(ship_data[f'Eq{i}EffInitKai'][:-1])+retro_effs[f'Equip {i} Efficiency']}%"
				except: continue
			else:
				try: ship_data[f'Eq{i}EffInitKai'] = f"{int(ship_data[f'Eq{i}EffInitMax'][:-1])+retro_effs[f'Equip {i} Efficiency']}%"
				except: ship_data[f'Eq{i}EffInitKai'] = f"{int(ship_data[f'Eq{i}EffInitMax'][:-1])}%"

	# SKILLS
	#Initialise skill list for LB1 (For AoA, LB0 if Bulin) and full skill_list
	if shipvals[1]:
		skill_list_0 = shipvals[1]['buff_list_display']
		skill_list_n = set(shipvals[1]['buff_list'])|(set(skill_list_0)&set(shipvals[3]['buff_list']))
	else:
		skill_list_0 = shipvals[0]['buff_list_display']
		skill_list_n = shipvals[0]['buff_list']
	#If a skill is buff_list_display, but not in buff_list (shows as locked) it is a retro skill unless the ship is a META ship
	skill_list = [(i,'') if i in skill_list_n or shipstat[0].nation == Constants.Nation.META else (i,'RN') for i in skill_list_0]
	if shipvals[3]:
                #Insert skills changed by LB (AoA) in skill_list after the original skill (Wouldn't handle jumbled order of skills well) 
		skill_list_3 = shipvals[3]['buff_list_display']
		if skill_list_3 != skill_list_0:
			c = 0
			for i in skill_list_3:
				if i not in skill_list_0:
					c += 1
					skill_list.insert(c,(i,'LB'))
				c += 1
	if augment:
		old,new = augment_skill
		for n,i in enumerate(skill_list):
			if i[0] == old:
				skill_list.insert(n+1,(new,'A'))
	if retrofit_data:
		if retro_ship_id: #Skills can only be replaced on retrofit with a new ship_id
			skill_list_r = retrovals['buff_list_display']
			if skill_list_r != skill_list_3:
				c = 0
				for i in skill_list_r:
					if i not in skill_list_3:
						if len(skill_list) > c+1:
							#Check if next skill has been replaced by LB (aka skill_list[c] is AoA)
							if skill_list[c+1][1] == 'LB':
								skill_data_main = skill_data_template.load_client(i, Client.EN)
								for client in [Client.CN, Client.JP]:
									if not skill_data_main:
										if skill_data := skill_data_template.load_client(i, client):
											skill_data_main = skill_data
								#If it is indeed AoA (or similar), insert after 'LB' and skip 2 since this skill replaces both of them
								if skill_data_main['max_level'] == 1:
									c += 2
									skill_list.insert(c,(i,'R'))
								#If it is not AoA, insert before AoA as new skill (Shouldn't happen as new skills should be in skill_list_3)
								else:
									print('Warning: Unexpected buff_list')
									skill_list.insert(c,(i,'RN'))
							else:
								c += 1
								skill_list.insert(c,(i,'R'))
						elif len(skill_list) > c and skill_list[c][1] == 'LB':
							print('Warning: Unexpected buff_list')
						else:
							c += 1
							skill_list.insert(c,(i,'R'))
					c += 1
					
	elif research_data:
		if change_skill_list:
			for i in change_skill_list:
				for c,j in enumerate(skill_list):
					if str(i[0]) == str(j[0]):
						#Insert the skill changed by Fate Sim after the skill it changes
						skill_list.insert(c+1,(i[1],'FS'))
	ops_skills = skill_world_display.all_ids(clients)
	skill_n = 1
	ship_temp_data = dict()
	for i in skill_list:
		skillid = i[0]
		skill_data_client = Client.EN
		skill_data_main = skill_data_template.load_client(skillid, skill_data_client)
		for client in [Client.CN, Client.JP]:
			if skill_data := skill_data_template.load_client(skillid, client):
				try: ship_temp_data['Skill'+str(skill_n)+client.name] = api.replace_namecode(skill_data['name'], client)
				except: pass
				if not skill_data_main:
					skill_data_client = client
					skill_data_main = skill_data
					
		desc = get_skilldesc(skill_data_main,skill_data_main.max_level)
		if skillid in ops_skills:
			skill_data_ops = skill_world_display.load_first(skillid,clients)
			desc_ops = get_skilldesc(skill_data_ops,skill_data_main.max_level)
			desc +='\n' + desc_ops

		if i[1] == 'LB':
			#For AoA get AoA 1 and AoA 2 name and desc
			name1 = ship_data['Skill'+str(skill_n-1)]
			try: name2 = api.replace_namecode(skill_data_main.name, skill_data_client)
			except: pass
			desc1 = ship_data['Skill'+str(skill_n-1)+'Desc']

			words1 = re.sub(r'; (\w)',lambda m: '. '+m.expand(r'\1').upper(),desc1).split(' ')
			words2 = re.sub(r'; (\w)',lambda m: '. '+m.expand(r'\1').upper(),desc).split(' ')
			
			#Extract desc that only applies for one of the skills (Can break on newlines in skill desc)
			#Probably not working properly on skills with more effect on AoA I, fix it whenever that happens 
			afterwords = ''
			if len(words1) != len(words2):
				words = sorted(((name1,words1),(name2,words2)),key=lambda e: len(e[1]))
				afterwords = f"\n{words[1][0]} only: "+' '.join(words[1][1][len(words[0][1]):])
			
			ship_data['Skill'+str(skill_n-1)] = name1.replace('Ⅰ', '').replace('I', '').strip()
			for client in [Client.CN, Client.JP]:
				ship_data['Skill'+str(skill_n-1)+client.name] = ship_data['Skill'+str(skill_n-1)+client.name].replace('Ⅰ', '').replace('I','').strip()

			#Find all occurances of Roman and normal numbers for both AoA lvls and format them into 1 string
			n1 = [s for s in re.findall(r'(?:[^\ \d(]*[\d]+(?:\.\d+)?[^\ \d.:)]*|\bI+\b)', desc1)]
			n2 = [s for s in re.findall(r'(?:[^\ \d(]*[\d]+(?:\.\d+)?[^\ \d.:)]*|\bI+\b)', desc)]
			max_len = min(len(n1),len(n2))
			for n in range(max_len):
				if n1[n] != n2[n]:
					desc1 = desc1.replace(n1[n],f"${n}",1)
			for n in range(max_len):
				desc1 = desc1.replace(f"${n}",f"{n1[n]} ({n2[n]})")
			ship_data['Skill'+str(skill_n-1)+'Desc'] = api.replace_namecode(desc1+afterwords, skill_data_client)
		
		elif i[1] == 'R' and skill_list[skill_n-1][1] == 'LB':
			#Filter out retrofit with new AoA
			ship_data['Skill'+str(skill_n-1)+'Desc'] += f"\n'''(Upon Retrofit)''' {desc}"
		else:
			#All of these add a new skill to the list
			try: ship_data['Skill'+str(skill_n)+'Desc'] = api.replace_namecode(desc, skill_data_client)
			except: ship_data['Skill'+str(skill_n)+'Desc'] = desc
			if 'R' in i[1]:
				#Retrofit skill
				ship_data['Skill'+str(skill_n)] = '(Retrofit) '
				if 'N' not in i[1] and skill_list[skill_n-2][1] != 'R':
					#Not a new retrofit skill, so replacement for the skill before and check if skill before is not in by retro too
					#(Might break on 2 or more replacing retro skills) 
					ship_data['Skill'+str(skill_n)+'Desc'] += f"\n'''(Replaces {ship_data['Skill'+str(skill_n-1)]})'''"
			elif i[1] == 'FS':
				#Replacement skill from Fate Sim
				ship_data['Skill'+str(skill_n)] = '(Fate Simulation)<br>'
				ship_data['Skill'+str(skill_n)+'Desc'] += f"\n'''(Replaces {ship_data['Skill'+str(skill_n-1)]})'''"
			elif i[1] == 'A':
				#Replacement from unique Augment Module
				ship_data['Skill'+str(skill_n)] = '(Augment Module)<br>'
				ship_data['Skill'+str(skill_n)+'Desc'] += f"\n'''(Replaces {ship_data['Skill'+str(skill_n-1)]})'''"
			else:
				#Only base skills left now
				ship_data['Skill'+str(skill_n)] = ''

			try: ship_data['Skill'+str(skill_n)] += api.replace_namecode(skill_data_main['name'], skill_data_client)
			except: pass
			for client in [Client.CN, Client.JP]:
				ship_data['Skill'+str(skill_n)+client.name] = ship_temp_data.get('Skill'+str(skill_n)+client.name,'Skill'+str(skill_n)+client.name)
			buffdata = api.loader.load_buff(skillid, skill_data_client)
			ship_data['Skill'+str(skill_n)+'Icon'] = buffdata.get('icon', skillid)

			ship_data['Type'+str(skill_n)] = SKILL_TYPE[skill_data_main['type']]
			skill_n += 1
	return ship_data


def getWikiData(shipname):
	wikiclient = WikiHelper.WikiClient().login()
	wikipage = wikiclient.mwclient.pages[shipname]
	parsed_template_data = dict()
	if wikipage.exists:
		mwparser = mwparserfromhell.parse(wikipage.text())
		templates = mwparser.filter_templates()
		for template in templates:
			if not 'Ship' in template.name: continue
			parsed_template_data = WikiHelper.parse_multiline_template(template)
	return parsed_template_data


def main():
	parser = ArgumentParser()
	parser.add_argument("-c", "--clients", choices=Client.__members__, default = ['EN'], nargs = '+',
						help="clients to gather information from (default: EN)")
	parser.add_argument("-n", "--name", required=True, type=str,
						help="name of the ship to get info from")
	args = parser.parse_args()

	clients = [ Client[c] for c in args.clients ]
	api = ALJsonAPI()
	groupid = api.ship_converter.get_groupid(args.name)
	if not groupid:
		try: groupid = int(args.name)
		except: raise ValueError(f'Error: "{args.name}" is not a valid/unique ship name.')
	template_data_game = getGameData(groupid, api, clients)
	ship_template = WikiHelper.MultilineTemplate("Ship")
	wikitext = ship_template.fill(template_data_game)
	Utility.output(wikitext)

if __name__ == "__main__":
	main()
