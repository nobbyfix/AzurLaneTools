import json
from os import PathLike
from typing import Union

from .. import ALJsonAPI, Client


def load_overrides(filepath: PathLike) -> dict[int, str]:
	"""Loads all all shipname overrides from the given file.

	:param filepath: path to the overrides file"""
	with open(filepath, 'r', encoding='utf8') as file:
		json_data = json.load(file)
	return {int(groupid): name for groupid, name in json_data.items()}


def update_converter(convert_fp: PathLike, override_fp: PathLike, api: ALJsonAPI):
	"""Updates the cached version of the converter data."""
	ship_data_statistics = api.get_sharecfgmodule("ship_data_statistics")

	# retrieve converter data
	overrides = load_overrides(override_fp)
	conversions = {'ship': dict(), 'groupid': dict()}

	def idfilter(dataid: Union[int, str]) -> bool:
		try:
			dataid = int(dataid)
		except: return True
		if dataid%10 != 1: return True
		if dataid//1000 == 900: return True
		if dataid == 901001: return True
		return False

	for shipstat in ship_data_statistics.load_all(Client, idfilter):
		groupid = shipstat.shipid.groupid

		# if groupid is overridden, just add the ship names from there
		if groupid in overrides:
			shipname = overrides[groupid]
		else:
			shipname = shipstat.name

		# add data onto conversions dict
		conversions['ship'][shipname] = groupid
		conversions['groupid'][groupid] = shipname

	# save data to file
	with open(convert_fp, 'w') as f:
		json.dump(conversions, f)
