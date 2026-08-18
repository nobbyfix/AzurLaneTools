import json
import sys
from abc import ABCMeta, abstractmethod
from collections import defaultdict
from collections.abc import Callable, Container, Generator, Hashable, Iterable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar, Self, TypeAlias

if sys.version_info < (3, 15):
	from frozendict import frozendict


JsonDict: TypeAlias = frozendict[Any, Any]


@dataclass(eq=False)
class ClientDataMixin:
	"""
	Data fields shared by all :class:`Client` enum members.

	Used as a mixin so that each ``Client`` member carries typed metadata
	alongside its enum value.
	"""

	locale_code: str
	"""The locale code of the client. Required for interaction with certain source repositories."""
	package_name: str
	"""Package name on the Google Play Store."""
	active: bool = field(repr=False, default=True)
	"""Whether the Client is receiving updates."""


class Client(ClientDataMixin, Enum):
	"""
	Enumeration of supported Azur Lane game clients.
	"""

	__package_name_map__: ClassVar[dict[str, Self]] = {}

	EN = "en-US", "com.YoStarEN.AzurLane"
	CN = "zh-CN", ""
	JP = "ja-JP", "com.YoStarJP.AzurLane"
	KR = "ko-KR", "kr.txwy.and.blhx", False
	TW = "zh-TW", "com.hkmanjuu.azurlane.gp", False

	@classmethod
	def from_package_name(cls, package_name: str) -> Self | None:
		"""
		Get a Client member with matching package name.

		Args:
			package_name: The package name to match

		Returns:
			Client or None: The matching Client member or None if no match
		"""
		if not cls.__package_name_map__:
			cls.__package_name_map__ = {member.package_name: member for member in cls}
		return cls.__package_name_map__.get(package_name)


class FrozenDictDecoder(json.JSONDecoder):
	"""
	Custom JsonDecoder that uses frozendict and tuples to make all values hashable.
	"""

	def __init__(self, *args, **kwargs):

		def object_hook(dct):
			# If values contain unhashable types like lists, convert them to tuples
			for key, val in dct.items():
				if isinstance(val, list):
					dct[key] = tuple(val)
			return frozendict(dct)

		super().__init__(*args, object_hook=object_hook, **kwargs)


