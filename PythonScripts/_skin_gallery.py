from collections import Counter
from itertools import chain
from time import sleep
import mwparserfromhell
import Utility, WikiHelper

JsonAPI = Utility.defaultJsonAPI()
ship_skin_template = JsonAPI.load_multi_sharecfg('ship_skin_template', JsonAPI.ALL_CLIENTS)
shop_template = JsonAPI.load_multi_sharecfg('shop_template', JsonAPI.ALL_CLIENTS)
ship_converter = JsonAPI.converter
site = WikiHelper.load_mwclient_site()
t_shipskin = WikiHelper.MultilineTemplate('ShipSkin')
t_shipskin0 = WikiHelper.MultilineTemplate('ShipSkin0')

# get all skinids from all versions
skinids = dict()
for client_data in ship_skin_template.values():
	for groupid, shipskinids in client_data['get_id_list_by_ship_group'].items():
		if groupid in skinids:
			skinids[groupid].update(shipskinids)
		else:
			skinids[groupid] = set(shipskinids)

def game_single_skin(fullid:int) -> dict:
	"""Returns a dict containing ONLY the important information of a single skin.
	The keys are named after parameters complying with Template:ShipSkin for easy convertability.

	:param fullid: A skinid from sharecfg/ship_skin_template
	"""
	skin_ret = dict()
	
	# additional objects to check if all clients actutally have the same values
	background_counter = dict()
	sp_background_counter = dict()
	live2d_counter = dict()
	cost_counter = dict()

	for client in ship_skin_template: # iterate through all available clients
		gameskindata = ship_skin_template[client].get(str(fullid))
		if not gameskindata: continue # continue with next client if this one does not have the skin

		live2d_counter[client.name] = '1' if 1 in gameskindata['tag'] else None

		# the following values are always not set for retrofit and default skins
		if fullid % 10 in {0, 9}: continue

		skin_ret['SkinName'+client.name] = JsonAPI.replace_namecode(gameskindata['name'], client).strip()
		background_counter[client.name] = gameskindata['bg']
		sp_background_counter[client.name] = gameskindata['bg_sp']
		
		# get shop data
		if (shopid := gameskindata['shop_id']) != 0:
			shopitem = shop_template[client].get(str(shopid))
			if shopitem != None:
				cost_counter[client.name] = shopitem['resource_num']
				if not shopitem['time'] == 'always':
					skin_ret['Limited'+client.name] = '1'
			else:
				# if the skin has an invalid shopid, its very likely an error and that skin actually does not exist in that client
				skin_ret.pop('SkinName'+client.name)

	# check if all clients have the same info, if not use most common one
	# background has empty string as its empty value
	if background_counter:
		counted_bg = Counter(background_counter.values()).most_common()
		if len(counted_bg) > 1: print(f'{fullid} has differing backgrounds: {background_counter}')
		if (background := counted_bg[0][0]) != '': skin_ret['Background'] = background

	# special background has empty string as its empty value
	if sp_background_counter:
		counted_spbg = Counter(sp_background_counter.values()).most_common()
		if len(counted_spbg) > 1: print(f'{fullid} has differing special backgrounds: {sp_background_counter}')
		if (spbg := counted_spbg[0][0]) != '': skin_ret['SpecialBackground'] = spbg

	# live2d has empty string as its empty value
	if live2d_counter:
		counted_live2d = Counter(live2d_counter.values()).most_common()
		if len(counted_live2d) > 1: print(f'{fullid} has differing live2d info: {live2d_counter}')
		if (live2d := counted_live2d[0][0]) != None: skin_ret['Live2D'] = live2d

	# cost has 0 as its empty value
	if cost_counter:
		counted_cost = Counter(cost_counter.values()).most_common()
		if len(counted_cost) > 1: print(f'{fullid} has differing shop cost: {cost_counter}')
		if (cost := counted_cost[0][0]) != 0: skin_ret['Cost'] = cost
	return skin_ret

