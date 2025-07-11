import re
from pathlib import Path

from .api import Client, JsonLoader, nobbyfix_JsonLoader, AzurLaneTools_JsonLoader, Module, ApiModule, SharecfgModule
from . import settings, apimodules, sharecfgmodules, Constants
from .converter import ships, equips, augments


### USEFUL CONSTANTS
DEFAULT_CLIENTS = [Client.EN, Client.CN, Client.JP]
NAMECODE = re.compile(r'(\{namecode:(\d+)\})')

jsonloaders = {
	"nobbyfix": nobbyfix_JsonLoader,
	"AzurLaneTools": AzurLaneTools_JsonLoader,
}


class UnknownModuleError(Exception):
	"""
	Exception thrown when a modules is requested but does not exist.
	"""

class ALJsonAPI:
	"""
	General purpose class to interact with json gamedata.
	"""
	_apimodules: dict[str, ApiModule]
	_sharecfgmodules: dict[str, SharecfgModule]
	loader: JsonLoader
	apisettings: settings.APISettings
	ship_converter: ships.ShipIDConverter
	equip_converter: equips.EquipConverter
	augment_converter: augments.AugmentConverter

	def __init__(self, loader: JsonLoader | None = None, source_path: Path | None = None, settings_path: Path | None = None) -> None:
		"""
		Initializes the JsonAPI. Uses the JsonLoader as set in the settings file at "data/settings.toml".
		Path of the settings file can be overridden using *settings_path*.
		For usage of a different/custom JsonLoader, *loader* can be set, which will ignore the settings file.
		"""
		if source_path:
			raise DeprecationWarning("Initialisation of ALJsonAPI using 'source_path' should be removed.")
		
		if loader:
			self.loader = loader
		else:
			if settings_path:
				self.apisettings = settings.read_and_parse_settings(settings_path)
			else:
				self.apisettings = settings.read_and_parse_settings()
			self.loader = jsonloaders[self.apisettings.jsonloader_variant](self.apisettings.json_source_path)

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
		if name == "augment_converter":
			self.augment_converter = augments.load_converter(Constants.AUGMENT_CONVERT_CACHE_PATH)
			return self.augment_converter
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

		# if the module exists, create an instance and return it
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

	def _get_module(self, name: str, is_api: bool = False) -> SharecfgModule | ApiModule:
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
	
	def get_module(self, name: str) -> Module:
		return self.get_sharecfgmodule(name) or self.get_apimodule(name)

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
