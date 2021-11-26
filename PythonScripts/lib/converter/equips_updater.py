import json
import html
from os import PathLike

from .. import ALJsonAPI, Client
from ..apiclasses import EquipStat


def load_wikinames(filepath: PathLike) -> dict[int, str]:
	with open(filepath, 'r') as file:
		wikidata = json.load(file)

	conversions = {}
	for entry in wikidata:
		data = entry['title']
		image = int(data['Image'].strip(".png"))
		if image in conversions: continue
		name = html.unescape(data['Name'])
		conversions[image] = name
	return conversions


def update_converter(convert_fp: PathLike, wiki_namecache_fp: PathLike, api: ALJsonAPI):
	"""Updates the cached version of the converter data."""
	equip_data_statistics = api.get_sharecfgmodule("equip_data_statistics")

	# retrieve converter data
	overrides = load_wikinames(wiki_namecache_fp)
	conversions = {'icon': dict(), 'gameid': dict(), 'gamename': dict(), 'wikiname': dict()}

	for equipstat in equip_data_statistics.load_all(Client):
		if not isinstance(equipstat, EquipStat): continue
		gameid = equipstat.id
		gamename = equipstat.name
		icon = int(equipstat.icon)
		wikiname = overrides.get(gameid) or overrides.get(icon) or ''

		json_res_data = { "gameid": gameid, "icon": icon, "gamename": gamename, "wikiname": wikiname }
		for k1, k2 in (("icon", str(icon)), ("gameid", str(gameid)), ("gamename", gamename), ("wikiname", wikiname)):
			conversions[k1][k2] = json_res_data

	# save data to file
	with open(convert_fp, 'w', encoding="utf8") as f:
		json.dump(conversions, f, ensure_ascii=False)