class JsonLoader(metaclass=ABCMeta):
	"""
	Abstract class providing an interface for loading sharecfg and gamecfg json files.
	"""

	source_directory: Path
	""" The path to the directory containg the json source files. """

	def __init__(self, source_directory: Path) -> None:
		"""
		source_directory - directory containing the converted json files
		"""
		if not source_directory.exists():
			raise FileNotFoundError(f"The source directory {source_directory} does not exist.")
		self.source_directory = source_directory

	def __repr__(self) -> str:
		return f"<{self.__class__.__name__}: '{self.source_directory}'>"

	def __str__(self) -> str:
		return f"{self.__class__.__name__}('{self.source_directory}')"

	def json_load(self, file) -> Any:
		return json.load(file, cls=FrozenDictDecoder)

	@abstractmethod
	def load_sharecfg(self, sharecfg_name: str, client: Client) -> JsonDict:
		"""
		Returns the contents of a single sharecfg json file.

		sharecfg_name - name of the sharecfg file to return contents from
		client - the client to load the sharecfg file from
		"""

	def load_multi_sharecfg(self, sharecfg_name: str, clients: Iterable[Client]) -> dict[Client, JsonDict]:
		"""
		Returns the contents of multiple sharecfg json files as a dict with format {client: data},
		with data being the client's decoded json content. If the sharecfg file for a client can not be found,
		it will not be inside the returned dict.

		sharecfg_name - name of the sharecfg files to return contents from
		clients - iterable containing clients to load the sharecfg files from
		"""
		multi_sharecfg = {}
		for client in clients:
			try:
				json_data = self.load_sharecfg(sharecfg_name, client)
				multi_sharecfg[client] = json_data
			except FileNotFoundError:
				pass
		return multi_sharecfg

	@abstractmethod
	def load_sharecfgdata(self, sharecfg_name: str, client: Client) -> JsonDict:
		"""
		Returns the contents of a single sharecfgdata json file.

		sharecfg_name - name of the sharecfgdata file to return contents from
		client - the client to load the sharecfgdata file from
		"""

	def load_multi_sharecfgdata(self, sharecfg_name: str, clients: Iterable[Client]) -> dict[Client, JsonDict]:
		"""
		Returns the contents of multiple sharecfgdata json files as a dict with format {client: data},
		with data being the client's decoded json content. If the sharecfgdata file for a client can not be found,
		it will not be inside the returned dict.

		sharecfg_name - name of the sharecfgdata files to return contents from
		clients - iterable containing clients to load the sharecfgdata files from
		"""
		multi_sharecfg = {}
		for client in clients:
			try:
				json_data = self.load_sharecfgdata(sharecfg_name, client)
				multi_sharecfg[client] = json_data
			except FileNotFoundError:
				pass
		return multi_sharecfg

	@abstractmethod
	def load_gamecfg(self, gamecfg_type: str, gamecfg_name: str, client: Client) -> JsonDict:
		"""
		Returns the contents of a single gamecfg json file.

		It is recommended to rather use the type specific methods to load gamecfg data.

		gamecfg_type - type of the gamecfg data ("dungeon", "buff", "skill", "story")
		gamecfg_name - name of the gamecfg file to return contents from
		client - the client to load the gamecfg file from
		"""

	def load_multi_gamecfg(self, gamecfg_type: str, gamecfg_name: str, clients: Iterable[Client]) -> dict[Client, JsonDict]:
		"""
		Returns the contents of multiple gamecfg json files as a dict with format {client: data},
		with data being the client's decoded json content. If the gamecfg file for a client can not be found,
		it will not be inside the returned dict.

		It is recommended to rather use the type specific methods to load gamecfg data.

		gamecfg_type - type of the gamecfg data ("dungeon", "buff", "skill", "story")
		gamecfg_name - name of the gamecfg files to return contents from
		clients - iterable containing clients to load the gamecfg files from
		"""
		multi_gamecfg = {}
		for client in clients:
			try:
				json_data = self.load_gamecfg(gamecfg_type, gamecfg_name, client)
				multi_gamecfg[client] = json_data
			except FileNotFoundError:
				pass
		return multi_gamecfg

	def load_dungeon(self, dungeon_id: int | str, client: Client) -> JsonDict:
		return self.load_gamecfg("dungeon", str(dungeon_id), client)

	def load_multi_dungeon(self, dungeon_id: int | str, clients: Iterable[Client]) -> dict[Client, JsonDict]:
		return self.load_multi_gamecfg("dungeon", str(dungeon_id), clients)

	def load_buff(self, buff_id: int | str, client: Client) -> JsonDict:
		return self.load_gamecfg("buff", "buff_" + str(buff_id), client)

	def load_multi_buff(self, buff_id: int | str, clients: Iterable[Client]) -> dict[Client, JsonDict]:
		return self.load_multi_gamecfg("buff", "buff_" + str(buff_id), clients)

	def load_skill(self, skill_id: int | str, client: Client) -> JsonDict:
		return self.load_gamecfg("skill", "skill_" + str(skill_id), client)

	def load_multi_skill(self, skill_id: int | str, clients: Iterable[Client]) -> dict[Client, JsonDict]:
		return self.load_multi_gamecfg("skill", "skill_" + str(skill_id), clients)

	def load_story(self, story_name: str, client: Client) -> JsonDict:
		return self.load_gamecfg("story", story_name, client)

	def load_multi_story(self, story_name: str, clients: Iterable[Client]) -> dict[Client, JsonDict]:
		return self.load_multi_gamecfg("story", story_name, clients)

	def load_card(self, card_id: int | str, client: Client) -> JsonDict:
		return self.load_gamecfg("card", "card_" + str(card_id), client)

	def load_multi_card(self, card_id: int | str, clients: Iterable[Client]) -> dict[Client, JsonDict]:
		return self.load_multi_gamecfg("card", "card_" + str(card_id), clients)


