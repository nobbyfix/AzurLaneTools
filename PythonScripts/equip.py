import re
from argparse import ArgumentParser
from difflib import get_close_matches
from collections.abc import Iterable

from lib import ALJsonAPI, Client, WikiHelper, Utility
from lib.Constants import Nation, ShipType

from ship import get_skilldesc

	
attributes = {
	'durability':	['Health',	'Health'],
	'cannon':		['FP',		'Firepower'],
	'torpedo':		['Torp',	'Torpedo'],
	'antiaircraft':	['AA',		'AA'],
	'air':			['Av',		'Aviation'],
	'reload':		['Reload',	'Reload'],
	'hit':			['Acc',		'Acc'],
	'dodge':		['Evasion',	'Evasion'],
	'speed':		['Spd',		'Spd'],
	'luck':			['Luck',	'Luck'],
	'antisub':		['ASW',		'ASW'],
	'oxy_max':		['Oxygen',	'Oxygen']
}


equipment_types = {
	1:	['DD Gun',['cannon','antiaircraft'], 'gun'],
	2:	['CL Gun',['cannon','antiaircraft'], 'gun'],
	3:	['CA Gun',['cannon','antiaircraft'], 'gun'],
	4:	['BB Gun',['cannon','antiaircraft'], 'gun'],
	5:	['Torpedo',['torpedo'], 'torpedo'],
	6:	['AA Gun',['cannon','antiaircraft','hit'], 'aa gun'],
	7:	['Fighter',['air'], 'plane'],
	8:	['Torpedo Bomber',['air'], 'plane'],
	9:	['Dive Bomber',['air'], 'plane'],
	10:	['Auxiliary',[], 'aux'],
	11:	['CB Gun',['cannon','antiaircraft'], 'gun'], 
	12:	['Seaplane',['air'], 'plane'],
	13:	['Submarine Torpedo',['torpedo'], 'torpedo'],
	14:	['Depth Charge',['antisub'], 'depth charge'],
	15:	['ASW Bomber',['antisub'], 'plane'], #Also has damage and damagemax and Coef and CoefMax tho
	17:	['ASW Helicopter',['antisub'], 'aux'], 
	18:	['Cargo',[], 'aux'],
	20:	['Missile',['torpedo'], 'torpedo'],
	21:	['VT Gun',['cannon','antiaircraft','hit'],'aa gun'],
	99:	['Airstrike stuff']
}

usability_default = {
	1: [22,23,24], #DD Gun
	2: [22,23,24], #CL Gun
	3: [8,17,22,23,24], #CA Gun
	4: [22,23,24], #BB Gun
	5: [22,23,24], #Torpedo
	6: [22,23,24], #AA Gun
	7: [22,23,24], #Fighter
	8: [10,22,23,24], #TB
	9: [10,22,23,24], #DB
	10: [], #Aux
	11: [3,22,23,24], #CB Gun
	12: [22,23,24], #Seaplane
	13: [22,23,24], #Sub Torp
	14: [3,4,5,6,7,8,9,10,11,12,13,17,18,19,22,23,24], #Depth Charge
	15: [1,2,3,4,7,8,9,10,11,12,13,17,18,19,20,21,22,23,24], #ASW Bomber
	17: [1,3,4,5,6,7,8,9,10,11,12,13,17,18,19,20,21,22,23,24], #Heli
	18: [1,2,3,4,5,6,7,8,9,10,11,12,13,17,18,20,21,22,23,24], #Cargo
	20: [1,2,3,4,5,6,7,8,9,10,11,12,13,17,18,19,22,23,24], #Missile
	21: [1,2,3,6,7,8,9,11,12,13,17,18,19,20,21,22,23,24], #VT Gun (Time Fuze)
}

