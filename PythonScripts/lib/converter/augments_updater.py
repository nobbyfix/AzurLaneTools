import json
from os import PathLike

from .. import ALJsonAPI, Client


def update_converter(convert_fp: PathLike, api: ALJsonAPI):
	"""Updates the cached version of the converter data."""
	augment_data_statistics = api.get_sharecfgmodule("spweapon_data_statistics")

	# retrieve converter data
	conversions = {'icon': dict(), 'gameid': dict(), 'shipid': dict(), 'wikiname': dict()}

	def idfilter(dataid: int) -> bool:
		if type(dataid) == str:
			if not dataid.isdigit(): return True
			else: dataid = int(dataid)
		if dataid%20 != 0: return True
	for augmentstat in augment_data_statistics.load_all(Client, idfilter):
		gameid = int(augmentstat.id)
		wikiname = augmentstat.name
		icon = 'Augment_'+str(augmentstat.icon)
		shipid = augmentstat.unique or 0

		# add data onto conversions dict
		json_res_data = { "gameid": gameid, "icon": icon, "shipid": shipid, "wikiname": wikiname }
		for k1, k2 in (("icon", icon), ("gameid", str(gameid)), ("shipid", str(shipid)), ("wikiname", wikiname)):
			if k2:
				conversions[k1][k2] = json_res_data

	# save data to file
	with open(convert_fp, 'w', encoding = "utf8") as f:
		json.dump(conversions, f, ensure_ascii=False)