class nobbyfix_JsonLoader(JsonLoader):
	"""
	Implementation of the JsonLoader for this json repository:
	https://github.com/nobbyfix/AzurLaneSourceJson
	"""

	def load_sharecfg(self, sharecfg_name: str, client: Client) -> JsonDict:
		jsonpath = Path(self.source_directory, client.name, "sharecfg", sharecfg_name + ".json")
		with open(jsonpath, "r", encoding="utf8") as f:
			return self.json_load(f)

	def load_sharecfgdata(self, sharecfg_name: str, client: Client) -> JsonDict:
		raise NotImplementedError("!!! Repo has no sharecfgdata files !!!")

	def load_gamecfg(self, gamecfg_type: str, gamecfg_name: str, client: Client) -> JsonDict:
		jsonpath = Path(self.source_directory, client.name, gamecfg_type, gamecfg_name + ".json")
		with open(jsonpath, "r", encoding="utf8") as f:
			return self.json_load(f)


class AzurLaneTools_JsonLoader(JsonLoader):
	"""
	Implementation of the JsonLoader for this json repository:
	https://github.com/AzurLaneTools/AzurLaneData
	"""

	_gamecfg_cache: dict[Client, dict[str, JsonDict]]

	def __init__(self, source_directory: Path) -> None:
		super().__init__(source_directory)
		self._gamecfg_cache = defaultdict(dict)

	def load_sharecfg(self, sharecfg_name: str, client: Client) -> JsonDict:
		jsonpath = Path(self.source_directory, client.name, "ShareCfg", sharecfg_name + ".json")
		with open(jsonpath, "r", encoding="utf8") as f:
			return self.json_load(f)

	def load_sharecfgdata(self, sharecfg_name: str, client: Client) -> JsonDict:
		jsonpath = Path(self.source_directory, client.name, "sharecfgdata", sharecfg_name + ".json")
		with open(jsonpath, "r", encoding="utf8") as f:
			return self.json_load(f)

	def load_gamecfg(self, gamecfg_type: str, gamecfg_name: str, client: Client) -> JsonDict:
		if client == Client.JP and gamecfg_type == "story":
			gamecfg_type = "storyjp"

		if gamecfg_type not in self._gamecfg_cache[client]:
			if gamecfg_type in ["buff", "skill"]:
				jsonpath = Path(self.source_directory, client.name, gamecfg_type + "Cfg.json")
			elif gamecfg_type in ["dungeon", "story", "storyjp"]:
				jsonpath = Path(self.source_directory, client.name, "GameCfg", gamecfg_type + ".json")
			else:
				raise NotImplementedError(f"The gamecfg_type '{gamecfg_type}' is not implemented.")

			with open(jsonpath, "r", encoding="utf8") as f:
				jsondata = self.json_load(f)
			self._gamecfg_cache[client][gamecfg_type] = jsondata
		return self._gamecfg_cache[client][gamecfg_type][gamecfg_name]


class Nagami_JsonLoader(JsonLoader):
	"""
	Implementation of the JsonLoader for this json repository:
	https://github.com/JustNagami/al-json
	"""

	_gamecfg_cache: dict[Client, dict[str, dict]]

	def load_sharecfg(self, sharecfg_name: str, client: Client) -> JsonDict:
		jsonpath = Path(self.source_directory, client.name, "sharecfg", sharecfg_name + ".json")
		with open(jsonpath, "r", encoding="utf8") as f:
			return self.json_load(f)

	def load_sharecfgdata(self, sharecfg_name: str, client: Client) -> JsonDict:
		jsonpath = Path(self.source_directory, client.name, "sharecfgdata", sharecfg_name + ".json")
		with open(jsonpath, "r", encoding="utf8") as f:
			return self.json_load(f)

	def load_gamecfg(self, gamecfg_type: str, gamecfg_name: str, client: Client) -> JsonDict:
		if client == Client.JP and gamecfg_type == "story":
			gamecfg_type = "storyjp"

		if gamecfg_type not in self._gamecfg_cache[client]:
			if gamecfg_type in ["buff", "skill", "card"]:
				jsonpath = Path(self.source_directory, client.name, gamecfg_type + "Cfg.json")
			elif gamecfg_type in ["activity", "backyardtheme", "dorm", "dungeon", "story", "storyjp", "useragreems"]:
				jsonpath = Path(self.source_directory, client.name, "GameCfg", gamecfg_type + ".json")
			else:
				raise NotImplementedError(f"The gamecfg_type '{gamecfg_type}' is not implemented.")

			with open(jsonpath, "r", encoding="utf8") as f:
				jsondata = self.json_load(f)
			self._gamecfg_cache[client][gamecfg_type] = jsondata
		return self._gamecfg_cache[client][gamecfg_type][gamecfg_name]


