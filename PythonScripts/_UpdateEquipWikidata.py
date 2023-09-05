import json

from lib import Constants
from lib.WikiHelper import WikiClient


def request_equips(wikiclient: WikiClient, offset=0):
	result = wikiclient.execute(wikiclient.mwclient.api,
		action="cargoquery",
		format="json",
		limit=500,
		tables="equipment",
		fields="equipment.Name,equipment.Image",
		where="equipment.Type != 'Augment Module'",
		offset=offset)
	return result['cargoquery']

def download_equip_data():
	wikiclient = WikiClient().login()
	all_entires = []
	offset = 0
	while True:
		entries = request_equips(wikiclient, offset)
		all_entires += entries
		if len(entries) == 500:
			offset += 500
		else:
			return all_entires


def main():
	cache_fp = Constants.EQUIP_WIKIDATA_PATH
	equipdata = download_equip_data()
	with open(cache_fp, "w", encoding="utf8") as file:
		json.dump(equipdata, file)

if __name__ == "__main__":
	main()
