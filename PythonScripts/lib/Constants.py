from pathlib import Path
from enum import Enum


# Constant Filepaths
JSON_SOURCE_PATH = Path("..", "SrcJson3").resolve()
SHIPID_CONVERT_CACHE_PATH = Path("data", "shipid_convert.json")
SHIPID_CONVERT_OVERRIDE_PATH = Path("data", "shipid_overrides.json")
EQUIP_CONVERT_CACHE_PATH = Path("data", "equip_convert.json")
EQUIP_WIKIDATA_PATH = Path("data", "equip_wikinames.json")
ITEMNAME_OVERRIDES_PATH = Path("data", "item_name_convert.json")


rarityindex = {}
class Rarity(Enum):
	rarity: int
	label: str
	letter: str

	def __new__(cls, rarity, label, letter):
		obj = object.__new__(cls)
		obj.rarity = rarity
		obj.label = label
		obj.letter = letter
		return obj

	NORMAL0 = (0, "Normal", "E")
	NORMAL = (1, "Normal", "E")
	RARE = (2, "Rare", "B")
	ELITE = (3, "Elite", "P")
	SUPER_RARE = (4, "Super Rare", "G")
	PRIORITY = (4, "Priority", "G")
	ULTRA_RARE = (5, "Ultra Rare", "R")
	LEGENDARY = (5, "Legendary", "R")
	DECISIVE = (5, "Decisive", "R")
	GIFT = (8, "Super Rare", "G")
	GIFT2 = (9, "Super Rare", "G")

	@staticmethod
	def from_id(rarity_id) -> 'Rarity':
		if not rarityindex:
			# fill rarityindex
			for rarity in Rarity:
				if rarity.rarity not in rarityindex:
					rarityindex[rarity.rarity] = rarity
		return rarityindex.get(rarity_id)

	@staticmethod
	def from_id_adv(rarity_id, is_research) -> 'Rarity':
		if is_research:
			return {4: Rarity.PRIORITY, 5: Rarity.DECISIVE}.get(rarity_id)
		return Rarity.from_id(rarity_id)

# from /model/const/nation.lua#Nation2Name
nationindex = {}
class Nation(Enum):
	label: str

	def __new__(cls, nation_id, label):
		obj = object.__new__(cls)
		obj._value_ = nation_id
		obj.label = label
		return obj

	UNIVERSAL = (0, "Universal")
	EAGLE_UNION = (1, "Eagle Union")
	ROYAL_NAVY = (2, "Royal Navy")
	SAKURA_EMPIRE = (3, "Sakura Empire")
	IRON_BLOOD = (4, "Iron Blood")
	EASTERN_RADIANCE = (5, "Eastern Radiance")
	SARDEGNA_EMPIRE = (6, "Sardegna Empire")
	NORTH_UNION = (7, "North Union")
	IRIS_LIBRE = (8, "Iris Libre")
	VICHYA_DOMINION = (9, "Vichya Dominion")
	META = (97, "META")
	UNIVERSAL2 = (98, "Universal")
	NEPTUNIA = (101, "Neptunia")
	BILIBILI = (102, "Bilibili")
	UTAWARERUMONO = (103, "Utawarerumono")
	KIZUNA_AI = (104, "Kizuna AI")
	HOLOLIVE = (105, "Hololive")
	VENUS_VACATION = (106, "Venus Vacation")
	IDOLMASTER = (107, 'The Idolmaster')
	SSSS = (108, 'SSSS')

	@staticmethod
	def from_id(nation_id: int) -> 'Nation':
		if not nationindex:
			# fill nationindex
			for nation in Nation:
				nationindex[nation.value] = nation
		return nationindex.get(nation_id)


