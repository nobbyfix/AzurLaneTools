from abc import abstractmethod
from argparse import ArgumentParser
import math
from typing import Any, Iterable, Union
from typing_extensions import Required
import mwparserfromhell

from lib import ALJsonAPI, Client, DEFAULT_CLIENTS, Constants, WikiHelper, Utility
from lib.apiclasses import CachedAPILoader
from lib.Constants import ShipType


SKILL_TYPE = {
	1: 'Offense',
	2: 'Defense',
	3: 'Support',
}

tech_type_defaults = {
	ShipType.DD: {1},
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
	ShipType.CV: {3, 13, 18},
	ShipType.AE: {19},
}
allowed_tech_types = set(tech_type_defaults.keys())

def get_tech_override(shiptype, tech_shiptypes):
	if shiptype not in allowed_tech_types: return
	self_techtypes = tech_type_defaults[shiptype]
	tech_shipresult = set(tech_shiptypes) & allowed_tech_types
	if self_techtypes != tech_shipresult:
		return ' '.join(['{{'+ship_type[shiptype_][1]+'}}' for shiptype_ in tech_shipresult])

# attribute code, parameter name, stat pos, templatename
attributes = {
	'durability':	['Health',		0,	'Health'],
	'cannon':		['Fire',		1,	'Firepower'],
	'torpedo':		['Torp',		2,	'Torpedo'],
	'antiaircraft':	['AA',			3,	'AA'],
	'air':			['Air',			4,	'Aviation'],
	'reload':		['Reload',		5,	'Reload'],
	'armor':		['ArmorDebug',	6,	'Armor'],
	'hit':			['Acc',			7,	'Accuracy'],
	'dodge':		['Evade',		8,	'Evasion'],
	'speed':		['Speed',		9,	'Speed'],
	'luck':			['Luck',		10,	'Luck'],
	'antisub':		['ASW',			11,	'ASW']
}

# attr, enhance pos
attribute_enhance = {
	Constants.Attribute.CANNON:		0,
	Constants.Attribute.TORPEDO:	1,
	Constants.Attribute.AIR:		3,
	Constants.Attribute.RELOAD:		4,
}

attributes_retro = {
	'equipment_proficiency_1': 'Equip 1 Efficiency',
	'equipment_proficiency_2': 'Equip 2 Efficiency',
	'equipment_proficiency_3': 'Equip 3 Efficiency',
	'skill_id': ''
}

