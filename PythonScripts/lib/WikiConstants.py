import json

from . import Constants


# convert item names to wiki filenames
itemname_convertpath = Constants.ITEMNAME_OVERRIDES_PATH
with open(itemname_convertpath, 'r') as file:
	ITEMFILENAMES = json.load(file)

#TODO: rewrite to primarily use icon name instead of item name
# enables to easier derive certain icons without knowing the award type
def item_filename(name: str) -> str:
	return ITEMFILENAMES.get(name)


# replaces certain phrases in item names for wiki purposes
ITEMNAME_REPLACE = {
	'Mystery': 'Random',
	'Series ': 'S',
	'General Blueprint -': 'Strengthening Unit',
}

def item_name(name: str) -> str:
	for match in ITEMNAME_REPLACE:
		if match in name: name = name.replace(match, ITEMNAME_REPLACE[match])
	return name


# return page links for certain items
def item_link(name: str) -> str:
	if not name: return ''
	if 'Strengthening Unit' in name: return 'Research'
	if name in ['Cognitive Chips', 'Cognitive Array']: return 'Dockyard#Cognitive_Awakening'
	if name == 'Oxy-cola': return 'Living_Area#Refilling_supplies'
	if name.endswith('Cat Box'): return 'Meowfficer#Cat_Lodge'
	if name.startswith('T'):
		if name.endswith('Tech Pack'): return 'Equipment#Equipment_Boxes'
		if name.endswith('Part'): return 'Equipment#Upgrade_(Enhance)'


# return filled templates that will display the icon of the item
def item_template(name: str) -> str:
	raise NotImplementedError()
