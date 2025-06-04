from pathlib import Path
from enum import Enum


### Constant Filepaths ###
# static files (only manual changes)
ITEMNAME_OVERRIDES_PATH = Path("data", "static", "item_name_convert.json")
SHIPID_CONVERT_OVERRIDE_PATH = Path("data", "static", "shipid_overrides.json")

# dynamic files (generated files)
SHIPID_CONVERT_CACHE_PATH = Path("data", "dynamic", "shipid_convert.json")
EQUIP_CONVERT_CACHE_PATH = Path("data", "dynamic", "equip_convert.json")
EQUIP_WIKIDATA_PATH = Path("data", "dynamic", "equip_wikinames.json")
SKIN_WIKIDATA_PATH = Path("data", "dynamic", "skin_wikidata.json")
AUGMENT_CONVERT_CACHE_PATH = Path("data", "dynamic", "augment_convert.json")


class Rarity(Enum):
	"""
	Enum class that allows conversion of rarity values between the game data and wiki.
	"""
	__num2member_map__: dict[int, "Rarity"] = {}

	rarity: int
	"""Rarity id used in the game."""
	label: str
	"""Full rarity name used on the wiki."""
	letter: str
	"""Single letter used on the wiki in some templates."""

	NORMAL0			= (0,	"Normal",		"E")
	NORMAL			= (1,	"Normal",		"E")
	RARE			= (2,	"Rare",			"B")
	ELITE			= (3,	"Elite",		"P")
	SUPER_RARE		= (4,	"Super Rare",	"G")
	PRIORITY		= (4,	"Priority",		"G")
	ULTRA_RARE		= (5,	"Ultra Rare",	"R")
	LEGENDARY		= (5,	"Legendary",	"R")
	DECISIVE		= (5,	"Decisive",		"R")
	VALENTINE_GIFT	= (8,	"Normal",		"E")
	GIFT_OTHER		= (9,	"Super Rare",	"G")
	UNKNOWN18		= (17,	"???",			"?")

	def __init__(self, rarity, label, letter) -> None:
		# add attributes to enum objects
		self.rarity = rarity
		self.label = label
		self.letter = letter
		# add enum objects to member maps
		if rarity not in self.__num2member_map__:
			self.__num2member_map__[rarity] = self

	def __str__(self) -> str:
		return self.label

	@classmethod
	def from_id(cls, rarity_num: int, is_research: bool = False) -> "Rarity" | None:
		"""
		Returns a `Rarity` member with *rarity_num* matching it's `rarity` attribute.
		Returns `None` if no match exists.

		For `rarity_num=4`, `Rarity.SUPER_RARE` will be returned over `Rarity.PRIORITY`.
		For `rarity_num=5`, `Rarity.ULTRA_RARE` will be returned over `Rarity.LEGENDARY` and `Rarity.DECISIVE`.
		For `rarity_num=7`, `Rarity.SUPER_RARE` will be returned, as there is only a single item (likely in error).

		If *is_research* is set True, `Rarity.PRIORITY` and `Rarity.DECISIVE` will be prioritised.
		"""
		if is_research:
			if rarity := {4: Rarity.PRIORITY, 5: Rarity.DECISIVE}.get(rarity_num):
				return rarity
		if rarity_num == 7:
			return Rarity.SUPER_RARE
		return cls.__num2member_map__.get(rarity_num)