APIdataclass = lambda cls, *args: dataclass(cls, *args, init=False, eq=False)
"""
Allows for simpler coding style, since all apiclasses need these params set.
"""


@dataclass(eq=False)
class ApiData(Hashable):
	"""
	Generic data class returned by all modules.
	"""

	id: int | str
	""" Unique ID of the ApiData within their corresponding module. """

	def __eq__(self, other) -> bool:
		if isinstance(other, ApiData):
			return self.id == other.id
		return False

	def __hash__(self) -> int:
		return hash(self.id)


@APIdataclass
class SharecfgData(ApiData, Hashable, Container):
	"""
	Data class returned by sharecfg modules.
	"""

	_json: JsonDict = field(repr=False)

	def __init__(self, json: JsonDict, **kwargs):
		self._json = json
		for k, v in kwargs.items():
			setattr(self, k, v)

	def __getitem__(self, key) -> Any:
		try:
			v = self._json[key]
		except KeyError as e:
			raise AttributeError from e

		if isinstance(v, str):
			return v.strip()
		return v

	def __getattr__(self, name) -> Any:
		return self[name]

	def __contains__(self, key) -> bool:
		return key in self._json

	def __eq__(self, other) -> bool:
		if isinstance(other, SharecfgData):
			return self._json == other._json
		return False

	def __hash__(self) -> Any:
		return hash(self._json)

	def get(self, key, default=None) -> Any:
		try:
			return self[key]
		except AttributeError:
			return default


@APIdataclass
class MergedSharecfgData(ApiData):
	"""
	Data class returned by ApiModules that merges multiple SharecfgData instances.
	"""

	_scfgdata: list[SharecfgData] = field(repr=False)

	def __init__(self, *args: SharecfgData, **kwargs) -> None:
		self._scfgdata = []
		for arg in args:
			if isinstance(arg, SharecfgData):
				self._scfgdata.append(arg)

		for k, v in kwargs.items():
			setattr(self, k, v)

	def __getattr__(self, name):
		for sdata in self._scfgdata:
			try:
				data = getattr(sdata, name)
				return data
			except AttributeError:
				pass
		raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

	def __contains__(self, key):
		for sdata in self._scfgdata:
			if key in sdata:
				return True
		return False