def game_skins(groupid:int) -> dict:
	"""Returns a dict containing ONLY the important information of all skins of a given ship.
	The keys are named after parameters complying with Template:ShipSkin for easy convertability.

	:param groupid: the groupid identifying the ship
	"""
	additional_skincount = 0
	skins = dict()
	for fullid in skinids[str(groupid)]:
		if groupid == fullid//10:
			skinnum = fullid%10
		else: # skinid is higher than 9 and has different groupid
			skinnum = 10+additional_skincount
			additional_skincount += 1

		skindata = game_single_skin(fullid)
		skindata['SkinID'] = skinnum
		skins[skinnum] = skindata
	return skins

def wiki_skins(shipname:str, gallerypage=None) -> dict:
	"""Returns a dict containing all the parameters of all skins from a gallery page of a given ship
	and the additional art on the page.

	:param shipname: name of the ship
	:param gallerypage: if the gallerypage if alraedy loaded, it can be passed over
	"""
	if gallerypage == None: gallerypage = site.pages[shipname+'/Gallery']
	if not gallerypage.exists: return

	skins = dict()
	mwparser = mwparserfromhell.parse(gallerypage.text())
	templates = mwparser.filter_templates()
	for template in templates:
		if not 'ShipSkin' in template.name: continue
		parsed_template = WikiHelper.parse_multiline_template(str(template))
		skinid_num = int(parsed_template.get('SkinID'))
		skins[skinid_num] = parsed_template
	
	# search for additional art
	additional_art = '' 
	found_addart = False
	for node in mwparser.nodes:
		if 'additional art' in str(node.lower()): found_addart = True
		if found_addart: additional_art += str(node)
	return skins, additional_art


def update_gallery_page(shipname:str, save_to_file:bool=False, default_skincategory:str='') -> bool:
	"""Updates the gallery page of a given ship.

	:param shipname: the name of a ship used on the wiki
	:param save_to_file: outputs into a file in the /output directory instead of updating the wikipage
	:param default_skincategory: the default skincategory if new skins are found in the game files
	:return: true if update was successful, otherwise false
	"""
	groupid = ship_converter.get_groupid(shipname)
	if not groupid: raise ValueError(f'Shipname {shipname} does not lead to a valid groupid.')

	# retrieve skins from wiki and game
	gallerypage = site.pages[shipname+'/Gallery']
	skins_game = game_skins(groupid)
	skins_wiki, additionalArt = wiki_skins(shipname, gallerypage)

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
		Utility.output('skin_gallery', wikitext)
		sleep(3.5)
	else:
		# update gallerypage on the wiki
		summary = 'Added missing skins/updated changed information' if gallerypage.exists else 'Created gallery page'
		gallerypage.save(wikitext, summary=summary)
		sleep(5)
	return True

def main():
	mode = input('Execute (all/test/single/list): ')
	if mode == 'test':
		while(1):
			shipname = input('Shipname: ')
			success = update_gallery_page(shipname, True)
			if not success: print('An error occured.')
	elif mode == 'single':
		shipname = input('Shipname: ')
		defcat = input('Default Category: ')
		print(f'Updating {shipname}...')
		success = update_gallery_page(shipname, default_skincategory=defcat)
		if not success: print('An error occured.')
	elif mode == 'list':
		amount = input('Amount to update: ')
		updates = [(input('Shipname: '), input('Default Category: ')) for _ in range(int(amount))]
		for shipname, defcat in updates:
			print(f'Updating {shipname}...')
			success = update_gallery_page(shipname, default_skincategory=defcat)
			if not success: print('An error occured.')
	elif mode == 'all':
		print('Do you really want to update all gallery pages?')
		confirm = input('Type "y" to confirm: ')
		if not confirm == 'y': return
		print('All gallery pages will be update now.')
		shipnames = ship_converter.get_shipnames()
		for shipname in shipnames:
			print(f'Updating {shipname}...')
			success = update_gallery_page(shipnames, False)
			if success: print(f'{shipname} successfully updated.')
			else: print(f'An error occured while updating {shipname}.')

if __name__ == "__main__":
	main()