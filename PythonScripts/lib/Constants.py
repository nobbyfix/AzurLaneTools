from pathlib import Path
from enum import Enum


# Constant Filepaths
JSON_SOURCE_PATH = Path("..", "SrcJson").resolve()
SHIPID_CONVERT_CACHE_PATH = Path("data", "shipid_convert.json")
SHIPID_CONVERT_OVERRIDE_PATH = Path("data", "shipid_overrides.json")
EQUIP_CONVERT_CACHE_PATH = Path("data", "equip_convert.json")
EQUIP_WIKIDATA_PATH = Path("data", "equip_wikinames.json")
SKIN_WIKIDATA_PATH = Path("data", "skin_wikidata.json")
ITEMNAME_OVERRIDES_PATH = Path("data", "item_name_convert.json")


rarityindex = {}
class Rarity(Enum):
	"""
	Enum class that allows conversion of rarity values between the game data and wiki.
	"""

	rarity: int
	"""Rarity id used in the game."""
	label: str
	"""Full rarity name used on the wiki."""
	letter: str
	"""Single letter used on the wiki in some templates."""

	def __new__(cls, rarity, label, letter):
		obj = object.__new__(cls)
		obj.rarity = rarity
		obj.label = label
		obj.letter = letter
		return obj

	NORMAL0		= (0,	"Normal",		"E")
	NORMAL		= (1,	"Normal",		"E")
	RARE		= (2,	"Rare",			"B")
	ELITE		= (3,	"Elite",		"P")
	SUPER_RARE	= (4,	"Super Rare",	"G")
	PRIORITY	= (4,	"Priority",		"G")
	ULTRA_RARE	= (5,	"Ultra Rare",	"R")
	LEGENDARY	= (5,	"Legendary",	"R")
	DECISIVE	= (5,	"Decisive",		"R")
	GIFT		= (8,	"Super Rare",	"G")
	GIFT2		= (9,	"Super Rare",	"G")

	@staticmethod
	def from_id(rarity_id: int, is_research: bool = False) -> "Rarity":
		"""
		Returns a rarity object with given *rarity_id*.
		Only returns the first one listed, as there are multiple with the same id.

		If *is_research* is set True, `Rarity.PRIORITY` and `Rarity.DECISIVE` will be prioritised.
		"""
		if is_research:
			if rarity := {4: Rarity.PRIORITY, 5: Rarity.DECISIVE}.get(rarity_id):
				return rarity
		return rarityindex.get(rarity_id)

def _fill_rarity_indexes():
	for rarity in Rarity:
		if rarity.rarity not in rarityindex:
			rarityindex[rarity.rarity] = rarity


nationindex = {}
# from /model/const/nation.lua#Nation2Name
class Nation(Enum):
	"""
	Enum class that allows conversion of nation values between the game data and wiki.
	"""

	id: int
	"""Nation id used in the game."""
	value: int
	"""Nation id used in the game."""
	label: str
	"""Name of the nation used on the wiki."""

	def __new__(cls, nation_id, label):
		obj = object.__new__(cls)
		obj._value_ = nation_id
		obj.label = label
		return obj

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
	META				= (97,	"META")
	UNIVERSAL2			= (98,	"Universal")
	NEPTUNIA			= (101,	"Neptunia")
	BILIBILI			= (102,	"Bilibili")
	UTAWARERUMONO		= (103,	"Utawarerumono")
	KIZUNA_AI			= (104,	"Kizuna AI")
	HOLOLIVE			= (105,	"Hololive")
	VENUS_VACATION		= (106,	"Venus Vacation")
	IDOLMASTER			= (107,	"The Idolmaster")
	SSSS				= (108,	"SSSS")

	@property
	def id(self):
		"""Nation id used in the game."""
		return self.value

	@staticmethod
	def from_id(nation_id: int) -> "Nation":
		"""
		Returns a nation object with given *nation_id*.
		"""
		return nationindex.get(nation_id)

def _fill_nation_indexes():
	for nation in Nation:
		nationindex[nation.value] = nation


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

	def __new__(cls, pos, param_name, template_name):
		obj = object.__new__(cls)
		obj.pos = pos
		obj.wiki_param_name = param_name
		obj.wiki_template_name = template_name
		return obj

	def __str__(self):
		return format(self._name_)

	DURABILITY		= (0,	"Health",		"Health")
	CANNON			= (1,	"Fire",			"Firepower")
	TORPEDO			= (2,	"Torp",			"Torpedo")
	ANTIAIRCRAFT	= (3,	"AA",			"AA")
	AIR				= (4,	"Air",			"Aviation")
	RELOAD			= (5,	"Reload",		"Reload")
	ARMOR			= (6,	"Armor_Debug",	"Armor")
	HIT				= (7,	"Acc",			"Accuracy")
	DODGE			= (8,	"Evade",		"Evasion")
	SPEED			= (9,	"Speed",		"Speed")
	LUCK			= (10,	"Luck",			"Luck")
	ANTISUB			= (11,	"ASW",			"ASW")


