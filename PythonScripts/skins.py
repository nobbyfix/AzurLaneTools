from collections import Counter
from itertools import chain
from pathlib import Path
from time import sleep
from typing import Any, Callable, Optional

import mwparserfromhell

from lib import ALJsonAPI, Client, WikiHelper, Constants, Utility, DEFAULT_CLIENTS
from lib.converter import ships


api = ALJsonAPI()
ship_skin_template = api.get_sharecfgmodule("ship_skin_template")
shop_template = api.get_sharecfgmodule("shop_template")
ship_converter = ships.load_converter(Constants.SHIPID_CONVERT_CACHE_PATH)

wikiclient = WikiHelper.WikiClient().login()
t_shipskin = WikiHelper.MultilineTemplate('ShipSkin')
t_shipskin0 = WikiHelper.MultilineTemplate('ShipSkin0')


# get all skinids from all versions
skinids = dict()
for client in Client:
	for groupid, shipskinids in ship_skin_template._load("get_id_list_by_ship_group", client).items():
		if groupid in skinids:
			skinids[groupid].update(shipskinids)
		else:
			skinids[groupid] = set(shipskinids)


def eval_counter(count_values: dict, val_check: Callable, error_msg: str) -> Optional[Any]:
	if count_values:
		mc = Counter(count_values.values()).most_common()
		if len(mc) > 1:
			print(error_msg.format(count_values))

		val = mc[0][0]
		if val_check(val):
			return val


def game_single_skin(fullid: int) -> dict:
	"""
	Returns a dict containing ONLY the important information of a single skin.
	The keys are named after parameters complying with Template:ShipSkin for easy convertability.

	:param fullid: A skinid from sharecfg/ship_skin_template
	"""
	skin_ret = dict()
	
	# additional objects to check if all clients actutally have the same values
	background_counter = dict()
	sp_background_counter = dict()
	live2d_counter = dict()
	cost_counter = dict()

	for client in DEFAULT_CLIENTS:
		gameskindata = ship_skin_template.load_client(fullid, client)
		if not gameskindata: continue # continue with next client if this one does not have the skin

		skin_ret['SkinID'] = gameskindata['group_index']

		live2d_counter[client.name] = '1' if 1 in gameskindata['tag'] else None

		# the following values are always not set for retrofit and default skins
		if fullid % 10 in {0, 9}: continue

		skin_ret['SkinName'+client.name] = api.replace_namecode(gameskindata['name'], client)
		background_counter[client.name] = gameskindata['bg']
		sp_background_counter[client.name] = gameskindata['bg_sp']
		
		# get shop data
		shopid = gameskindata['shop_id']
		if shopid != 0:
			shopitem = shop_template.load_client(shopid, client)
			if shopitem is not None:
				cost_counter[client.name] = shopitem['resource_num']
				if not shopitem['time'] == 'always':
					skin_ret['Limited'+client.name] = '1'
			else:
				# if the skin has an invalid shopid, its very likely an error and that skin actually does not exist in that client
				skin_ret.pop('SkinName'+client.name)

	# check if all clients have the same info, if not use most common one
	# background has empty string as its empty value
	if bg := eval_counter(background_counter, (lambda v: v != ''), f'{fullid} has differing backgrounds: %s'):
		skin_ret['Background'] = bg

	# special background has empty string as its empty value
	if spbg := eval_counter(sp_background_counter, (lambda v: v != ''), f'{fullid} has differing special backgrounds: %s'):
		skin_ret['SpecialBackground'] = spbg

	# live2d has empty string as its empty value
	if live2d := eval_counter(live2d_counter, (lambda v: v is not None), f'{fullid} has differing live2d info: %s'):
		skin_ret['Live2D'] = live2d

	# cost has 0 as its empty value
	if cost := eval_counter(cost_counter, (lambda v: v != 0), f'{fullid} has differing shop cost: %s'):
		skin_ret['Live2D'] = cost

def game_skins(groupid: int) -> dict:
	"""
	Returns a dict containing ONLY the important information of all skins of a given ship.
	The keys are named after parameters complying with Template:ShipSkin for easy convertability.

	:param groupid: the groupid identifying the ship
	"""
	skins = dict()
	for fullid in skinids[str(groupid)]:
		skindata = game_single_skin(fullid)
		skins[skindata['SkinID']] = skindata
	return skins

