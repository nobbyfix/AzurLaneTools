from argparse import ArgumentParser
from AzurLane import Client
import WikiHelper, Utility, Constants

template_shop = WikiHelper.MultilineTemplate('EventShop')

def shop(client, eventid:int, pt_filename:str):
	JsonAPI = Utility.defaultJsonAPI()
	activity_template = JsonAPI.load_sharecfg('activity_template', client)
	activity_shop_template = JsonAPI.load_sharecfg('activity_shop_template', client)

	# get shopitem_id's from activity_template
	activity = activity_template[str(eventid)]
	total_pt = 0

	shopitem_wikitexts = ['']
	for shopitem_id in activity['config_data']:
		shopitem = activity_shop_template[str(shopitem_id)]
		award = JsonAPI.load_award(shopitem['commodity_type'], shopitem['commodity_id'])
		
		item_name = Constants.item_name(award.name.strip())
		item_rarity = Constants.RARITY_NAME[award.rarity]
		item_link = Constants.item_link(item_name)
		item_icon = Constants.item_filename(item_name) or award.icon or ''

		if award.data_type == 4:
			item_link = item_name
			item_icon = item_name+'Icon'

		item_amount = shopitem['num_limit']
		item_sub_amount = shopitem['num']
		cost_amount = shopitem['resource_num']
		total_pt += cost_amount * item_amount
		item_template_data = [ item_rarity, item_name, item_link, item_icon, item_amount, cost_amount, pt_filename, item_sub_amount ]
		shopitem_wikitexts.append(WikiHelper.simple_template('EventShopItem', item_template_data))

	eventshop_template_data = {
		'TotalPt': total_pt,
		'PtImage': pt_filename,
		'Items': '\n'.join(shopitem_wikitexts)
	}

	return template_shop.fill(eventshop_template_data)

def main():
	parser = ArgumentParser()
	parser.add_argument('shopid', metavar='INDEX', type=int, nargs=1, help='an index from sharecfg/activity_template that links to sharecfg/activity_shop_template')
	parser.add_argument('-c', '--client', required=True, help='client to gather information from')
	parser.add_argument('-pt', '--pointfile', default='', type=str, help='filename of the point icon on the wiki')
	parser.add_argument('-f', '--file', metavar='FILENAME', default='shop', type=str, help='file to save to, default is "shop"')
	args = parser.parse_args()
	
	client = Client[args.client]
	result = shop(client, args.shopid[0], args.pointfile)
	Utility.output(args.file, result)

if __name__ == "__main__":
	Utility.output('shop', shop(Client.EN, 30432, 'IrisPt'))