@dataclass
class Module(metaclass=ABCMeta):
	"""
	Abstract module class implementing basic game data interaction.

	All data requests return None if there is no entry for the dataid for the client.
	"""

	# cache to hold reference to parsed apidata so it doesn't have to be parsed again
	_cache: dict[Client, dict[str, ApiData | None]] = field(
		default_factory=lambda: {c: {} for c in Client}, init=False, repr=False
	)

	def _load_from_cache(self, dataid: str, client: Client) -> ApiData | None:
		"""
		Tries to load the ApiData entry associated with *dataid* from the cache for *client*.
		If the client is not in the cache or there is no entry for *dataid* for *client*,
		None is returned.
		"""
		if client in self._cache:
			return self._cache[client].get(dataid)

	@abstractmethod
	def _load_client(self, dataid: str, client: Client) -> ApiData | None:
		"""
		Tries to load the ApiData entry associated with *dataid* for *client*.
		If there is no *dataid* associated with *client*, None is returned.

		This method bypasses the cache and is only intented for internal use from the class itself.
		The method load_client should be used instead.
		"""

	def load_client(self, dataid: int | str, client: Client) -> ApiData | None:
		"""
		Tries to load the ApiData entry associated with *dataid* for *client*.
		If there is no *dataid* associated with *client*, None is returned.
		"""
		# convert to string, because the internal _load_client only takes strings as dataid
		dataid = str(dataid)
		# try to load from cache first, if None is returned load using internal loader method
		if data := self._load_from_cache(dataid, client):
			return data

		data = self._load_client(dataid, client)
		# save to cache
		self._cache[client][dataid] = data
		return data

	@abstractmethod
	def all_client_ids(self, client: Client) -> Iterable[int | str]:
		"""
		Returns all dataids that are associated with *client* as an iterable.
		"""

	def all_client(self, client: Client, id_filter: Callable[[int | str], bool] | None = None) -> Generator[ApiData]:
		"""
		Returns all ApiData entries associated with *client* as a generator.

		An *id_filter* can be used to pre-filter certain entries using their ids.
		The id_filter is a callable that takes an ApiData ID as input and returns whether it
		should be included or not as a boolean.
		There is no guarantee about the type of the ApiData ID, it should be assumed that both
		strings or integer can be supplied.
		"""
		if id_filter:
			filtered_ids = [dataid for dataid in self.all_client_ids(client) if not id_filter(dataid)]
		else:
			filtered_ids = self.all_client_ids(client)

		for dataid in filtered_ids:
			# only yield entry if an result is returned, otherwise it can be skipped
			if data := self.load_client(dataid, client):
				yield data

	def load_first(self, dataid: int | str, clients: Client | Iterable[Client]) -> ApiData | None:
		"""
		Returns the first ApiData entry with *dataid* from the *clients* given.
		The order used to check depends on the order of the iterable given with *clients*.
		If there is no *dataid* associated with any of the *clients* given, None is returned.
		"""
		if isinstance(clients, Client):
			return self.load_client(dataid, clients)
		else:
			for client in clients:
				if data := self.load_client(dataid, client):
					return data

	def all_ids(self, clients: Iterable[Client]) -> set[int | str]:
		"""
		Returns a set of all dataids associated with the *clients* given.
		Note that not all clients hava data associated with all returned ids.
		"""
		ids = set()
		for client in clients:
			if client_ids := self.all_client_ids(client):
				ids = ids.union(client_ids)
		return ids

	def load_all(self, clients: Iterable[Client], id_filter: Callable[[int | str], bool] | None = None) -> Generator[ApiData]:
		"""
		Returns all ApiData entries associated with *clients* as a generator.
		The ApiData returned for a certain dataid will be determined by Module.load_first.

		An *id_filter* can be used to pre-filter certain entries using their ids.
		The id_filter is a callable that takes an ApiData ID as input and returns whether it
		should be included or not as a boolean.
		There is no guarantee about the type of the ApiData ID, it should be assumed that both
		strings or integer can be supplied.
		"""
		if id_filter:
			filtered_ids = [dataid for dataid in self.all_ids(clients) if not id_filter(dataid)]
		else:
			filtered_ids = self.all_ids(clients)

		for dataid in filtered_ids:
			# only yield entry if an result is returned, otherwise it can be skipped
			if data := self.load_first(dataid, clients):
				yield data


@dataclass
class SharecfgmoduleDataSettings:
	is_sublisted: bool = False
	is_sharecfgdata: bool = False
	is_sharecfgdata2: bool = False