equipment_slots = {
	1: 'DD Guns',
	2: 'CL Guns',
	3: 'CA Guns',
	4: 'BB Guns',
	5: 'Torpedoes',
	6: 'Anti-Air Guns',
	7: 'Fighters',
	8: 'Torpedo Bombers',
	9: 'Dive Bombers',
	10: 'Auxiliary Equipment',
	11: 'CB Guns', 
	12: 'Seaplanes',
	13: 'Submarine Torpedoes',
	14: 'Auxiliary Equipment',
#	15: 'ASW Aircraft', # NOT EXISTING
#	17: 'Helicopter', # NOT EXISTING
	18: 'Goods',
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
	if (3 in eqlist) and (4 in eqlist): return 'CA/CB Guns'
	if (3 in eqlist) and (11 in eqlist): return 'CA/CB Guns'
	if (3 in eqlist) and (2 in eqlist): return 'CA/CL Guns'
	#if (2 in eqlist) and (1 in eqlist) and (12 in retrolist): return 'CL/DD Guns (Seaplanes on retrofit)'
	if (2 in eqlist) and (1 in eqlist): return 'CL/DD Guns'
	#if (2 in eqlist) and (3 in retrolist): return 'CL Guns (CA Guns on retrofit)'
	if (2 in eqlist) and (6 in eqlist): return 'CL Guns/Anti-Air Guns'
	if (2 in eqlist) and (9 in eqlist): return 'CL Guns/Dive Bombers'
	#if (5 in eqlist) and (1 in retrolist): return 'Torpedoes/DD Guns (retrofit)'
	if (10 in eqlist) and (18 in eqlist): return 'Auxiliary Equipment++'
	if (2 in eqlist) and (10 in eqlist): return 'CL Guns/Auxiliary Equipment'
	if (5 in eqlist) and (10 in eqlist): return 'Torpedoes/Auxiliary Equipment'
	if (6 in eqlist) and (10 in eqlist): return 'Anti-Air Guns/Auxiliary Equipment'
	raise ValueError(f'Equipment types {eqlist} are unknown.')

def oil_consumption(start, end, level, api):
	ship_level = api.get_sharecfgmodule("ship_level")
	fight_oil_ratio = ship_level.load_first(level, DEFAULT_CLIENTS)['fight_oil_ratio']
	return start + math.floor(end * fight_oil_ratio / 10000)

def calculate_stat(base_stat, growth, level, enhance, affinity=1.06):
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
	item_data_statistics = api.get_sharecfgmodule("item_data_statistics")
	ship_data_by_star = api.get_sharecfgmodule("ship_data_by_star")
	ShipConverter = api.ship_converter

	# load first important ship data
	shipstat = [ ship_data_statistics.load_first(f"{ship_groupid}{i}", clients) for i in range(1, 4+1) ]
	shipvals = [ ship_data_template.load_first(f"{ship_groupid}{i}", clients) for i in range(1, 4+1) ]
	research_data = ship_data_blueprint.load_first(ship_groupid, clients)

	ship_data = dict()

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
	ship_data['Type'] = shipstat[0].type.typename
	ship_data['Rarity'] = shipstat[0].rarity.label
	for i in shipstat[0].tag_list:
		if i[-4:] == "lass" and i[:4] != "Plan":
			ship_data['Class'] = i[:-6]
	base_star = shipstat[0].star																								#<----------------PRINT

	# BASE STAT CALCULATION
	base_attr_val = shipstat[0].attributes
	ship_data['Armor'] = shipstat[0].armor.label
	ship_data['ConsumptionInitial'] = oil_consumption(shipvals[0].oil_at_start, shipvals[0].oil_at_end, 1, api)
	for attr, val in base_attr_val.items():
		if attr in [Constants.Attribute.SPEED, Constants.Attribute.LUCK]:
			ship_data[attr.wiki_param_name] = math.floor(val)
		else:
			ship_data[attr.wiki_param_name + "Initial"] = math.floor(val)

	# LVL 100/120 STAT CALCULATION
	if shipstat[3]:
		attr_dicts = [shipstat[3].attributes, shipstat[3].attributes_growth]
		lb3_attrs = {k: [d[k] for d in attr_dicts] for k in attr_dicts[0]}
		if shipstat[3].nation == Constants.Nation.META:
			enhance_json = ship_strengthen_meta.load_first(ship_groupid, clients)
			enhance_json = enhance_json._json
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
			for i in research_data.strengthen_effect:
				strengthen = ship_strengthen_blueprint.load_first(str(i), clients)
				attr = strengthen.effect_attr
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
					for j in dev_list.copy():
						if 'Limit' in j or 'Unlock' in j:
							dev_list.remove(j)
					for j in range(len(dev_list)):
						dev_list[j] = dev_list[j].replace('base','Mount')
					ship_data['B'+str(i%100)] = str(dev_list)
				# EXTRA STATS (Not really how it works, but adding to enhance values is easier)
				if type(attr) is list:
					for j in attr:
						try:
							strengthen_data[j[0]] += j[1]
						except:
							strengthen_data[j[0]] = j[1]
			# FATE SIM
			luck_max = 0
			for i in research_data.fate_strengthen:
				strengthen = ship_strengthen_blueprint.load_first(str(i), clients)
				attrlist = strengthen.effect_attr
				if type(attrlist) is list:
					for j in attrlist:
						luck_max += j[1]
			ship_data['LuckMax'] = str(luck_max)
		ship_data['ConsumptionMax'] = oil_consumption(shipvals[3].oil_at_start, shipvals[3].oil_at_end, 100, api)
		ship_data['ReinforcementValue'] = ''
		for attr, attr_vals in lb3_attrs.items():
			attr_val, attr_growth = attr_vals
			enhance_val = 0
			if shipstat[3].nation != Constants.Nation.META:
				if (enhanceslot := attribute_enhance.get(attr)) is not None:
					enhance_val = enhance_data.durability[enhanceslot]
					ship_data['ReinforcementValue'] += str(enhance_data.attr_exp[enhanceslot])+' {{'+attr.wiki_template_name+'}} '
				if research_data:
					try:
						enhance_val += strengthen_data[str(attr).lower()]#Dirty, but works
					except:
						pass
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
	for i in range(1, 4):
		lb_data = ship_data_breakout.load_first(ship_groupid*10+i, DEFAULT_CLIENTS)
		if lb_data:
			ship_data['LB'+str(i)] = lb_data['breakout_view'].replace('/',' / ')
	if ship_data['Type'] == "Destroyer" and shipstat[0].nation != Constants.Nation.UNIVERSAL2:
		DD_buff = shipvals[3].specific_type[0]
		ship_data['LB3'] += ' / '+DD_buffs[DD_buff]

	# EQUIPMENT SLOTS, CHANGES AT LB HALF IMPLEMENTED
	equip_percent_base = shipstat[0]['equipment_proficiency']
	if shipstat[3]:
		equip_percent_max = shipstat[3]['equipment_proficiency']
	for i in range(3):
		ship_data[f'Eq{i+1}EffInit'] = format(equip_percent_base[i], '.0%')
		if shipstat[3]:
			ship_data[f'Eq{i+1}BaseMax'] = shipstat[3]['base_list'][i]
			ship_data[f'Eq{i+1}EffInitMax'] = format(equip_percent_max[i], '.0%')
			if research_data:
				if i+1 in extra_eff.keys(): ship_data[f'Eq{i+1}EffInitMax'] = format(equip_percent_max[i] + extra_eff[i+1], '.0%')

	equip_type = {
		1: shipvals[0]['equip_1'],
		2: shipvals[0]['equip_2'],
		3: shipvals[0]['equip_3']
	}
	for i, shipval in enumerate(shipvals):
		if not shipval: continue
		for j in range(1, 4):
			equip_type_new = shipval['equip_'+str(j)]
			if set(equip_type_new) != set(equip_type[j]):
				print(f'changed equipment @ {i}LB and {j} Slot: from {equip_type[j]} to {equip_type_new}.')
	for i in range(1, 4):
		ship_data['Eq'+str(i)+'Type'] = equip_string(equip_type[i])
		if 4 in shipvals[0]['equip_'+str(i)]:
			ship_data[f'Eq{i}BaseMax'] += shipvals[3]['hide_buff_list'][0]

	# SKILLS (Skills that change at Retrofit/Fatesim not implemented, AoA/Siren Killer half implemented)
	skill_list = shipvals[0]['buff_list_display']
	if shipvals[3]:
		skill_list = shipvals[3]['buff_list_display']
	for i in range(1, len(skill_list)+1):
		skillid = skill_list[i-1]
		skill_data_client = Client.EN
		skill_data_main = skill_data_template.load_client(skillid, skill_data_client)
		for client in [Client.CN, Client.JP]:
			if skill_data := skill_data_template.load_client(skillid, client):
				ship_data['Skill'+str(i)+client.name] = api.replace_namecode(skill_data['name'], client)
				if not skill_data_main:
					skill_data_client = client
					skill_data_main = skill_data

		ship_data['Type'+str(i)] = SKILL_TYPE[skill_data_main['type']]
		ship_data['Skill'+str(i)] = api.replace_namecode(skill_data_main['name'], skill_data_client)
		desc = skill_data_main['desc']
		desc_add = skill_data_main['desc_add']
		for j, desc_add_item in enumerate(desc_add):
			desc = desc.replace('$'+str(j+1), desc_add_item[0][0]+' ('+desc_add_item[skill_data_main['max_level']-1][0]+')')
			desc = desc.replace('.0%','%')
		ship_data['Skill'+str(i)+'Desc'] = api.replace_namecode(desc, skill_data_client)

		buffdata = api.loader.load_buff(skillid, skill_data_client)
		ship_data['Skill'+str(i)+'Icon'] = buffdata.get('icon', skillid)

	# RETROFIT
	retrofit_data = ship_data_trans.load_first(ship_groupid, DEFAULT_CLIENTS)
	if retrofit_data:
		retro_stats = {}
		retro_effs = {}
		retro_ship_id = 0
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
				
				# RETROFIT INTO DIFFERENT SHIP_ID
				if retro_node_data['ship_id']: # (Usually only entered once at most, in case of DDGs thrice)
					retro_ship_id = retro_node_data['ship_id'][0][1]
					retrostat = ship_data_statistics.load_first(f"{retro_ship_id}", clients)
					retrovals = ship_data_template.load_first(f"{retro_ship_id}", clients)
					retro_type = retrostat.type.typename
					if retro_type != ship_data['Type']:
						ship_data['SubtypeRetro'] = retro_type
					attr_dicts = [retrostat.attributes, retrostat.attributes_growth]
					retro_attrs = {k: [d[k] for d in attr_dicts] for k in attr_dicts[0]}
					retro_enhance_id = ship_data_template.load_first(retro_ship_id, clients).strengthen_id
					print(retro_enhance_id)
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
					#Equip slots that change at retrofit not implemented

				ship_data['Index'+letter] = letter
				icon = retro_node_data['icon'].lower()
				if icon[:5] == "mode_": continue
				if icon in retroicon_convert: icon = retroicon_convert[icon]
				ship_data['RetrofitImage'+letter] = icon
				ship_data['ProjName'+letter] = retro_node_data['name']
				ship_data['ProjType'+letter] = retroicon_class[icon]
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
					if attribute_code == 'skill_id':
						attribute += 'Unlock Skill'
						continue
					elif attribute_code in attributes:
						try: retro_stats[attributes[attribute_code][2]] += sum(values)
						except: retro_stats[attributes[attribute_code][2]] = sum(values)
						attribute_name = '{{'+attributes[attribute_code][2]+'}}'
					elif attribute_code in attributes_retro:
						try: retro_effs[attributes_retro[attribute_code]] += sum(map(lambda x: int(str(x)[2:]),values))
						except: retro_effs[attributes_retro[attribute_code]] = sum(map(lambda x: int(str(x)[2:]),values))
						attribute += attributes_retro[attribute_code] + ' '
						valtype = 'Eff'

					firstval = True
					for value in values:
						if firstval: firstval = False
						else: attribute += ' / '

						if valtype == 'Eff': value = str(int(value*100))+'%'
						else: attribute += attribute_name + ' '
						attribute += '+'+str(value)

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
			if retro_ship_id != 0:
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
		# RETROFIT EQUIP
		for i in range(1,4):
			if retro_ship_id != 0:
				try: ship_data[f'Eq{i}EffInitKai'] = f"{int(ship_data[f'Eq{i}EffInitKai'][:-1])+retro_effs[f'Equip {i} Efficiency']}%"
				except: continue
			else:
				try: ship_data[f'Eq{i}EffInitKai'] = f"{int(ship_data[f'Eq{i}EffInitMax'][:-1])+retro_effs[f'Equip {i} Efficiency']}%"
				except: ship_data[f'Eq{i}EffInitKai'] = f"{int(ship_data[f'Eq{i}EffInitMax'][:-1])}%"
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
		raise ValueError(f'Error: "{args.name}" is not a valid/unique ship name.')
	template_data_game = getGameData(groupid, api, clients)
	ship_template = WikiHelper.MultilineTemplate("Ship")
	wikitext = ship_template.fill(template_data_game)
	Utility.output(wikitext)

if __name__ == "__main__":
	main()
