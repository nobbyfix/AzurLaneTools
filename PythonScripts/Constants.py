import os, json

RARITY_LETTER = [ 'E', 'E', 'B', 'P', 'G', 'R' ]
RARITY_NAME = [ 'Normal', 'Normal', 'Rare', 'Elite', 'Super Rare', 'Ultra Rare' ]
RARITY_NAME_RESEARCH = {4: 'Priority', 5: 'Decisive'}

with open(os.path.join('data', 'item_wiki_filenames.json')) as jfile:
	ITEMFILENAMES = json.load(jfile)

ITEMNAME_REPLACE = {
		'Mystery': 'Random',
		'Series ': 'S',
		'General Blueprint -': 'Strengthening Unit'
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