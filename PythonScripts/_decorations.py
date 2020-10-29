from collections import Counter
from argparse import ArgumentParser
from AzurLane import Client
import WikiHelper, Utility, Constants

FURNTYPE = {
	1: 'Wallpaper', # TYPE_WALLPAPER
	2: 'Furniture', # TYPE_FURNITURE
	3: 'Decoration', # TYPE_DECORATE
	4: 'Floor', # TYPE_FLOORPAPER
	5: 'Floor Item', # TYPE_MAT
	6: 'Wall Decoration', # TYPE_WALL
	7: 'Special', # TYPE_COLLECTION
	8: 'Stage', # TYPE_STAGE
	9: 'Arch', # TYPE_ARCH
	10: 'Special', # TYPE_WALL_MAT
	11: 'Moving Object', # TYPE_MOVEABLE
	12: 'Transport', # TYPE_TRANSPORT
	13: 'Special' # TYPE_RANDOM_CONTROLLER
}

INTERACTION = {
	'sit': 'sit',
	'wash': 'bath',
	'sleep': 'sleep',
	'dance': 'dance',
	'stand2': 'stand',
	'victory': 'stand',
	'yun': 'stand'
}

NUM_TEXT = ['One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven']
def shipgirl_amount(num:int) -> str:
	text = NUM_TEXT[num-1] + ' shipgirl'
	if num > 1: text += 's'
	return text

def decotheme(client, themeid):
	JsonAPI = Utility.defaultJsonAPI()
	backyard_theme_template = JsonAPI.load_sharecfg('backyard_theme_template', client)
	furniture_data_template = JsonAPI.load_sharecfg('furniture_data_template', client)
	furniture_shop_template = JsonAPI.load_sharecfg('furniture_shop_template', client)

	theme = backyard_theme_template.get(str(themeid))
	if not theme:
		raise ValueError(f'Client {client.name} has no theme with id {themeid}.')

	theme_name = theme['name'].strip()
	theme_desc = theme['desc'].strip()
	theme_icon = theme['icon'].strip()
	
	# add as wikitext
	wikitext = f'== {theme_name} ==\n'
	wikitext += f"*'''Description:''' ''{theme_desc}''\n"
	wikitext += WikiHelper.simple_template('FurnitureTableHeader', [f'FurnIcon_{theme_icon}.png'])+'\n'

	furniture_rows = []
	for furnid in furniture_data_template['all']:
		furniture = furniture_data_template.get(str(furnid))
		if (not furniture) or (furniture['themeId'] != themeid): continue

		name = furniture['name'].strip()
		desc = furniture['describe'].strip()
		icon = furniture['icon'].strip()
		rarity = Constants.RARITY_NAME_ITEM[furniture['rarity']]
		furntype = FURNTYPE[furniture['type']]
		comf = furniture['comfortable']
		
		size = furniture['size'] or ''
		if size: size = str(size[0])+'x'+str(size[1])
		
		count = furniture['count']

		interaction = furniture.get('interAction') or ''
		if interaction:
			interaction_counter = Counter()
			for action_data in interaction:
				interaction_counter[action_data[0]] += 1
			interaction = []
			for actionname, amount in interaction_counter.most_common():
				interaction.append(f'{shipgirl_amount(amount)} can {INTERACTION[actionname]} here.')
			interaction = '<br>'.join(interaction)

		price_coin = ''
		price_gem = ''
		furniture_shop = furniture_shop_template.get(str(furnid))
		if furniture_shop:
			price_coin = furniture_shop['dorm_icon_price']
			price_gem = furniture_shop['gem_price']

		params = [name, icon, desc, rarity, furntype, price_coin, price_gem, comf, size, count, interaction]
		furniture_rows.append(WikiHelper.simple_template('FurnitureRow', params))

	return wikitext + '\n'.join(furniture_rows) + '\n|}'

def main():
	parser = ArgumentParser()
	parser.add_argument('themeid', metavar='INDEX', type=int, nargs=1, help='an index from sharecfg/backyard_theme_template')
	parser.add_argument('-c', '--client', required=True, help='client to gather information from')
	parser.add_argument('-f', '--file', metavar='FILENAME', default='decorations', type=str, help='file to save to, default is "decorations"')
	args = parser.parse_args()
	
	client = Client[args.client]
	result = decotheme(client, args.themeid[0])
	Utility.output('decorations', result)

if __name__ == "__main__":
	main()