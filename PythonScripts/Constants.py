import os, json

RARITY_LETTER = [ 'E', 'E', 'B', 'P', 'G', 'R' ]
RARITY_NAME_SHIP = [ 'Normal', 'Normal', 'Rare', 'Elite', 'Super Rare', 'Ultra Rare' ]
RARITY_NAME_ITEM = [ 'Normal', 'Normal', 'Rare', 'Elite', 'Super Rare', 'Legendary' ]
RARITY_NAME_RESEARCH = {4: 'Priority', 5: 'Decisive'}

with open(os.path.join('data', 'item_wiki_filenames.json')) as jfile:
	ITEMFILENAMES = json.load(jfile)

ITEMNAME_REPLACE = {
	'Mystery': 'Random',
	'Series ': 'S',
	'General Blueprint -': 'Strengthening Unit',
	'樱之御守': 'Sakura Amulets',
	'荣誉之冠': 'Miniature Crowns'
}

def item_name(name:str) -> str:
	for match in ITEMNAME_REPLACE:
		if match in name: name = name.replace(match, ITEMNAME_REPLACE[match])
	return name

def item_link(name:str) -> str:
	if not name: return ''
	if 'Strengthening Unit' in name: return 'Research'
	if name == 'Cognitive Chips': return 'Dockyard#Cognition_Awaken'
	if name == 'Oxy-cola': return 'Living_Area#Refilling_supplies'
	if name.endswith('Cat Box'): return 'Meowfficer#Cat_Lodge'
	if name.startswith('T') and name.endswith('Tech Pack'): return 'Equipment#Equipment_Boxes'
	if name.startswith('T') and name.endswith('Part'): return 'Equipment#Upgrade_(Enhance)'

def item_filename(name:str) -> str:
	return ITEMFILENAMES.get(name)


NATIONALITY = {
	0: 'Universal',
	1: 'Eagle Union',
	2: 'Royal Navy',
	3: 'Sakura Empire',
	4: 'Ironblood',
	5: 'Eastern Radiance',
	6: 'Sardegna Empire',
	7: 'North Union',
	8: 'Iris Libre',
	9: 'Vichya Dominion',
	98: 'Universal',
	101: 'Neptunia',
	102: 'Bilibili',
	103: 'Utawarerumono',
	104: 'Kizuna AI',
	105: 'Hololive',
}

AMRMOR_TYPE = {
	1: 'Light',
	2: 'Medium',
	3: 'Heavy',
}

SKILL_TYPE = {
	1: 'Offense',
	2: 'Defense',
	3: 'Support',
}