usability_wikitext_default = {
	1: {
		1: [1],
		2: [2, "Atlanta-class, Dido-class, Ceres-class, Isuzu and Emden (secondary); Optional. Harbin, Emden (primary), Pamiat Merkuria (retrofitted) and Hai Tien (secondary); Required."],
		3: [2, "Secondary gun"],
		18: [2, "Secondary gun, Azuma & Brest only"],
		5: [2, "Secondary gun"],
		4: [2, "Secondary gun, excluding Odin and Scharnhorst META"],
		13: [2, "Secondary gun"],
		19: [1, "Excluding Ting An"],
		8: [1, "Excluding Surcouf"]
	},
	2: {
		1: [2, "Type 1936A-class only"],
		2: [1, "Excluding Hai Chi-class"],
		3: [2, "Tallinn, Suzuya and Kumano only"],
		18: [2, "Secondary gun, Kronshtadt & Kala Ideas only"],
		5: [2, "Secondary gun, cannot be used on Eagle Union's BBs"],
		4: [2, "Secondary gun, cannot be used on Royal Navy's BCs, Dunkerque, Odin or Scharnhorst META"],
		7: [2, "Zeppy, Béarn and Eagle only"],
		6: [2, "Houshou only"],
		8: [2, "Nautilus only"]
	},
	3: {
		2: [2, "Hai Chi-class only"],
		3: [1],
		18: [1]
	},
	11: {
		18: [1]
	},
	6: {
		1: [1],
		2: [1, "Excluding Emden and Hai Tien"],
		3: [1],
		18: [1],
		5: [1],
		4: [1],
		13: [1],
		10: [1],
		6: [1],
		12: [1],
		19: [1, "Excluding Ting An"]
	},
	4: {
		5: [1],
		4: [1],
		13: [1],
		10: [1]
	},
	5: {
		1: [1],
		2: [1, "Excluding Ceres-class"],
		3: [1],
		18: [2, "Ägir only"],
		4: [2, "Odin and Scharnhorst META only"]
	},
	13: {
		8: [1],
		17: [1]
	},
	12: {
		10: [1, "Excluding Kearsarge"],
		6: [2, "Chen Hai and Hwah Jah only"],
		17: [1],
		19: [2, "Ting An only"]
	},
	7: {
		10: [2, "Kearsarge only"],
		7: [1],
		6: [1, "Chen Hai and Hwah Jah excluded"]
	},
	8: {
		7: [1],
		6: [1, "Chen Hai and Hwah Jah excluded"]
	},
	9: {
		1: [2, "Shirakami Fubuki only"],
		7: [1],
		6: [1, "Chen Hai and Hwah Jah excluded"]
	},
	18: {
		19: [1]
	},
	14: {
		1: [1],
		2: [1]
	},
	15: {
		5: [2, "Warspite (Retrofit) only"],
		6: [1, "Chen Hai and Hwah Jah excluded"]
	},
	20: {
		1: [2, "DDG only"]
	},
	21: {
		4: [1],
		5: [1],
		10: [1],
	},
	10: {
		1: [1],
		2: [1],
		3: [1],
		4: [1],
		5: [1],
		6: [1],
		7: [1],
		8: [1],
		10: [1],
		12: [1],
		13: [1],
		17: [1],
		18: [1],
		19: [1],
		20: [1],
		21: [1],
		22: [1],
		23: [1],
		24: [1],
	}
}