@dataclass
class SharecfgModule(Module):
	"""
	Implementation of the Module class for sharecfg files.
	"""

	name: str
	"""Name of the Module. Matches with the name of the file containing the underlying data."""
	_loader: JsonLoader = field(repr=False)
	_data: dict[Client, JsonDict | None] = field(default_factory=dict, init=False, repr=False)
	_settings: SharecfgmoduleDataSettings = field(default_factory=SharecfgmoduleDataSettings, init=False)
	_all_key_warning: bool = field(default=False, init=False, repr=False)

	def _load_data(self, client: Client) -> JsonDict | None:
		"""
		Loads the underlying json data using the JsonLoader for *client*.
		If the file can not be found by the loader, the error will be ignored
		and the loaded data counted as empty for *client*.

		Returns the loaded json data on success, otherwise None.
		"""
		# check whether the data for *client* has been loaded already
		if not client in self._data:
			# try loading the data using the loader
			# on failure mark the data for client as None so loading is not attempted again
			try:
				jsondata = self._loader.load_sharecfg(self.name, client)
				jsondata = self._process_data(client, jsondata)

				# do sharecfgdata loading if sharecfg file is a sharecfgdata one
				# has to be done on sharecfg load, otherwise all_id functions return None
				if self._settings.is_sharecfgdata or self._settings.is_sharecfgdata2:
					self._do_sharecfgdata_loading(client, jsondata)
			except FileNotFoundError:
				self._data[client] = None
		# return *client* json data for easier access in data loader methods
		return self._data[client]

	def _do_sharecfgdata_loading(self, client: Client, clientdata: JsonDict) -> None:
		if self._settings.is_sharecfgdata:
			sharecfgdataname = clientdata["__name"]
			try:
				sharecfgdata = self._loader.load_sharecfgdata(sharecfgdataname, client)
				self._data[client] |= sharecfgdata  # pyright: ignore [reportOperatorIssue]
			except FileNotFoundError:
				print(f"Failed to load sharecfgdata '{sharecfgdataname}' for module '{self.name}'.")

		if self._settings.is_sharecfgdata2:
			sharecfgdataname = self.name
			try:
				sharecfgdata = self._loader.load_sharecfgdata(sharecfgdataname, client)
				self._data[client] |= sharecfgdata  # pyright: ignore [reportOperatorIssue]
			except FileNotFoundError:
				print(f"Failed to load sharecfgdata '{sharecfgdataname}' for module '{self.name}'.")

	def _process_data(self, client: Client, jsondata: JsonDict) -> JsonDict:
		if jsondata == []:
			jsondata = frozendict()
			self._settings.is_sharecfgdata2 = True

		self._settings.is_sublisted = "indexs" in jsondata
		self._settings.is_sharecfgdata = "__name" in jsondata
		self._data[client] = jsondata
		return jsondata

	def _load(self, dataid: str, client: Client) -> JsonDict | None:
		"""
		Returns the json data for *dataid* associated with *client*.
		"""
		# make sure *client* json data is already loaded
		if clientdata := self._load_data(client):
			if data := clientdata.get(dataid):
				return data

			# do sublist loading if the sharecfg file is sublisted
			if self._settings.is_sublisted and (sublistid := clientdata["indexs"].get(dataid)):
				sublistname = clientdata["subList"][sublistid - 1]
				sublistpath = f"{clientdata['subFolderName'].lower()}/{sublistname}"
				try:
					sublist_jsondata = self._loader.load_sharecfg(sublistpath, client)
					self._data[client] |= sublist_jsondata  # pyright: ignore [reportOperatorIssue]
					return self._data[client].get(dataid)  # pyright: ignore [reportOptionalMemberAccess]
				except FileNotFoundError:
					print(f"Failed to load sublist '{sublistpath}' for module '{self.name}'.")

	def _instantiate_client(self, dataid: str, data: JsonDict) -> SharecfgData:
		"""
		Creates the instance of SharecfgData. Allows subclasses to override this method
		to create subclass instances of SharecfgData.
		"""
		return SharecfgData(id=dataid, json=data)

	def _load_client(self, dataid: str, client: Client) -> SharecfgData | None:
		"""
		Tries to load the SharecfgData entry associated with *dataid* for *client*.
		If there is no *dataid* associated with *client*, None is returned.

		This method bypasses the cache and is only intented for internal use from the class itself.
		The method load_client should be used instead.
		"""
		if data := self._load(dataid, client):
			return self._instantiate_client(dataid, data)

	def all_client_ids(self, client: Client) -> Iterable[int | str]:
		"""
		Returns all dataids that are associated with *client* as an iterable.
		"""
		if ids := self._load("all", client):
			return ids

		# print warning that "all" key is missing
		if not self._all_key_warning:
			print(f"WARNING: \"all\" key not present for client '{client.name}' in module '{self.name}'.")
			self._all_key_warning = True

		# use the key view of the entire client dict for missing "all" key
		if data := self._load_data(client):
			return data.keys()
		return []


@dataclass
class ApiModule(Module, metaclass=ABCMeta):
	"""
	Abstract module class implementing more advanced game data interaction.
	Using ApiModules, ApiData can be returned that shares ids between multiple SharecfgModules.

	Since there is no shared standard between ApiModules how data is loaded,
	the loader functions have to be implemented on the individual modules themselves.
	"""

	_api: "ALJsonAPI"

	def _getmodule(self, modulename: str) -> SharecfgModule:
		"""
		Returns the requested SharecfgModule with *modulename*.
		"""
		return self._api.get_sharecfgmodule(modulename)
