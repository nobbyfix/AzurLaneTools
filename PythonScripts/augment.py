from argparse import ArgumentParser
from difflib import get_close_matches
from collections.abc import Iterable

from lib import ALJsonAPI, Client, WikiHelper, Utility
from lib.Constants import ShipType as ship_types


attributes = {
	'durability':		['Health',		'HealthMax',	'HealthOPS'],
	'cannon':		['Firepower',		'FPMax',	'FPOPS'],
	'torpedo':		['Torpedo',		'TorpMax',	'TorpOPS'],
	'antiaircraft':		['AA',			'AAMax',	'AAOPS'],
	'air':			['Aviation',		'AvMax',	'AvOPS'],
	'reload':		['Reload',		'ReloadMax',	'ReloadOPS'],
	'hit':			['Acc',			'AccMax',	'AccOPS'],
	'dodge':		['Evasion',		'EvasionMax',	'EvasionOPS'],
	'speed':		['Spd',			'SpdMax',	'SpdOPS'],
	'luck':			['Luck',		'LuckMax',	'LuckOPS'],
	'antisub':		['ASW',			'ASWMax',	'ASWOPS'],
	'oxygen':		['Oxygen',		'OxygenMax',	'OxygenOPS']
}



def getGameData(augment, api: ALJsonAPI, clients: Iterable[Client]):
	augment_data_statistics = api.get_sharecfgmodule("spweapon_data_statistics")
	augment_data = {}
	if type(augment) != int:
		augment_id = augment.id
		augment_data['Name'] = augment.wikiname
		augment_data['Image'] = augment.icon
	else:
		augment_stats = augment_data_statistics.load_first(augment, clients)
		augment_id = augment
		augment_data['Name'] = augment_stats.name
		augment_data['Image'] = "Augment " + augment_stats.icon
	augment_data['BaseID'] = augment_id
	
	for client in [Client.CN, Client.JP]:
		if augment0 := augment_data_statistics.load_client(f"{augment_id}", client):
			augment_data[client.name+'Name'] = api.replace_namecode(augment0.name, client)
	
	augment_stats = augment_data_statistics.load_first(augment_id, clients)
	augment_stats_up = augment_data_statistics.load_first(augment_id+10, clients)
	if not augment_stats:
		raise KeyError(f"Augment ID not found: {augment_id}")
	augment_data['Type'] = "Augment Module"
	augment_data['Stars'] = augment_stats.get('rarity') + 1
	augment_data['Nationality'] = 'Universal'
	augment_data['Tech'] = f"T{augment_stats.tech}"


	i = 1
	while stat := augment_stats.get(f"attribute_{i}"):
		augment_data[attributes[stat][0]] = f"{augment_stats.get(f'value_{i}')} + {augment_stats.get(f'value_{i}_random')}"
		if augment_stats_up.get(f'value_{i}'):
			augment_data[attributes[stat][1]] = f"{augment_stats_up.get(f'value_{i}')} + {augment_stats.get(f'value_{i}_random')}"
		i += 1


	if not (usability := augment_stats.usability):
		aug_type_data = api.get_sharecfgmodule('spweapon_type')
		aug_type = aug_type_data.load_first(augment_stats.type,clients)
		#usability = [1,2,3,4,5,6,7,8,10,12,13,17,18,19,22]
		usability = aug_type.ship_type
	for i in usability:
		ship_type = ship_types.from_id(i)
		if unique_ship := augment_stats.get('unique'):
			augment_data[ship_type.templatename] = 2
			augment_data[ship_type.templatename + 'Note'] = api.ship_converter.get_shipname(unique_ship) + ' only'
		else:
			augment_data[ship_type.templatename] = 1

	augment_data['DropLocation'] = '[[Augmentation]]'



	
	skill_data_template = api.get_sharecfgmodule("skill_data_template")
	skill_desc_template = api.get_sharecfgmodule("skill_world_display")


	skill_id = augment_stats.effect_id
	skill_data = skill_data_template.load_first(skill_id, clients)
	skill_desc = skill_desc_template.load_first(skill_id, clients)
	name = skill_data.name

	desc_list = []
	for j in [skill_data,skill_desc]:
		if j:
			desc = j['desc']
			desc_add = j['desc_add']
			for k, desc_add_item in enumerate(desc_add):
				desc = desc.replace('$'+str(k+1), desc_add_item[0][0]+' ('+desc_add_item[skill_data['max_level']-1][0]+')')
			desc_list.append(desc.replace('.0%','%'))
	effect = "'''{}''': {}{}".format(name,desc_list[0] if desc_list else "","<br>[Operation Siren only] "+desc_list[1] if len(desc_list)>1 else "")

	augment_data['Notes'] = effect


	if augment_stats.get('skill_upgrade'):
		skill_up = augment_stats_up.skill_upgrade[0]
		old_skill_data = skill_data_template.load_first(skill_up[0], clients)
		new_skill_data = skill_data_template.load_first(skill_up[1], clients)
		new_skill_desc = skill_desc_template.load_first(skill_up[1], clients)
		old_name = old_skill_data.name
		new_name = new_skill_data.name

		desc_list = []
		for j in [new_skill_data,new_skill_desc]:
			if j:
				desc = j['desc']
				desc_add = j['desc_add']
				for k, desc_add_item in enumerate(desc_add):
					desc = desc.replace('$'+str(k+1), desc_add_item[0][0]+' ('+desc_add_item[new_skill_data['max_level']-1][0]+')')
				desc_list.append(desc.replace('.0%','%'))
		effect = "<br><br>''Replaces {} at +10 with {}''<br>{}{}".format(old_name,new_name,desc_list[0] if desc_list else "","<br>[Operation Siren only] "+desc_list[1] if len(desc_list)>1 else "")

		augment_data['Notes'] += effect


	return augment_data