wiki_ammo = {
	'DD Gun': {
		1: {
			(100,50,20,18): 'Normal',
			(100,55,25,18): 'Normal*',
			(100,55,25,19): 'Normal^',
			(100,60,20,18): 'Normal+',
			(100,60,20,20): 'Normal++',
		},
		2: {
			(90,70,40,22): 'AP'
		},
		3: {
			(120,60,60,15): 'HE'
		},
		7: {
			(95,95,25,22): 'SAP'
		}
	},
	'CL Gun': {
		1: {
			(100,75,40,18): 'Normal'
		},
		2: {
			(100,80,60,22): 'AP',
			(100,100,60,22): 'AP*',
			(110,90,70,22): 'AP+',
			(115,85,65,22): 'APK',
			(100,95,55,22): 'APC28'
		},
		3: {
			(145,105,70,15): 'HE',
			(145,110,75,15): 'HE+',
			(150,105,70,15): 'HEK'
		},
		
	},
	'CA Gun': {
		1: {
			(100,90,50,18): 'Normal',
			(115,110,90,20): 'NormalPR',
			(115,115,95,20): 'NormalDR',
		},
		2: {
			(75,110,75,22): 'AP',
			(75,110,85,22): 'AP+'
		},
		3: {
			(135,95,70,16): 'HE',
			(135,95,70,18): 'HE*'
		},
		7: {
			(65,125,65,22): 'SAP'
		}
	},
	'BB Gun': {
		1: {
			(70,100,90,12): 'Normal'
		},
		2: {
			(45,130,110,12): 'AP',
			(45,130,115,12): 'APMKD',
			(40,135,115,12): 'AP*',
			(40,140,115,14): 'AP4',
			(40,140,120,13): 'AP^',
			(55,145,125,12): 'AP+',
		},
		3: {
			(140,110,90,10): 'HE'
		},
		7: {
			(100,150,50,12): 'SAP'
		}
	},
	'CB Gun': {
		2: {
			(75,110,75,14): 'AP',
			(75,115,75,14): 'AP*',
			(70,115,80,16): 'APB',
			(55,110,90,16): 'APM'
		},
		3: {
			(135,100,75,12): 'HE'
		}
	},
	'Torpedo': {
		4: {
			(80,100,130,3): 'Normal',
			(80,100,130,3.5): 'Normal (Royal Navy)',
			(80,100,130,4): 'Normal (Sakura Empire)',
			(80,100,130,2): 'Acoustic Homing',
		}
	},
	'Submarine Torpedo': {
		4: {
			(80,100,130,3): 'Normal',
			(80,100,130,2): 'Acoustic',
			(70,100,120,2): 'Normal*',
			(70,100,120,3): 'NormalS',
		}
	}
}

conv = 1/(60*(2*3.14)**0.5)

def convert_reload(x):
	return f"{x*conv:.2f}"

def skill_desc_enhance(api,desc):
	for i in Nation:
		if i not in (Nation.KIZUNA_AI,): desc = desc.replace(str(i),f"[[{i}]]",1)
	for i in api.ship_converter.ship_to_id.keys():
		if i not in ('Eagle','Vanguard'): desc = re.sub(r'\b'+i+r'\b','[['+i+']]',desc,1)
	desc = re.sub('armor break', 'Armor Break',desc,flags=re.I).replace('burn','Burn').replace('flood','Flood')
	desc = re.sub('Armor Break','[[Combat#Armor_breaking/shattering|Armour Break]]',desc,1)
	desc = re.sub('Burn','[[Combat#Fire_Damage|Burn]]',desc,1)
	desc = re.sub('F(lood(?:ing)?)',r'[[Combat#Flood_Damage|F\1]]',desc,1)
	return desc

