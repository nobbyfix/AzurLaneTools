import os, json

PATH_OVERRIDES = os.path.join('data', 'ship_convert_overrides.json')
PATH_CONVERT = os.path.join('data', 'ship_convert_data.json')

def load_overrides(filepath=PATH_OVERRIDES):
	"""Returns a dict of all groupid overrides.
	
	:param filepath: path to the overrides file"""
	with open(filepath, 'r', encoding='utf8') as jfile:
		json_data = json.load(jfile)
	return {int(groupid): name for groupid, name in json_data.items()}

def update_converter(JsonAPI, filepath=PATH_CONVERT):
	"""Updates the cached version of the converter data.
	
	:param JsonAPI: an instance of the ALJsonAPI
	:param filepath: path to the converter data cache file"""
	ship_data_statistics = JsonAPI.load_multi_sharecfg('ship_data_statistics', JsonAPI.ALL_CLIENTS)
	
	# create set of all groupid from all clients
	all_groupids = set()
	for client_data in ship_data_statistics.values():
		# groupids starting with 900 are probably for enemies, are filtered out
		all_groupids.update({el//10 for el in client_data['all'] if ((el//1000 != 900) and (el%10 == 1) and (el != 901001))})

	# retrieve converter data
	overrides = load_overrides()
	conversions = {'ship': dict(), 'groupid': dict()}
	for groupid in all_groupids:
		# if groupid is overridden, just add the ship names from there
		if groupid in overrides:
			shipname = overrides[groupid]
			conversions['ship'][shipname] = groupid
			conversions['groupid'][groupid] = shipname
			continue
		
		# go through all clients in default order and search if the ship name exists there
		for client, client_data in ship_data_statistics.items():
			shipstat = client_data.get(str(groupid*10+1))

			# if the client does not contain the ship of current groupid, its usually that overrides are missing
			if not shipstat:
				print(f'Name of "{groupid}" could not be in "{client}" found, are the overrides incomplete?')
				continue
			shipname = shipstat['name']
			conversions['ship'][shipname] = groupid
			conversions['groupid'][groupid] = shipname
			break

	# save data to file
	with open(filepath, 'w') as f:
		json.dump(conversions, f)

def load_converter(filepath=PATH_CONVERT):
	"""Returns the converter using the cached converter data.
	
	:param filepath: path to the converter data cache file"""
	
	with open(filepath, 'r') as f:
		ship_data = json.load(f)
	return ShipIDConverter(ship_data['ship'], ship_data['groupid'])

def init_converter(JsonAPI, filepath=PATH_CONVERT):
	"""Updates the converter data cache file and then returns the converter.

	:param JsonAPI: an instance of the ALJsonAPI
	:param filepath: path to the converter data cache file"""
	
	update_converter(JsonAPI, filepath)
	return load_converter()

class ShipIDConverter:
	def __init__(self, ship_to_id:dict, id_to_ship:dict):
		self.ship_to_id = ship_to_id
		self.id_to_ship = id_to_ship
	
	def get_groupid(self, shipname):
		return self.ship_to_id.get(shipname)

	def get_shipname(self, groupid):
		return self.id_to_ship.get(str(groupid))

	def convert(self, key):
		"""Returns either a groupid or shipname depending on the key.
		get_groupid and get_shipname should be preffered.
		
		:param key: a groupid or shipname"""
		groupid = self.get_groupid(str(key))
		shipname = self.get_shipname(key)
		return groupid or shipname

	def get_groupids(self) -> set:
		"""Returns a set of all groupids.
		Because of json limitations the groupids will be strings."""
		return set(self.id_to_ship.keys())

	def get_shipnames(self) -> set:
		"""Returns a set of all shipnames."""
		return set(self.ship_to_id.keys())

if __name__ == "__main__":
	from Utility import defaultJsonAPI
	update_converter(defaultJsonAPI())