# from /model/const/nation.lua#Nation2Name
class Nation(Enum):
	"""
	Enum class that allows conversion of nation values between the game data and wiki.
	"""
	id: int
	"""Nation id used in the game."""
	label: str
	"""Name of the nation used on the wiki."""

	UNIVERSAL			= (0,	"Universal")
	EAGLE_UNION			= (1,	"Eagle Union")
	ROYAL_NAVY			= (2,	"Royal Navy")
	SAKURA_EMPIRE		= (3,	"Sakura Empire")
	IRON_BLOOD			= (4,	"Iron Blood")
	DRAGON_EMPERY		= (5,	"Dragon Empery")
	SARDEGNA_EMPIRE		= (6,	"Sardegna Empire")
	NORTHERN_PARLIAMENT	= (7,	"Northern Parliament")
	IRIS_LIBRE			= (8,	"Iris Libre")
	VICHYA_DOMINION		= (9,	"Vichya Dominion")
	IRIS_ORTHODOXY		= (10,	"Iris Orthodoxy")
	TULIPA				= (11,	"Kingdom of Tulipa")
	TEMPESTA			= (96,	"Tempesta")
	META				= (97,	"META")
	UNIVERSAL2			= (98,	"Universal")
	SIREN				= (99,	"Siren")
	NEPTUNIA			= (101,	"Neptunia")
	BILIBILI			= (102,	"Bilibili")
	UTAWARERUMONO		= (103,	"Utawarerumono")
	KIZUNA_AI			= (104,	"Kizuna AI")
	HOLOLIVE			= (105,	"Hololive")
	VENUS_VACATION		= (106,	"Venus Vacation")
	IDOLMASTER			= (107,	"The Idolmaster")
	SSSS				= (108,	"SSSS")
	ATELIER_RYZA		= (109,	"Atelier Ryza")
	SENRAN_KAGURA		= (110,	"Senran Kagura")
	TO_LOVE_RU			= (111,	"To LOVE-Ru")

	def __new__(cls, nation_id, label):
		obj = object.__new__(cls)
		obj._value_ = nation_id
		obj.label = label
		return obj
	
	def __str__(self) -> str:
		return self.label

	@property
	def id(self) -> int:
		"""Nation id used in the game."""
		return self.value

	@classmethod
	def from_id(cls, nation_id: int) -> "Nation" | None:
		"""
		Returns a `Nation` member with *nation_id* matching it's `id` attribute.
		Returns `None` if no match exists.
		"""
		return cls._value2member_map_.get(nation_id)


class Attribute(Enum):
	"""
	Enum class that allows conversion of ship attributes between the game data and wiki.
	"""
	pos: int
	"""The position of the attribute in the ship statistics array."""
	wiki_param_name: str
	"""The name of the parameter on wiki templates used for the attribute."""
	wiki_template_name: str
	"""The name of the template displaying the attribute icon on the wiki."""

	DURABILITY		= (0,	"Health",		"Health")
	CANNON			= (1,	"Fire",			"Firepower")
	TORPEDO			= (2,	"Torp",			"Torpedo")
	ANTIAIRCRAFT	= (3,	"AA",			"AA")
	AIR				= (4,	"Air",			"Aviation")
	RELOAD			= (5,	"Reload",		"Reload")
	ARMOR			= (6,	"Armor_Debug",		"Armor")
	HIT				= (7,	"Acc",			"Accuracy")
	DODGE			= (8,	"Evade",		"Evasion")
	SPEED			= (9,	"Speed",		"Speed")
	LUCK			= (10,	"Luck",			"Luck")
	ANTISUB			= (11,	"ASW",			"ASW")

	def __init__(self, pos, param_name, template_name) -> None:
		# add attributes to enum objects
		self.pos = pos
		self.wiki_param_name = param_name
		self.wiki_template_name = template_name

	def __str__(self) -> str:
		return self.name