def getGameData(equip, api: ALJsonAPI, clients: Iterable[Client]):
	weapon_prop = api.get_sharecfgmodule("weapon_property")
	barrage_temp = api.get_sharecfgmodule("barrage_template")
	bullet_temp = api.get_sharecfgmodule("bullet_template")
	plane_temp = api.get_sharecfgmodule("aircraft_template")
	equip_data_statistics = api.get_sharecfgmodule("equip_data_statistics")
	equip_data_template = api.get_sharecfgmodule("equip_data_template")
	equip_upgrade_data = api.get_sharecfgmodule("equip_upgrade_data")
	skill_world_display = api.get_sharecfgmodule("skill_world_display")
	skill_data_template = api.get_sharecfgmodule("skill_data_template")

	equip_data = {}
	if type(equip) != int:
		equip_id = equip.id
		if not equip.wikiname: equip.wikiname = equip.gamename
		equip_data['Name'] = equip.wikiname
		equip_data['Image'] = equip.icon
		if equip.gamename != equip.wikiname:
			equip_data["AltNames"] = 1
			equip_data["ENName"] = equip.gamename
	else:
		equip_id = equip
	equip_data['BaseID'] = equip_id
	
	for client in [Client.CN, Client.JP]:
		if equip0 := equip_data_statistics.load_client(f"{equip_id}", client):
			equip_data[client.name+'Name'] = api.replace_namecode(equip0.name, client)
	
	equip_stats = equip_data_statistics.load_first(equip_id, clients)
	if not equip_stats:
		raise KeyError(f"Equipment ID not found: {equip_id}")
	equip_type = equipment_types.get(equip_stats.type,['Unknown type',[]])
	equip_data['Type'] = equip_type[0]
	equip_data['Nationality'] = equip_stats.nation.label
	equip_data['Stars'] = equip_stats.get('rarity')
	equip_data['Tech'] = f"T{equip_stats.tech}"

	
	#INITIALISE DATA FOR MAX / OPS MAX EQUIPS (This breaks if there is no ordinary max equip lvl, but that should never happen anyway)
	for i in [3,6,10]:
		if stats := equip_data_statistics.load_first(equip_id+i,clients):
			if stats.base.id == equip_id:
				max_lvl = i
				equip_max = stats
	equip_ops = []
	if equip_stats.tech in {0,3}:
		for i in [7,11,13]:
			if stats := equip_data_statistics.load_first(equip_id+i,clients):
				if stats.base.id == equip_id:
					ops_lvl = i
					equip_ops = stats
	if equip_ops:
		try: equip_data['OpSiren'] = equip_ops.anti_siren // 100
		except: pass
	
	for i in equip_type[1]:
		equip_data[attributes[i][1]] = 0
	shipstats = {}
	for i in range(1,4):
		if attr := equip_stats.get(f"attribute_{i}"):
			if attr not in shipstats:
				shipstats[attr] = {}
			val = int(equip_stats[f"value_{i}"])
			shipstats[attr]['base'] = val
		if attr := equip_max.get(f"attribute_{i}",attr):
			if attr not in shipstats:
				shipstats[attr] = {}
			val = int(equip_max.get(f"value_{i}",val))
			shipstats[attr]['max'] = val
		if equip_ops and (attr := equip_ops.get(f"attribute_{i}",attr)):
			if attr not in shipstats:
				shipstats[attr] = {}
			val = int(equip_ops.get(f"value_{i}",val))
			shipstats[attr]['ops'] = val
	for attr, value in shipstats.items():
		if 'base' not in value:
			value['base'] = 0
		if 'max' not in value:
			value['max'] = value['base']
		if 'ops' not in value:
			value['ops'] = value['max']
		try:
			equip_data[attributes[attr][1]] = value['base']
			if not (value['base'] == value['max'] == value['ops']):
				equip_data[attributes[attr][0] + 'Max'] = value['max']
				if equip_ops:
					equip_data[attributes[attr][0] + 'OPS'] = value['ops']
		except KeyError: print(f"Unknown attr: {attr} {value['base']}->{value['max']}->{value['ops']}")

	if equip_type[2] == 'plane':
		plane_id = equip_stats.weapon_id[0]
		plane_base = plane_temp.load_first(plane_id,clients)
		if stats := plane_temp.load_first(plane_id+max_lvl,clients):
			if stats.base == plane_id:
				plane_max = stats
		plane_ops = {}
		if equip_ops:
			if stats := plane_temp.load_first(plane_id+ops_lvl,clients):
				if stats.base == plane_id:
					plane_ops = stats
		weap_base = weapon_prop.load_first(plane_id,clients)
		if stats := weapon_prop.load_first(plane_id+max_lvl,clients):
			if stats.base == plane_id:
				weap_max = stats
		equip_data['RoF'] = convert_reload(weap_base.reload_max)
		equip_data['RoFMax'] = convert_reload(weap_max.reload_max)
		equip_data['PlaneHP'] = plane_base.max_hp
		equip_data['PlaneHPMax'] = plane_max.max_hp
		if equip_ops:
			equip_data['PlaneHPOPS'] = plane_ops.max_hp
		equip_data['PlaneSpeed'] = plane_base.speed
		equip_data['CrashDamage'] = plane_base.crash_DMG
		equip_data['DodgeLimit'] = plane_base.dodge_limit
		equip_data['PlaneDodge'] = f"{plane_base.dodge:.3f}"
		equip_data['Weapons'] = str(plane_base.weapon_ID)[1:-1]
		if len(equip_stats.weapon_id) > 1:
			int_id = equip_stats.weapon_id[1]
			int_base = weapon_prop.load_first(int_id,clients)
			if stats := weapon_prop.load_first(int_id+max_lvl,clients):
				if stats.base == int_id:
					int_max = stats
			intercept = convert_reload(int_base.reload_max)
			interceptmax = convert_reload(int_max.reload_max)
			equip_data['Int'] = intercept
			equip_data['IntMax'] = interceptmax

	elif equip_type[2] == 'aa gun':
		weap_id = equip_stats.weapon_id[0]
		weap_base = weapon_prop.load_first(weap_id,clients)
		if stats := weapon_prop.load_first(weap_id+max_lvl,clients):
			if stats.base == weap_id:
				weap_max = stats
		weap_ops = {}
		if equip_ops:
			if stats := weapon_prop.load_first(weap_id+ops_lvl,clients):
				if stats.base == weap_id:
					weap_ops = stats
		barr_list_base = weap_base.barrage_ID
		bull_list_base = weap_base.bullet_ID
		if len(barr_list_base) != 1:
			raise ValueError(f'Expected barrage list of length 1, got {barr_list_base}')
		if len(barr_list_base) != len(bull_list_base):
			raise ValueError(f'Length of bullet list({bull_list_base}) != barrage list ({barr_list_base})')
		if barr_list_max := weap_max.get("barrage_ID"):
			pass
		if bull_list_max := weap_max.get("bullet_ID"):
			pass
		if barr_list_ops := weap_ops.get("barrage_ID"):
			pass
		if bull_list_ops := weap_max.get("bullet_ID"):
			pass
		barr_id = barr_list_base[0]
		bull_id = bull_list_base[0]
		barr = barrage_temp.load_first(barr_id,clients)
		bull = bullet_temp.load_first(bull_id,clients)
		
		equip_data['Damage'] = weap_base.damage
		equip_data['DamageMax'] = weap_max.damage
		equip_data['RoF'] = convert_reload(weap_base.reload_max)
		equip_data['RoFMax'] = convert_reload(weap_max.reload_max)
		equip_data['Angle'] = weap_base.angle
		if weap_base.get('min_range'): equip_data['WepRangeMin'] = weap_base.min_range
		equip_data['WepRange'] = weap_base.range
		if equip_type[0] == 'VT Gun':
			equip_data['AoE'] = bull.hit_type['range']
		equip_data['Coef'] = weap_base.corrected
		if equip_ops:
			try: equip_data['CoefMax'] = weap_ops.corrected
			except AttributeError:
				print(f"Warning: No increased Coef for OpS Level.")
		equip_data['Ammo'] = 'Normal'
	
	
	elif len(equip_stats.weapon_id) == 1:
		weap_id = equip_stats.weapon_id[0]
		weap_base = weapon_prop.load_first(weap_id,clients)
		if not weap_base:
			print("Error: This equip's weapon cannot be found:", weap_id)
			return
		if stats := weapon_prop.load_first(weap_id+max_lvl,clients):
			if stats.base != weap_id:
				print('Warning: Different base ID')
				diffbase = weapon_prop.load_first(stats.base,clients)
				if diffbase.barrage_ID != weap_base.barrage_ID or diffbase.bullet_ID != weap_base.bullet_ID:
					print('Warning, different barrage or bullet IDs')
			weap_max = stats
		weap_ops = {}
		if equip_ops:
			if stats := weapon_prop.load_first(weap_id+ops_lvl,clients):
				if stats.base != weap_id:
					print('Warning: Different base ID')
					diffbase = weapon_prop.load_first(stats.base,clients)
					if diffbase.barrage_ID != weap_base.barrage_ID or diffbase.bullet_ID != weap_base.bullet_ID:
						print('Warning, different barrage or bullet IDs')
				weap_ops = stats
		barr_list_base = weap_base.barrage_ID
		bull_list_base = weap_base.bullet_ID
		if len(barr_list_base) != len(bull_list_base):
			raise ValueError(f'Length of bullet list({bull_list_base}) != barrage list ({barr_list_base})')
		n=0
		salvo_multiplier = 1
		if len(barr_list_base) != 1:
			bullets = []
			for n,i in enumerate(bull_list_base):
				bull = bullet_temp.load_first(i,clients)
				if not bull.extra_param or bull.extra_param.get('diveFilter') != [1,2]:
					bullets.append(n)
			if len(bullets) != 1:
				if all(bull_list_base[bullets[0]]==bull_list_base[n] for n in bullets):
					salvo_multiplier = len(bullets)
					print(f'Warning: Expected barrage list of length 1, got {barr_list_base}. Assuming all barrages are the same and adjusting salvo count. Highly imprecise.')
				else:
					raise ValueError(f'Expected barrage list of length 1, got {barr_list_base}')
			n = bullets[0]
			
		if barr_list_max := weap_max.get("barrage_ID"):
			pass
		if bull_list_max := weap_max.get("bullet_ID"):
			pass
		if barr_list_ops := weap_ops.get("barrage_ID"):
			pass
		if bull_list_ops := weap_max.get("bullet_ID"):
			pass
		barr_id = barr_list_base[n]
		bull_id = bull_list_base[n]
		barr = barrage_temp.load_first(barr_id,clients)
		bull = bullet_temp.load_first(bull_id,clients)
		
		equip_data['Damage'] = weap_base.damage
		equip_data['DamageMax'] = weap_max.damage
		if  bull.random_damage_rate:
			equip_data['Damage'] *=  bull.random_damage_rate/2 + 1
			if int(equip_data['Damage']) == equip_data['Damage']: equip_data['Damage'] = int(equip_data['Damage'])
			equip_data['DamageMax'] *=  bull.random_damage_rate/2 + 1
			if int(equip_data['DamageMax']) == equip_data['DamageMax']: equip_data['DamageMax'] = int(equip_data['DamageMax'])
		equip_data['RoF'] = convert_reload(weap_base.reload_max)
		equip_data['RoFMax'] = convert_reload(weap_max.reload_max)
		if equip_type[2] == 'depth charge':
			equip_data['Type'] = 'Depth Charge'
		else:
			equip_data['Angle'] = weap_base.angle
		if weap_base.get('min_range'): equip_data['WepRangeMin'] = weap_base.min_range
		equip_data['WepRange'] = weap_base.range
		if bull.type not in (2,16):
			if bull.range_offset:
				equip_data['ProjRange'] = f"{bull.range - bull.range_offset}-{bull.range+bull.range_offset}"
			else:
				equip_data['ProjRange'] = bull.range
		equip_data['ProjSpeed'] = bull.velocity
		if bull.extra_param and ((vo := bull.extra_param.get('velocity_offset')) or (vo := bull.extra_param.get('velocity_offsetF'))):
			equip_data['ProjSpeed'] = f"{bull.velocity-vo}-{bull.velocity+vo}"
		if 'gravity' in bull.extra_param and bull.extra_param['gravity']:#weap_base.type == 23 or equip_type[2] == 'depth charge':
			if (spreadX := bull.extra_param.get('randomOffsetX',0)) != (spreadZ := bull.extra_param.get('randomOffsetZ',0)):
				print(f"Warning! Uneven spread: {spreadX} x {spreadZ}")
			equip_data['Spread'] = spreadX
			if bull.hit_type: equip_data['AoE'] = bull.hit_type['range']
		elif barr.random_angle:
			equip_data['FiringSpread'] = abs(barr.angle)
			equip_data['PatternSpread'] = 0
		else:
			equip_data['FiringSpread'] = 0
			equip_data['PatternSpread'] = abs(barr.delta_angle * barr.primal_repeat)
		equip_data['Coef'] = weap_base.corrected
		if equip_ops:
			try: equip_data['CoefMax'] = weap_ops.corrected
			except AttributeError:
				print(f"Warning: No increased Coef for OpS Level.")
		if equip_type[2] != 'depth charge':
			equip_data['ArmorModL'], equip_data['ArmorModM'], equip_data['ArmorModH'] = (mods:=[round(100*i) for i in bull.damage_type])
			ammo = wiki_ammo.get(equip_type[0]).get(bull.ammo_type)
		if equip_type[2] == 'torpedo':
			equip_data['Number'] = (barr.primal_repeat+1)*salvo_multiplier
			equip_data['Ammo'] = ammo.get((*mods,bull.velocity),list(ammo.values())[0])
			if bull.acceleration:
				if type(bull.acceleration) == list:
					equip_data['Characteristic'] = 'Oxygen'
					equip_data['Ammo'] = 'Oxygen'
				elif (acc := bull.acceleration.get('tracker')):
					equip_data['Characteristic'] = 'Acoustic Homing'
				else:
					print('Unknown accel:', bull.acceleration)
			else:
				equip_data['Characteristic'] = 'Normal'
		else:
			equip_data['Shells'] = barr.primal_repeat+1
			equip_data['Salvoes'] = (barr.senior_repeat+1)*salvo_multiplier
			equip_data['VolleyTime'] = f"{(barr.senior_repeat)*barr.senior_delay:.2f}"
			if equip_type[2] != 'depth charge':
				equip_data['Ammo'] = ammo.get((*mods,bull.velocity),list(ammo.values())[0])
				if weap_base.aim_type == 1:
					equip_data['Characteristic'] = 'Lock-On'
				elif weap_base.aim_type == 0:
					equip_data['Characteristic'] = 'Scattershot'
				if 'gravity' in bull.extra_param and bull.extra_param['gravity']:#weap_base.type == 23:
					equip_data['Characteristic'] = 'Bracketing'
		
	else:
		if equip_type[2] not in {'aux'} and equip_type[0] != 'Missile':
			raise ValueError(f"Expected 1 weapon, got {len(equip_stats.weapon_id)}: {equip_stats.weapon_id}")
	
	#USABILITY
	forbidden = equip_data_template.load_first(equip_id,clients).ship_type_forbidden
	if forbidden != (forbidden_default := usability_default[equip_stats.type]):
		if not set(forbidden_default) < set(forbidden):
			equip_data["UseOverride"] = 1
			print(f"Warning: [{set(forbidden_default) - set(forbidden)}] allowed. Setting all to 1")
			for i in set(forbidden_default) - set(forbidden) - {20,21}:
				equip_data[ShipType.from_id(i).templatename] = 1
			if equip_type[0] == 'CB Gun':
				equip_data['CA'] = 2
				equip_data['CANote'] = 'Deutschland-class and P-class Only'
		if set(forbidden) & (uw := usability_wikitext_default.get(equip_stats.type,{}).copy()).keys() - {20,21}:
			equip_data["UseOverride"] = 1
			for i in forbidden:
				uw.pop(i,None)
		if 'UseOverride' in equip_data:
			for i,j in uw.items():
				ship_type = ShipType.from_id(i).templatename
				equip_data[ship_type] = j[0]
				if len(j) > 1:
					equip_data[ship_type+'Note'] = j[1]
		else:
			print(set(forbidden_default), set(forbidden), set(uw.keys()), set(forbidden) & uw.keys())




	#GEAR LAB
	upgrades = equip_upgrade_data.load_all(clients)
	LabFrom = []
	LabTo = []
	for i in upgrades:
		if i.target_id == equip_id:
			source_id = i.upgrade_from
			source_stats = equip_data_statistics.load_first(source_id, clients)
			rarity = source_stats.get('rarity')
			tech = f"Type {source_stats.tech}"
			conv = api.equip_converter.from_equipid(source_id)
			text = '{{'+f"EquipmentBox|{rarity}|{conv.wikiname}|{conv.wikiname}{(f'#{tech}-0' if tech != 'Type 0' else '')}|{conv.icon}}}}} [[{conv.wikiname}{(f'#{tech}-0|{conv.wikiname}' if tech != 'Type 0' else '')}]]"
			LabFrom.append(text)
		if i.upgrade_from == equip_id:
			target_id = i.target_id
			target_stats = equip_data_statistics.load_first(target_id, clients)
			rarity = target_stats.get('rarity')
			tech = f"Type {target_stats.tech}"
			conv = api.equip_converter.from_equipid(target_id)
			text = '{{'+f"EquipmentBox|{rarity}|{conv.wikiname}|{conv.wikiname}{(f'#{tech}-0' if tech != 'Type 0' else '')}|{conv.icon}}}}} [[{conv.wikiname}{(f'#{tech}-0|{conv.wikiname}' if tech != 'Type 0' else '')}]]"
			LabTo.append(text)
	if LabFrom: equip_data['LabFrom'] = '<br>'.join(LabFrom)
	if LabTo: equip_data['LabTo'] = '<br>'.join(LabTo)

	if equip_type[2] == 'aux' and 'range' in equip_stats.equip_parameters:
		equip_data['Type'] = 'Sonar'
		equip_data['WepRange'] = equip_stats.equip_parameters['range']
	
	#SKILLS
	notes = []
	for i in equip_stats.equip_parameters:
		pass
	ops_skills = skill_world_display.all_ids(clients)
	if equip_stats.hidden_skill_id:
		print('Hidden skills:', equip_stats.hidden_skill_id)
	for skillid in equip_stats.skill_id:
		skill_data_client = Client.EN
		skill_data_main = skill_data_template.load_client(skillid, skill_data_client)
					
		desc = get_skilldesc(skill_data_main,skill_data_main.max_level)
		if skillid in ops_skills:
			skill_data_ops = skill_world_display.load_first(skillid,clients)
			desc_ops = get_skilldesc(skill_data_ops,skill_data_main.max_level)
			desc +='\n' + desc_ops
		desc = skill_desc_enhance(api,desc)
		notes.append(skill_data_main.name + ': ' + desc)
	equip_data['Notes'] = '\n'.join(notes)
	return equip_data