shiptypeindex = {}
shiptypeindex_name = {}
shiptypeindex_fullname = {}
# from /model/const/shiptype.lua
class ShipType(Enum):
	id: int
	typename: str
	categoryname: str
	templatename: str
	typetext: str

	def __new__(cls, typeid, typename, catname, templatename, typetext):
		obj = object.__new__(cls)
		obj.id = typeid
		obj.typename = typename
		obj.categoryname = catname
		obj.templatename = templatename
		obj.typetext = typetext
		return obj

	DD		= (1,	"Destroyer",				"Destroyers",					"DD",	"DD")
	CL		= (2,	"Light Cruiser",			"Light cruisers",				"CL",	"CL")
	CA		= (3,	"Heavy Cruiser",			"Heavy cruisers",				"CA",	"CA")
	BC		= (4,	"Battlecruiser",			"Battlecruisers",				"BC",	"BC")
	BB		= (5,	"Battleship",				"Battleships",					"BB",	"BB")
	CVL		= (6,	"Light Aircraft Carrier",	"Light aircraft carriers",		"CVL",	"CVL")
	CV		= (7,	"Aircraft Carrier",			"Aircraft carriers",			"CV",	"CV")
	SS		= (8,	"Submarine",				"Submarines",					"SS",	"SS")
	CAV		= (9,	"Aviation Cruiser",			"Aviation cruisers",			"CAV",	"CAV")
	BBV		= (10,	"Aviation Battleship",		"Aviation battleships",			"BBV",	"BBV")
	CT		= (11,	"Torpedo Cruiser",			"Torpedo cruisers",				"CT",	"CT")
	AR		= (12,	"Repair Ship",				"Repair ships",					"AR",	"AR")
	BM		= (13,	"Monitor",					"Monitors",						"BM",	"BM")
	SSV		= (17,	"Submarine Carrier",		"Submarine carriers",			"SSV",	"SSV")
	CB		= (18,	"Large Cruiser",			"Large cruisers",				"CB",	"CB")
	AE		= (19,	"Munition Ship",			"Munition ships",				"AE",	"AE")
	DDG_V	= (20,	"DDG",						"Guided-missile destroyers",	"DDG",	"DDG")
	DDG_M	= (21,	"DDG",						"Guided-missile destroyers",	"DDG",	"DDG")
	ZHAN	= (-1,	"",							"",								"BC",	"BC or BB")
	HANG	= (-1,	"",							"",								"CVL",	"CV or CVL")
	QIAN	= (-1,	"",							"",								"SS",	"SS or SSV")
	ZHONG	= (-1,	"",							"",								"CB",	"CB or CA")
	FANQIAN	= (-1,	"",							"",								"DD",	"DD or DDG or CL")
	QUZHU	= (-1,	"",							"",								"DD",	"DD or DDG")

	@staticmethod
	def from_id(type_id: int) -> 'ShipType':
		return shiptypeindex.get(type_id)

	@staticmethod
	def from_type(type_name: str) -> 'ShipType':
		return shiptypeindex_name[type_name.lower()]

	@staticmethod
	def from_name(type_name: str) -> 'ShipType':
		return shiptypeindex_fullname[type_name.lower()]

def _fill_shiptype_indexes():
	for shiptype in ShipType:
		shiptypeindex_name[shiptype.name.lower()] = shiptype

		if shiptype.id != -1:
			shiptypeindex[shiptype.id] = shiptype
			shiptypeindex_fullname[shiptype.typename.lower()] = shiptype


armorindex_id = {}
armorindex_label = {}
class Armor(Enum):
	label: str

	def __new__(cls, armor_id, label):
		obj = object.__new__(cls)
		obj._value_ = armor_id
		obj.label = label
		return obj

	LIGHT	= (1,	"Light")
	MEDIUM	= (2,	"Medium")
	HEAVY	= (3,	"Heavy")

	@staticmethod
	def from_id(armor_id: int) -> 'Armor':
		return armorindex_id.get(armor_id)

	@classmethod
	def from_label(cls, armor_label: str) -> 'Armor':
		return armorindex_label.get(armor_label)

def _fill_armor_indexes():
	for armor in Armor:
		armorindex_id[armor.value] = armor
		armorindex_label[armor.label] = armor


def _fill_all_indexes():
	_fill_rarity_indexes()
	_fill_nation_indexes()
	_fill_shiptype_indexes()
	_fill_armor_indexes()

_fill_all_indexes()