class Attribute(Enum):
	pos: int
	wiki_param_name: str
	wiki_template_name: str

	def __new__(cls, pos, param_name, template_name):
		obj = object.__new__(cls)
		obj.pos = pos
		obj.wiki_param_name = param_name
		obj.wiki_template_name = template_name
		return obj

	DURABILITY = (0, "Health", "Health")
	CANNON = (1, "Fire", "Firepower")
	TORPEDO = (2, "Torp", "Torpedo")
	ANTIAIRCRAFT = (3, "AA", "AA")
	AIR = (4, "Air", "Aviation")
	RELOAD = (5, "Reload", "Reload")
	ARMOR = (6, "Armor_Debug", "Armor")
	HIT = (7, "Acc", "Accuracy")
	DODGE = (8, "Evade", "Evasion")
	SPEED = (9, "Speed", "Speed")
	LUCK = (10, "Luck", "Luck")
	ANTISUB = (11, "ASW", "ASW")


shiptypeindex = {}
shiptypeindex_name = {}
shiptypeindex_fullname = {}
class ShipType(Enum):
	id: int
	typename: str
	categoryname: str
	templatename: str

	def __new__(cls, typeid, typename, catname, templatename):
		obj = object.__new__(cls)
		obj.id = typeid
		obj.typename = typename
		obj.categoryname = catname
		obj.templatename = templatename
		return obj

	DD = (1, "Destroyer", "Destroyers","DD")
	CL = (2, "Light Cruiser", "Light cruisers", "CL")
	CA = (3, "Heavy Cruiser", "Heavy cruisers", "CA")
	BC = (4, "Battlecruiser", "Battlecruisers", "BC")
	BB = (5, "Battleship", "Battleships", "BB")
	CVL = (6, "Light Aircraft Carrier", "Light aircraft carriers", "CVL")
	CV = (7, "Aircraft Carrier", "Aircraft carriers", "CV")
	SS = (8, "Submarine", "Submarines", "SS")
	CAV = (9, "Aviation Cruiser", "Aviation cruisers", "CAV")
	BBV = (10, "Aviation Battleship", "Aviation battleships", "BBV")
	CT = (11, "Torpedo Cruiser", "Torpedo cruisers", "CT")
	AR = (12, "Repair Ship", "Repair ships", "AR")
	BM = (13, "Monitor", "Monitors", "BM")
	SSV = (17, "Submarine Carrier", "Submarine carriers", "SSV")
	CB = (18, "Large Cruiser", "Large cruisers", "CB")
	AE = (19, "Munition Ship", "Munition ships", "AE")
	DDG_V = (20, "DDG", "Guided-missile destroyers", "DDG")
	DDG_M = (21, "DDG", "Guided-missile destroyers", "DDG")
	ZHAN = (-1, "", "", "BC")
	HANG = (-1, "", "", "CVL")
	QIAN = (-1, "", "", "SS")
	ZHONG = (-1, "", "", "CB")
	FANQIAN = (-1, "", "", "DD")

	@staticmethod
	def from_id(type_id: int) -> 'ShipType':
		if not shiptypeindex:
			# fill shiptypeindex
			for shiptype in ShipType:
				if shiptype.id == -1:
					continue
				shiptypeindex[shiptype.id] = shiptype
		return shiptypeindex.get(type_id)

	@staticmethod
	def from_type(type_name: str) -> 'ShipType':
		if not shiptypeindex_name:
			# fill shiptypeindex
			for shiptype in ShipType:
				shiptypeindex_name[shiptype.name.lower()] = shiptype
		return shiptypeindex_name[type_name.lower()]

	@staticmethod
	def from_name(type_name: str) -> 'ShipType':
		if not shiptypeindex_fullname:
			# fill shiptypeindex
			for shiptype in ShipType:
				shiptypeindex_fullname[shiptype.typename.lower()] = shiptype
		return shiptypeindex_fullname[type_name.lower()]


armorindex = {}
class Armor(Enum):
	label: str

	def __new__(cls, armor_id, label):
		obj = object.__new__(cls)
		obj._value_ = armor_id
		obj.label = label
		return obj

	LIGHT = (1, "Light")
	MEDIUM = (2, "Medium")
	HEAVY = (3, "Heavy")

	@staticmethod
	def from_id(armor_id: int) -> 'Armor':
		if not armorindex:
			# fill nationindex
			for armor in Armor:
				armorindex[armor.value] = armor
		return armorindex.get(armor_id)