def main():
	parser = ArgumentParser()
	parser.add_argument("-c", "--clients", choices=Client.__members__, default = ['EN'], nargs = '+',
						help="clients to gather information from (default: EN)")
	parser.add_argument("-n", "--name", required=True, type=str,
						help="name of the equip to get info for")
	args = parser.parse_args()

	clients = [ Client[c] for c in args.clients ]
	api = ALJsonAPI()
	equip = api.equip_converter.from_wikiname(args.name)
	if not equip:
		equip = api.equip_converter.from_gamename(args.name)
	if not equip:
		if args.name.isdigit():
			equip_id = int(args.name)
			equip = api.equip_converter.from_equipid(equip_id)
			if not equip:
				print("Warning: ID not found in wiki data, attempting to get data from json!")
				equip = equip_id
		else:
			if m := get_close_matches(args.name, set(api.equip_converter.gamename_to_data.keys()) | set(api.equip_converter.wikiname_to_data.keys()), 1):
				print(f'"{args.name}" is not a valid Equip name, assuming you meant "{m[0]}"!')
				equip = api.equip_converter.from_wikiname(m[0])
				if not equip:
					equip = api.equip_converter.from_gamename(m[0])
				if not equip:
					raise Exception('Equip cannot be found! (Something major must be wrong with the Equipment Converter)')
			else:
				e = f'"{args.name}" is not a valid Equip name.'
				raise ValueError(e)
	equips = sorted((i for i in api.equip_converter.id_to_data.values() if equip.gamename == i.gamename and equip.wikiname == i.wikiname and equip.icon == i.icon), key = lambda x: x.id)
	if len(equips) > 1:
		wikitext = "<tabber>"
	else:
		wikitext = ''
	for n,equip in enumerate(equips):
		template_data_game = getGameData(equip, api, clients)
		if not template_data_game:
			print('No game data returned for this equip', equip)
			continue
		if wikitext:
			wikitext += f"Type {template_data_game['Tech'][-1]}=\n"
		equip_template = WikiHelper.MultilineTemplate("Equipment")
		wikitext += equip_template.fill(template_data_game)
		if n+1<len(equips):
			wikitext += "\n|-|"
	if len(equips) > 1:
		wikitext += '\n</tabber>'
	Utility.output(wikitext)
	#print(equip.id)

if __name__ == "__main__":
	main()
