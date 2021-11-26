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
	'equipment_proficiency_1': 'Slot1 Efficiency',
	'equipment_proficiency_2': 'Slot2 Efficiency',
	'equipment_proficiency_3': 'Slot3 Efficiency',
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
#	11: 'CB Guns', # NOT EXISTING
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

def calculate_stat(base_stat, growth, extra, level, enhance, affinity=1.06):
	return math.floor((base_stat + ((level-1) * growth/1000) + ((level-100) * extra/1000) + enhance) * affinity)

def scrap_values(level, shiptype, api: ALJsonAPI):
	ship_data_by_type = api.get_sharecfgmodule("ship_data_by_type")
	shiptype_data = ship_data_by_type.load_first(shiptype, DEFAULT_CLIENTS)
	coin_ratio = shiptype_data['distory_resource_gold_ratio']
	coins = math.floor((30 + level * coin_ratio) / 10)

	oil_ratio = shiptype_data['distory_resource_oil_ratio']
	oils = math.floor((30 + level * oil_ratio) / 10)
	return coins, oils


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
	ship_data_trans = api.get_sharecfgmodule("ship_data_trans")
	transform_data_template = api.get_sharecfgmodule("transform_data_template")
	ship_data_strengthen = api.get_sharecfgmodule("ship_data_strengthen")
	ship_strengthen_meta = api.get_sharecfgmodule("ship_strengthen_meta")
	ship_data_breakout = api.get_sharecfgmodule("ship_data_breakout")
	skill_data_template = api.get_sharecfgmodule("skill_data_template")
	item_data_statistics = api.get_sharecfgmodule("item_data_statistics")
	ship_data_by_star = api.get_sharecfgmodule("ship_data_by_star")
	ShipConverter = api.ship_converter

	# load first important ship data
	shipstat = [ ship_data_statistics.load_first(f"{ship_groupid}{i}", clients) for i in range(1, 4+1) ]
	shipvals = [ ship_data_template.load_first(f"{ship_groupid}{i}", clients) for i in range(1, 4+1) ]
	research_data = ship_data_blueprint.load_first(ship_groupid, clients)

	ship_wiki_template = dict()
	ship_data = ship_wiki_template# !!!!

	ship_wiki_template['GroupID'] = ship_groupid
	ship_wiki_template['ID'] = OldIDLoader(api).oldid_from_groupid(ship_groupid)
	for client in [Client.CN, Client.JP]:
		if ship0 := ship_data_statistics.load_client(f"{ship_groupid}1", client):
			ship_wiki_template[client.name+'Name'] = api.replace_namecode(ship0.name, client)

	ship_wiki_template['Nationality'] = shipstat[0].nation.label
	ship_wiki_template['Type'] = shipstat[0].type.typename
	ship_wiki_template['Rarity'] = shipstat[0].rarity.label
	base_star = shipstat[0].star

	# BASE STAT CALCULATION
	base_attr_val = shipstat[0].attributes
	ship_wiki_template['Armor'] = shipstat[0].armor.label
	ship_wiki_template['ConsumptionInitial'] = oil_consumption(shipvals[0].oil_at_start, shipvals[0].oil_at_end, 1, api)
	for attr, val in base_attr_val.items():
		if attr in [Constants.Attribute.SPEED, Constants.Attribute.LUCK]:
			ship_wiki_template[attr.wiki_param_name] = math.floor(val)
		else:
			ship_wiki_template[attr.wiki_param_name + "Initial"] = math.floor(val)

	# LVL 100/120 STAT CALCULATION
	if shipstat[3]:
		attr_dicts = [shipstat[3].attributes, shipstat[3].attributes_growth, shipstat[3].attributes_growth_extra]
		lb3_attrs = {k: [d[k] for d in attr_dicts] for k in attr_dicts[0]}
		if shipstat[3].nation == Constants.Nation.META:
			enhance_data = ship_strengthen_meta.load_first(ship_groupid, clients)
		else:
			enhance_data = ship_data_strengthen.load_first(ship_groupid, clients)

		ship_wiki_template['ConsumptionMax'] = oil_consumption(shipvals[3].oil_at_start, shipvals[3].oil_at_end, 100, api)
		ship_wiki_template['Consumption120'] = oil_consumption(shipvals[3].oil_at_start, shipvals[3].oil_at_end, 120, api)
		ship_wiki_template['Consumption125'] = oil_consumption(shipvals[3].oil_at_start, shipvals[3].oil_at_end, 125, api)
		ship_wiki_template['ReinforcementValue'] = ''
		for attr, attr_vals in lb3_attrs.items():
			attr_val, attr_growth, attr_extra = attr_vals
			enhance_val = 0
			if shipstat[3].nation != Constants.Nation.META:
				if (enhanceslot := attribute_enhance.get(attr)) is not None:
					enhance_val = enhance_data.durability[enhanceslot]
					ship_wiki_template['ReinforcementValue'] += str(enhance_data.attr_exp[enhanceslot])+' {{'+attr.wiki_template_name+'}} '
			else:
				raise NotImplementedError("META Enhance stats not included.")

			ship_wiki_template[attr.wiki_param_name+'Max'] = calculate_stat(attr_val, attr_growth, attr_extra, 100, enhance_val)
			ship_wiki_template[attr.wiki_param_name+'120'] = calculate_stat(attr_val, attr_growth, attr_extra, 120, enhance_val)
			ship_wiki_template[attr.wiki_param_name+'125'] = calculate_stat(attr_val, attr_growth, attr_extra, 125, enhance_val)
		ship_wiki_template['ReinforcementValue'] = ship_wiki_template['ReinforcementValue'].strip()

	#### LVL 100 and LVL 120 stats are not fully accurate for Research ships
	if research_data:
		ship_wiki_template['ShipGroup'] = 'Research'
		print('WARNING: level 100/120/125 stats are not accurate!')

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

	# LIMIT BREAK
	for i in range(1, 4):
		lb_data = ship_data_breakout.load_first(ship_groupid*10+i, DEFAULT_CLIENTS)
		if lb_data:
			ship_data['LB'+str(i)] = lb_data['breakout_view']

	# EQUIPMENT SLOTS
	equip_percent_base = shipstat[0]['equipment_proficiency']
	if shipstat[3]:
		equip_percent_max = shipstat[3]['equipment_proficiency']
	for i in range(0, 3):
		ship_data[f'Eq{str(i+1)}EffInit'] = format(equip_percent_base[i], '.0%')
		if shipstat[3]:
			ship_data[f'Eq{str(i+1)}BaseMax'] = shipstat[3]['base_list'][i]
			ship_data[f'Eq{str(i+1)}EffInitMax'] = format(equip_percent_max[i], '.0%')

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
				print(f'changed equipment @ {str(i)}LB and {str(j)} Slot: from {equip_type[j]} to {equip_type_new}.')
	for i in range(1, 4):
		ship_data['Eq'+str(i)+'Type'] = equip_string(equip_type[i])

	# SKILLS
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
		ship_data['Skill'+str(i)+'Desc'] = api.replace_namecode(desc, skill_data_client)

		buffdata = api.loader.load_buff(skillid, skill_data_client)
		ship_data['Skill'+str(i)+'Icon'] = buffdata.get('icon', skillid)

	# RETROFIT
	retrofit_data = ship_data_trans.load_first(ship_groupid, DEFAULT_CLIENTS)
	if retrofit_data:
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
					if attribute_code in attributes:
						attribute += '{{'+attributes[attribute_code][2]+'}}'
					elif attribute_code in attributes_retro:
						attribute += attributes_retro[attribute_code]
						valtype = 'Eff'
					elif attribute_code == 'skill_id':
						attribute += 'Unlock Skill'
						continue

					firstval = True
					for value in values:
						if firstval: firstval = False
						else: attribute += ' /'

						if valtype == 'Eff': value = str(int(value*100))+'%'
						attribute += ' +'+str(value)

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
					if bpnum_str: bpnum_str += 'x / '+str(bpitem[1])
					else: bpnum_str = str(bpitem[1])
				ship_data['BPNum'+letter] = bpnum_str

				platenum_str = ''
				for plateitem in plates:
					plateitem_res = retro_plate[plateitem[0]]
					ship_data['PlateTier'+letter] = plateitem_res[0]
					ship_data['PlateType'+letter] = plateitem_res[1]
					if platenum_str: platenum_str += 'x / '+str(plateitem[1])
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

			for i in range(0, 3):
				if i not in used_heights:
					retromap[i] += '-'

		ship_data['RetrofitMap'] = ''
		for retromappart in retromap:
			ship_data['RetrofitMap'] += '['+retromappart+']'

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
	parser.add_argument("-c", "--clients", required=True, choices=Client.__members__, nargs='+',
						help="clients to gather information from")
	parser.add_argument("-n", "--name", required=True, type=str,
						help="name of the ship to get info from")
	args = parser.parse_args()

	clients = [ Client[c] for c in args.clients ]
	api = ALJsonAPI()

	template_data_game = getGameData(api.ship_converter.get_groupid(args.name), api, clients)
	ship_template = WikiHelper.MultilineTemplate("Ship")
	wikitext = ship_template.fill(template_data_game)
	Utility.output(wikitext)

if __name__ == "__main__":
	main()