def wiki_skins(shipname: str, gallerypage = None) -> dict:
	"""
	Returns a dict containing all the parameters of all skins from a gallery page of a given ship
	and the additional art on the page.

	:param shipname: name of the ship
	:param gallerypage: if the gallerypage is already loaded, it can be passed over
	"""
	if gallerypage is None: gallerypage = wikiclient.execute(wikiclient.mwclient.pages.get, shipname+'/Gallery')
	if not gallerypage.exists: return

	skins = dict()
	mwparser = mwparserfromhell.parse(gallerypage.text())
	templates = mwparser.filter_templates()
	for template in templates:
		if not 'ShipSkin' in template.name: continue
		parsed_template = WikiHelper.parse_multiline_template(str(template))
		skinid_num = int(parsed_template.get('SkinID'))
		skins[skinid_num] = parsed_template
	
	# search for additional art/artwork
	additional_art = '' 
	found_addart = False
	for node in mwparser.nodes:
		nodename = str(node.lower())
		if 'additional art' in nodename or 'artwork' in nodename:
			found_addart = True
		if found_addart:
			additional_art += str(node)
	return skins, additional_art


def update_gallery_page(shipname: str, save_to_file: bool = False, default_skincategory: str = '') -> bool:
	"""Updates the gallery page of a given ship.

	:param shipname: the name of a ship used on the wiki
	:param save_to_file: outputs into a file in the /output directory instead of updating the wikipage
	:param default_skincategory: the default skincategory if new skins are found in the game files
	:return: true if update was successful, otherwise false
	"""
	groupid = ship_converter.get_groupid(shipname)
	if not groupid: raise ValueError(f'Shipname {shipname} does not lead to a valid groupid.')

	# retrieve skins from wiki and game
	gallerypage = wikiclient.execute(wikiclient.mwclient.pages.get, shipname+'/Gallery')
	skins_game = game_skins(groupid)
	skins_wiki, additionalArt = wiki_skins(shipname, gallerypage) or ({}, '')

	# merge game and wiki skin information with game overwriting wiki
	skins = dict()
	for skinid in set(skins_game.keys()) | set(skins_wiki.keys()):
		skin = skins_wiki.get(skinid, {})
		skin.update(skins_game.get(skinid, {}))
		skins[skinid] = skin

	# generate wikitext
	wikitext = '{{ShipTabber}}\n{{#tag:tabber|'
	for skinid in chain([0,-1,9,8], range(1, 7+1), range(10,max(skins)+1)):
		if skinid not in skins: continue
		skin = skins[skinid]

		# use default skincategory if skin has none or the value for it is already set empty
		if 'SkinCategory' not in skin or skin['SkinCategory'] == '':
			skin['SkinCategory'] = default_skincategory
		# only retrofit skin need a static skin category set
		if skinid == 9: skin['SkinCategory'] = 'Kai'

		# append filled template to result wikitext (used template depends on skinid)
		if skinid == 0: wikitext += '\n'+t_shipskin0.fill(skin)
		else: wikitext += '\n'+t_shipskin.fill(skin)
	
	wikitext += '\n}}' # close tabber
	if additionalArt: wikitext += f'\n{additionalArt}' # also add additional art at the end

	if save_to_file:
		#save wikitext to file
		Utility.output(wikitext, Path("outout", "skins", shipname + ".wikitext"))
		sleep(1)
	else:
		# update gallerypage on the wiki
		summary = 'Added missing skins/updated changed information' if gallerypage.exists else 'Created gallery page'
		gallerypage.save(wikitext, summary=summary)
		sleep(2)
	return True


def main():
	_MANUAL_OVERRIDES = {
		"fuxu": ("Foch", ""),
		"fuxu_2": ("Foch", "Casual"),
		"ougen_5": ("Prinz Eugen", "RaceQueen"),
		"qiye_7": ("Enterprise", "RaceQueen"),
	}

	ships = {}
	for name, cat in _MANUAL_OVERRIDES.values():
		if not name in ships or cat:
			ships[name] = cat

	for shipname, defcat in ships.items():
		print(f'Updating {shipname}...')
		success = update_gallery_page(shipname, default_skincategory=defcat, save_to_file=True)
		if not success: print('An error occured.')

if __name__ == "__main__":
	main()