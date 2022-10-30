import json

from lib import Constants
from lib.WikiHelper import WikiClient


def request_skins(wikiclient: WikiClient, offset=0):
	result = wikiclient.execute(wikiclient.mwclient.api,
		action="cargoquery",
		format="json",
		limit=500,
		tables="ship_skins",
		fields="ship_skins.ShipName,ship_skins.SkinID,ship_skins.SkinCategory",
		order_by='"cargo__ship_skins"."ShipName","cargo__ship_skins"."SkinID"',
		offset=offset)
	return result['cargoquery']

def download_skin_data():
	wikiclient = WikiClient().login()
	all_entires = []
	offset = 0
	while True:
		entries = request_skins(wikiclient, offset)
		all_entires += entries
		if len(entries) == 500:
			offset += 500
		else:
			return all_entires


def main():
	cache_fp = Constants.SKIN_WIKIDATA_PATH
	equipdata = download_skin_data()
	with open(cache_fp, "w", encoding="utf8") as file:
		json.dump(equipdata, file)

if __name__ == "__main__":
	main()
