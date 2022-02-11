import re
from pathlib import Path
from typing import Union

from .api import Client, JsonLoader, nobbyfix_JsonLoader, AzurLaneTools_JsonLoader, ApiModule, SharecfgModule
from . import apimodules, sharecfgmodules, Constants
from .converter import ships, equips


### USEFUL CONSTANTS
DEFAULT_CLIENTS = [Client.EN, Client.CN, Client.JP]
NAMECODE = re.compile(r'(\{namecode:(\d+)\})')



class UnknownModuleError(Exception):
	"""
	Exception thrown when a modules is requested but does not exist.
	"""

class ALJsonAPI:
	"""
	General purpose class to interact with json gamedata.
	"""
	_apimodules: dict
	_sharecfgmodules: dict
	loader: JsonLoader
	ship_converter: ships.ShipIDConverter
	equip_converter: equips.EquipConverter

	def __init__(self, loader: JsonLoader = None, source_path: Path = None):
		"""
		Initializes the JsonAPI. If neither *loader* nor *source_path* is given,
		the JsonLoader is initialized with the path given in "Constants.JSON_SOURCE_PATH".
		"""
		if loader is None:
			if source_path:
				loader = AzurLaneTools_JsonLoader(source_path)
			else:
				loader = AzurLaneTools_JsonLoader(Constants.JSON_SOURCE_PATH)
		self.loader = loader
		self._apimodules = {}
		self._sharecfgmodules = {}

	# only initialize converter when they are actually used
	def __getattr__(self, name):
		if name == "ship_converter":
			self.ship_converter = ships.load_converter(Constants.SHIPID_CONVERT_CACHE_PATH)
			return self.ship_converter
		if name == "equip_converter":
			self.equip_converter = equips.load_converter(Constants.EQUIP_CONVERT_CACHE_PATH)
			return self.equip_converter
		raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

	### Module Loader Methods

	def _load_apimodule(self, name: str) -> ApiModule:
		"""
		Loads an instance of the ApiModule called *name* and returns it.

		Raises UnknownModuleError if that module does not exist.
		"""
		# get the class of the apimodule with *name*
		moduleclass = apimodules.import_module(name)

		# if no class is returned, that class does not exist, so an exception will be raised
		if not moduleclass:
			raise UnknownModuleError(f"The ApiModule {name} does not exist.")

		# if the module exists, create and instance and return it
		module = moduleclass(_api=self)
		return module

	def _load_sharecfgmodule(self, name: str) -> SharecfgModule:
		"""
		Loads an instance of the SharecfgModule called *name* and returns it.

		If no client has json files under that name, an instance will still be returned
		and all data requests to that module will just return None.
		"""
		# get the class of the apimodule with *name*
		moduleclass = sharecfgmodules.import_module(name)

		# if that module does not exists, the generic module class will be used
		if not moduleclass:
			moduleclass = SharecfgModule
		
		# create the instance and return it
		module = moduleclass(name=name, _loader=self.loader)
		return module

	def _get_module(self, name: str, is_api: bool = False) -> Union[SharecfgModule, ApiModule]:
		"""
		Returns an instance of either a SharecfgModule or ApiModule called *name*.
		If *is_api* is set to true, an ApiModule will be returned, if False a SharecfgModule.

		If the requested ApiModule does not exists, an UnknownModuleError will be raised.

		For SharecfgModules, if no client has json files under that name, an instance will still be returned
		and all data requests to that module will just return None.
		"""
		# determine which instance cache to use depending on *is_api*
		used_cache = self._apimodules if is_api else self._sharecfgmodules
		
		# if there is an instance already in the cache, return it
		if name in used_cache:
			return used_cache[name]

		# determine which loader function to use depending on *is_api* and try to load it
		module = self._load_apimodule(name) if is_api else self._load_sharecfgmodule(name)

		# put the module instance into the cache and return it
		used_cache[name] = module
		return module

	def get_apimodule(self, name: str) -> ApiModule:
		return self._get_module(name, True)

	def get_sharecfgmodule(self, name: str) -> SharecfgModule:
		return self._get_module(name)

	### Additional Api Methods

	def replace_namecode(self, inputstring: str, client: Client) -> str:
		"""
		Replaces namecode references in a string with their respective codes for *client*.
		"""
		name_code = self.get_sharecfgmodule('name_code')
		results = NAMECODE.findall(inputstring)
		for namecode_string, namecode_num in results:
			# get the replacement string 'code' for the found namecode number for *client*
			code = name_code.load_client(namecode_num, client)
			# replace the namecode placeholder in the inputstring with the 'code'
			inputstring = inputstring.replace(namecode_string, code.name)
		return inputstring