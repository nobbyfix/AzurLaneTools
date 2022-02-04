from collections import Counter
from argparse import ArgumentParser
from typing import Iterable

from lib import ALJsonAPI, Client, WikiHelper, Utility
from lib.apiclasses import Furniture


FURNITURE_TYPE = {
	1: "Wallpaper", # TYPE_WALLPAPER
	2: "Furniture", # TYPE_FURNITURE
	3: "Decoration", # TYPE_DECORATE
	4: "Floor", # TYPE_FLOORPAPER
	5: "Floor Item", # TYPE_MAT
	6: "Wall Decoration", # TYPE_WALL
	7: "Special", # TYPE_COLLECTION
	8: "Stage", # TYPE_STAGE
	9: "Arch", # TYPE_ARCH
	10: "Special", # TYPE_WALL_MAT
	11: "Moving Object", # TYPE_MOVEABLE
	12: "Transport", # TYPE_TRANSPORT
	13: "Special" # TYPE_RANDOM_CONTROLLER
}

INTERACTION = {
	"sit": "sit",
	"wash": "bath",
	"sleep": "sleep",
	"dance": "dance",
	"stand2": "stand",
	"victory": "stand",
	"yun": "stand",
	"attack": "stand",
}

NUM_TEXT = ["One", "Two", "Three", "Four", "Five", "Six", "Seven"]
def convert_shipgirl_amount(num: int) -> str:
	text = NUM_TEXT[num-1] + " shipgirl"
	if num > 1: text += "s"
	return text


def furniture_item_template(furn: Furniture):		
		# optional shop data that needs to be checked if the field is there
		price_coin = furn.dorm_icon_price if "dorm_icon_price" in furn else ""
		price_gem = furn.gem_price if "dorm_icon_price" in furn else ""

		if size := furn.size or "":
			size = f"{size[0]}x{size[1]}"

		interaction = ""
		if "interAction" in furn:
			interaction_counter = Counter()
			for action_data in furn.interAction:
				interaction_counter[action_data[0]] += 1
			
			interaction = []
			for actionname, amount in interaction_counter.most_common():
				interaction.append(f"{convert_shipgirl_amount(amount)} can {INTERACTION[actionname]} here.")
			interaction = "<br>".join(interaction)

		params = [furn.name, furn.icon, furn.describe, furn.rarity.label, FURNITURE_TYPE[furn.type], price_coin, price_gem,
					furn.comfortable or "", size, furn.count, interaction]
		return WikiHelper.simple_template("FurnitureRow", params)

class FurnitureQuery:
	api: ALJsonAPI

	def __init__(self, api: ALJsonAPI) -> None:
		self.api = api

	def get_theme(self, themeid: int, clients: Iterable[Client]):
		# determine client list, because all api calls use load_first
		backyard_theme_template = self.api.get_sharecfgmodule("backyard_theme_template")
		theme = backyard_theme_template.load_first(themeid, clients)
		if not theme:
			raise ValueError(f"There is no theme with id {themeid}.")

		wikitext = [
			f"== {theme.name} ==",
			f"*'''Description:''' ''{theme.desc}''",
			WikiHelper.simple_template("FurnitureTableHeader", [f"FurnIcon_{theme.icon}.png"]),
		]

		# add all furniture directly referenced from the set
		theme_items = {}
		for furniture_ref in theme.furniture:
			furnitem = furniture_ref.load_first(self.api, clients)
			theme_items[furnitem] = None

		# search for more furniture items that are not directly referenced
		# these are usually gem-only items
		furniture_module = self.api.get_apimodule("furniture")
		for furnitem in furniture_module.load_all(clients):
			if furnitem.themeId == theme.id:
				theme_items[furnitem] = None

		# convert all items to wikitext
		for furnitem in theme_items:
			wikitext.append(furniture_item_template(furnitem))

		wikitext.append("|}")
		return "\n".join(wikitext)

	def get_themeid_from_name(self, name: str, clients: Iterable[Client]) -> int:
		backyard_theme_template = self.api.get_sharecfgmodule("backyard_theme_template")
		for theme in backyard_theme_template.load_all(clients):
			if theme.name == name:
				return theme.id


def main():
	parser = ArgumentParser()
	parser.add_argument("-i", "--id", type=int,
						help="an index from sharecfg/backyard_theme_template")
	parser.add_argument("-n", "--name", type=str,
						help="a theme name from sharecfg/backyard_theme_template")
	parser.add_argument("-c", "--client", nargs='*', choices=Client.__members__,
						help="client to gather information from")
	args = parser.parse_args()

	clients = Client
	if args.client:
		clients = [Client[c] for c in args.client]
	
	jsonapi = ALJsonAPI()
	fquery = FurnitureQuery(jsonapi)
	if themename := args.name:
		themeid = fquery.get_themeid_from_name(themename, clients)
	else:
		themeid = args.id

	print(themeid)

	result = fquery.get_theme(themeid, clients)
	Utility.output(result)

if __name__ == "__main__":
	main()