import json
from os import PathLike

from .. import ALJsonAPI, Client


def load_wikinames(filepath: PathLike) -> dict[int, str]:
	with open(filepath, "r") as file:
		wikidata = json.load(file)

	for entry in wikidata:
		data = entry["title"]
		shipname = data["ShipName"]
		skinid = data["SkinID"]
		category = data.get("SkinCategory", "")
		yield (shipname, skinid, category)


def update_converter(convert_fp: PathLike, wiki_namecache_fp: PathLike, api: ALJsonAPI):
	"""Updates the cached version of the converter data."""
	ship_skin_template = api.get_sharecfgmodule("ship_skin_template")

	# retrieve converter data
	wikidata = load_wikinames(wiki_namecache_fp)
	conversions = {"painting": dict()}

	for shipskin in ship_skin_template.load_all(Client):
		gameid = equipstat.id
		gamename = equipstat.name
		wikiname = overrides.get(gameid) or ""

		conversions["gameid"][str(gameid)] = {"gamename": gamename, "wikiname": wikiname}
		conversions["gamename"][gamename] = {"gameid": gameid, "wikiname": wikiname}
		conversions["wikiname"][wikiname] = {"gameid": gameid, "gamename": gamename}

	# save data to file
	with open(convert_fp, "w", encoding="utf8") as f:
		json.dump(conversions, f, ensure_ascii=False)