def main():
	parser = ArgumentParser()
	parser.add_argument("-c", "--clients", choices=Client.__members__, default = ['EN'], nargs = '+',
						help="clients to gather information from (default: EN)")
	group = parser.add_mutually_exclusive_group()
	group.add_argument("-n", "--name", action="store_true",help="interprets arg as name/id of the Augment to get info for")
	group.add_argument("-s", "--ship", action="store_true",help="interprets arg as name/id of a ship")
	parser.add_argument("arg",help="argument to get info for")
	args = parser.parse_args()

	clients = [ Client[c] for c in args.clients ]
	api = ALJsonAPI()
	if args.name:
		augment = api.augment_converter.from_wikiname(args.arg)
		if not augment:
			if args.arg.isdigit():
				augment_id = int(args.arg)
				augment = api.augment_converter.from_augmentid(augment_id)
				if not augment:
					print("Warning: ID not found in wiki data, attempting to get data from json!")
					augment = augment_id
			else:
				if m := get_close_matches(args.arg, api.augment_converter.wikiname_to_data.keys(), 1):
					print(f'"{args.arg}" is not a valid Augment name, assuming you meant "{m[0]}"!')
					augment = api.augment_converter.from_wikiname(m[0])
					if not augment:
						raise Exception('Augment cannot be found! (Something major must be wrong with the Augment Converter)')
				else:
					e = f'"{args.arg}" is not a valid Augment name.'
					raise ValueError(e)
	elif args.ship:
		if type(args.arg) != str:
			try:
				groupid = int(args.arg)
			except:
				raise TypeError(f'Expected string or int, got {type(args.arg)} at {args.arg}')
		else: groupid = api.ship_converter.get_groupid(args.arg)
		if not groupid:
			if args.arg.isdigit():
				groupid = int(args.arg)
			else:
				if m := get_close_matches(args.arg, api.ship_converter.ship_to_id.keys(), 1):
					e = f'"{args.arg}" is not a valid ship name, did you mean {m[0]}?'
				else:
					e = f'"{args.arg}" is not a valid ship name.'
				raise ValueError(e)
		augment = api.augment_converter.from_shipid(groupid)
		if not augment: print(f"Ship {args.arg} has no unique augment")
	template_data_game = getGameData(augment, api, clients)
	equip_template = WikiHelper.MultilineTemplate("Equipment")
	wikitext = equip_template.fill(template_data_game)
	Utility.output(wikitext)
	#print(equip.id)

if __name__ == "__main__":
	main()