# from /model/const/shiptype.lua
class ShipType(Enum):
	"""
	Enum class that allows conversion of shiptype values between the game data and wiki.
	"""
	__id2member_map__: dict[int, "ShipType"] = {}
	__name2member_map__: dict[str, "ShipType"] = {}
	__fullname2member_map__: dict[str, "ShipType"] = {}

	id: int
	"""The ID of the shiptype as used in the game."""
	typename: str
	"""The full name of the shiptype as used on the wiki."""
	categoryname: str
	"""The full name of the shiptypes category as used on the wiki"""
	templatename: str
	"""The name of the template to display the shiptype icon on the wiki."""
	typetext: str
	"""The text displaying the abbreviation of the shiptype or multiple types for shiptype bundles."""

	DD		= (1,	"Destroyer",					"Destroyers",					"DD",	"DD")
	CL		= (2,	"Light Cruiser",				"Light cruisers",				"CL",	"CL")
	CA		= (3,	"Heavy Cruiser",				"Heavy cruisers",				"CA",	"CA")
	BC		= (4,	"Battlecruiser",				"Battlecruisers",				"BC",	"BC")
	BB		= (5,	"Battleship",					"Battleships",					"BB",	"BB")
	CVL		= (6,	"Light Aircraft Carrier",		"Light aircraft carriers",		"CVL",	"CVL")
	CV		= (7,	"Aircraft Carrier",				"Aircraft carriers",			"CV",	"CV")
	SS		= (8,	"Submarine",					"Submarines",					"SS",	"SS")
	CAV		= (9,	"Aviation Cruiser",				"Aviation cruisers",			"CAV",	"CAV")
	BBV		= (10,	"Aviation Battleship",			"Aviation battleships",  		"BBV",	"BBV")
	CT		= (11,	"Torpedo Cruiser",				"Torpedo cruisers",				"CT",	"CT")
	AR		= (12,	"Repair Ship",					"Repair ships",					"AR",	"AR")
	BM		= (13,	"Monitor",						"Monitors",						"BM",	"BM")
	SSV		= (17,	"Submarine Carrier",			"Submarine carriers",			"SSV",	"SSV")
	CB		= (18,	"Large Cruiser",				"Large cruisers",				"CB",	"CB")
	AE		= (19,	"Munition Ship",				"Munition ships",				"AE",	"AE")
	DDG_V	= (20,	"DDG",							"Guided-missile destroyers",	"DDG",	"DDG")
	DDG_M	= (21,	"DDG",							"Guided-missile destroyers",	"DDG",	"DDG")
	IX_S	= (22,	"Sailing Frigate (Submarine)",	"Sailing Frigate",				"IXs",	"IX")
	IX_V	= (23,	"Sailing Frigate (Vanguard)",	"Sailing Frigate",				"IXv",	"IX")
	IX_M	= (24,	"Sailing Frigate (Main)",		"Sailing Frigate",				"IXm",	"IX")
	ZHAN	= (-1,	"",								"",								"BC",	"BC or BB")
	HANG	= (-1,	"",								"",								"CVL",	"CV or CVL")
	QIAN	= (-1,	"",								"",								"SS",	"SS or SSV or IX")
	ZHONG	= (-1,	"",								"",								"CB",	"CB or CA")
	FANQIAN	= (-1,	"",								"",								"DD",	"DD or DDG or CL")
	QUZHU	= (-1,	"",								"",								"DD",	"DD or DDG")
	FEGNFAN	= (-1,	"",								"",								"IXs",	"IX")

	def __init__(self, typeid, typename, catname, templatename, typetext):
		# add attributes to enum objects
		self.id = typeid
		self.typename = typename
		self.categoryname = catname
		self.templatename = templatename
		self.typetext = typetext

		# add enum objects to member maps
		self.__name2member_map__[self.name.lower()] = self
		if typeid != -1:
			self.__id2member_map__[typeid] = self
		if typename != "":
			self.__fullname2member_map__[typename.lower()] = self

	@classmethod
	def from_id(cls, type_id: int) -> "ShipType" | None:
		"""
		Returns a `ShipType` member with *type_id* matching it's `id` attribute.
		Returns `None` if no match exists.
		"""
		return cls.__id2member_map__.get(type_id)

	@classmethod
	def from_type(cls, type_name: str) -> "ShipType" | None:
		"""
		Returns a `ShipType` member with *type_name* matching it's `name` attribute, ignoring capitalization.
		Returns `None` if no match exists.
		"""
		return cls.__name2member_map__.get(type_name)

	@classmethod
	def from_name(cls, type_name: str) -> "ShipType" | None:
		"""
		Returns a `ShipType` member with *type_name* matching it's `typename` attribute.
		Returns `None` if no match exists.
		"""
		return cls.__fullname2member_map__.get(type_name)


class Armor(Enum):
	__label2member_map__: dict[str, "Armor"] = {}
	id: int
	"""ID of the armor type as used in the game."""
	label: str
	"""Name of the armor type."""

	LIGHT	= (1,	"Light")
	MEDIUM	= (2,	"Medium")
	HEAVY	= (3,	"Heavy")

	def __new__(cls, armor_id, label):
		obj = object.__new__(cls)
		obj._value_ = armor_id
		return obj

	def __init__(self, armor_id, label) -> None:
		# add attributes to enum objects
		self.label = label
		# add enum objects to member maps
		self.__label2member_map__[label] = self

	def __str__(self) -> str:
		return self.label

	@property
	def id(self) -> int:
		"""
		ID of the armor type as used in the game.
		"""
		return self.value

	@classmethod
	def from_id(cls, armor_id: int) -> "Armor" | None:
		"""
		Returns an Armor member with matching *armor_id* if match exists, otherwise None.
		"""
		return cls._value2member_map_.get(armor_id)

	@classmethod
	def from_label(cls, armor_label: str) -> "Armor" | None:
		"""
		Returns an Armor member with matching *armor_label* if match exists, otherwise None.
		"""
		return cls.__label2member_map__.get(armor_label)
