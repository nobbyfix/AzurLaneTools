from argparse import ArgumentParser

from lib import ALJsonAPI, Client, Utility
from lib.WikiHelper import MultilineTemplate, Wikifier, simple_template


template_shop = MultilineTemplate("EventShop")

def shop(api: ALJsonAPI, wikifier: Wikifier, client: Client, eventid: int, pt_filename: str) -> str:
	activity_template = api.get_sharecfgmodule("activity_template")
	activity_shop_template = api.get_sharecfgmodule("activity_shop_template")

	# get shopitem_id's from activity_template
	activity = activity_template.load_client(eventid, client)
	total_pt = 0

	shopitem_wikitexts = [""]
	for shopitemid in activity["config_data"]:
		shopitem = activity_shop_template.load_client(shopitemid, client)
		award = shopitem.load(api, client)
		wikiaward = wikifier.wikify_awardable(award)
		rarity = wikiaward.rarity.label
		name = wikiaward.name
		link = wikiaward.link
		filelink = wikiaward.filelink

		total_pt += shopitem.resource_num * shopitem.num_limit
		item_template_data = [ rarity, name, link, filelink, shopitem.num_limit, shopitem.resource_num, pt_filename, shopitem.amount ]
		shopitem_wikitexts.append(simple_template('EventShopItem', item_template_data))

	eventshop_template_data = {
		'TotalPt': total_pt,
		'PtImage': pt_filename,
		'Items': '\n'.join(shopitem_wikitexts)
	}
	return template_shop.fill(eventshop_template_data)

def main():
	parser = ArgumentParser()
	parser.add_argument("shopid", metavar="INDEX", type=int, nargs=1,
						help="an index from sharecfg/activity_template that links to sharecfg/activity_shop_template")
	parser.add_argument("-c", "--client", required=True, choices=Client.__members__,
						help="client to gather information from")
	parser.add_argument("-pt", "--pointfile", default="Pt.png", type=str,
						help="filename of the point icon on the wiki")
	args = parser.parse_args()

	api = ALJsonAPI()
	result = shop(api, Wikifier(api), Client[args.client], args.shopid[0], args.pointfile)
	Utility.output(result)

if __name__ == "__main__":
	main()
