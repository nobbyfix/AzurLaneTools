import re
import math
from collections import Counter
from collections.abc import Iterable
from argparse import ArgumentParser
from itertools import chain

from lib import ALJsonAPI, Client, Utility, WikiHelper, Constants
from lib.apiclasses import Award, CachedAPILoader, ShipReward, Task


TIER_EQUIP_NAME = re.compile(r"^(T[0-9]\s).*")
DESIGN_EQUIP_NAME = re.compile(r".*(\s(T[0-9]\s)Design)")

property_limit_text = {
	"level" : "Average Level",
	"durability": "{{Health}} Total HP",
	"cannon": "{{Firepower}} Total Firepower",
	"torpedo": "{{Torpedo}} Total Torpedo",
	"antiaircraft": "{{AA}} Total Anti-Air",
	"air": "{{Aviation}} Total Aviation",
	"antisub": "{{ASW}} Total ASW",
	"dodge": "{{Evasion}} Total Evasion",
	"reload": "{{Reload}} Total Reload",
}

property_limit_sign = {
	-1: "<",
	0: "=",
	1: ">",
}

# "model/const/chapterconst.lua" with slot0.AttachX
node_type_letter = {
	-1: "x", # land
	0: " ", # water
	1: "s", # start
	2: "q", # question
	3: "a", # ammo
	4: "c", # combat
	5: "ambush", # ambush
	6: "e", # enemy
	7: "m", # matime_escort: mine
	8: "b", # boss
	9: "story", # story
	11: "areaboss", # areaboss
	12: "p", # siren (champion)
	14: "torpedofleet", # torpedo-fleet
	15: "sirenpatrol", # siren (champion)-patrol
	16: "u", # submarine
	17: "f", # matime_escort: transport
	18: "d", # matime_escort: transport_target
	19: "siren-submarine", # siren (champion)-submarine
	20: "oni", # oni
	21: "oni-target", # oni-target
	24: "bomb-enemy", # bomb-enemy
	25: "barrier", # barrier
	26: "huge supply", # huge supply
	100: "h", # harbour
}

drop_const = {
	"bp": {
		54041: "{{Blueprint|T2|Destroyer}} T1-T2 Destroyer Retrofit Blueprint",
		54042: "{{Blueprint|T2|Cruiser}} T1-T2 Cruiser Retrofit Blueprint",
		54043: "{{Blueprint|T2|Battleship}} T1-T2 Battleship Retrofit Blueprint",
		54044: "{{Blueprint|T2|Carrier}} T1-T2 Carrier Retrofit Blueprint",
		54045: "{{Blueprint|T3|Destroyer}} T1-T3 Destroyer Retrofit Blueprint",
		54046: "{{Blueprint|T3|Cruiser}} T1-T3 Cruiser Retrofit Blueprint",
		54047: "{{Blueprint|T3|Battleship}} T1-T3 Battleship Retrofit Blueprint",
		54048: "{{Blueprint|T3|Carrier}} T1-T3 Carrier Retrofit Blueprint",
	},
	"coredata": { 59900: "{{Core data}} Core Data", },
	"part": {
		54011: "{{Plate|T1}} T1 Upgrade Parts",
		54012: "{{Plate|T2}} T1-T2 Upgrade Parts",
		54013: "{{Plate|T3}} T1-T3 Upgrade Parts",
		54017: "{{Plate|T3}} T2-T3 Upgrade Parts",
	},
	"box": {
		54021: "{{Box|T1}} T1 Tech Boxes",
		54022: "{{Box|T2}} T1-T2 Tech Boxes",
		54023: "{{Box|T3}} T1-T3 Tech Boxes",
		54024: "{{Box|T4}} T1-T4 Tech Boxes",
	},
	"coins": { 59001: "{{Coin}} Coins", },
}

# for star strings, see "model/const/chapterconst.lua#GetAchieveDesc"
star_strings = {
	1: "Defeat flagship",
	2: "Defeat {} escort fleets",
	3: "Defeat all enemies",
	4: "Deployed ships ≤ {}",
	#5: "%s not deployed",
	6: "Clear with a Full Combo",
}


def flatten(*args) -> Iterable:
	iterables = []
	for arg in args:
		if isinstance(arg, Iterable):
			iterables.extend(arg)
		else:
			iterables.append(arg)
	return iterables


def find_chapter_tasks(chapterid: int, api: ALJsonAPI, client: Client) -> tuple[Task, Task]:
	"""
	:return: Returns a tuple of format (<cleartask>, <threestartask>)
	"""
	clear_task = None
	threestar_task = None

	task_data_template = api.get_sharecfgmodule("task_data_template")
	for task in task_data_template.all_client(client):
		taskid_it = flatten(task.target_id)
		if chapterid in taskid_it:
			if task.sub_type == 1020: clear_task = task
			elif task.sub_type == 1021: threestar_task = task
			# break loop if both tasks are already found
			if clear_task and threestar_task:
				break
	return clear_task, threestar_task


def get_task_awards(task: Task, api: ALJsonAPI, client: Client, wikifier: WikiHelper.Wikifier) -> str:
	award_output = []
	for award in task.awards:
		awardable = award.load(api, client)

		wiki_awardable = wikifier.wikify_awardable(awardable)
		outicon = wiki_awardable.icontemplate or WikiHelper.put_icon(filename=wiki_awardable.filelink+".png",
			itemname=wiki_awardable.name, nolink=True)
		outname = wiki_awardable.name
		if isinstance(awardable, ShipReward):
			outname = f"[[{outname}]]"
		award_output.append(f"{award.amount}x {outname} {outicon}")
	return ", ".join(award_output)


class EnemyNameLoader(CachedAPILoader):
	def _generate_cache(self) -> None:
		enemy_data_statistics = self._api.get_sharecfgmodule("enemy_data_statistics")
		for entry in enemy_data_statistics.all_client(Client.EN):
			if "icon" in entry:
				priority = False
				if entry_prev := self._cache.get(entry.icon):
					entry_prev, priority = entry_prev
				
				if not priority:
					if "name" in entry:
						self._cache[entry.icon] = (entry, entry.name in self._api.ship_converter.ship_to_id)
					else:
						if entry_prev:
							self._cache[entry.icon] = (entry_prev, False)
						else:
							self._cache[entry.icon] = (entry, False)
	
	def name_from_icon(self, icon: str) -> str:
		if entry := self._cache.get(icon):
			entry, priority = entry
			name = entry.get("name") or entry.prefab
			if priority:
				name = "[["+ name + "]]"

			if "type" in entry:
				return name + " {{" + Constants.ShipType.from_id(entry.type).templatename + "}}"

			return name
		return icon	


def star_requirement(num: int, value: int | None = None) -> str:
	if num == 0:
		return

	star_text = star_strings[num]
	if num in [2, 4]:
		return star_text.format(value)
	return star_text

def fleet_retriction(fleet_limit: list[list[Constants.ShipType | int]]) -> str:
	countedtypes = Counter(chain(*fleet_limit))
	types_str = []
	for shiptype, amount in countedtypes.items():
		if shiptype == 0: continue
		types_str.append(f"{amount} {{{{{shiptype.templatename}}}}} {shiptype.typetext}")
	return ", ".join(types_str)


def get_chapter(chapterid: int, api: ALJsonAPI, client: Client) -> str:
	wikifier = WikiHelper.Wikifier(api)
	chapter_template = api.get_sharecfgmodule("chapter_template")
	chapter = chapter_template.load_client(chapterid, client)

	### set default chapter info
	chapter_wiki_template = {}
	chapter_wiki_template["ctID"] = chapter.id
	chapter_wiki_template["ID"] = chapter.chapter_name
	chapter_wiki_template["Title"] = chapter.name
	chapter_wiki_template["Introduction"] = api.replace_namecode(chapter.profiles, client)

	### unlock condition
	unlock_require = []
	map_require = []
	if unlocklevel := chapter.unlocklevel:
		unlock_require.append("Commander Lv. " + str(unlocklevel))
	for previous_chapter_entry in chapter.previous_chapter:
		pre_chapter = previous_chapter_entry.load(api, client)
		pre_chapter_name = pre_chapter.chapter_name
		map_require.append(f"[[#{pre_chapter_name}|{pre_chapter_name}]]")
	if len(map_require) == 1:
		unlock_require.append(f"Clear {map_require[0]}")
	elif len(map_require) > 1:
		unlock_require.append("Clear either " + " or ".join(map_require))
	chapter_wiki_template["Requirements"] = " and ".join(unlock_require)

	### associated tasks
	clear_task, threestar_task = find_chapter_tasks(chapterid, api, client)
	if clear_task: chapter_wiki_template["ClearReward"] = get_task_awards(clear_task, api, client, wikifier)
	if threestar_task: chapter_wiki_template["3StarReward"] = get_task_awards(threestar_task, api, client, wikifier)

	### normal and elite mob info
	exp = [ -1, -1, -1 ]
	level = [ 9999, -1 ]
	for enemyref in chain(chapter.mob_list, chapter.elite_list):
		enemy = enemyref.load(api, client)
		# small fleets are type 1, 4, 7
		# medium fleets are type 2, 5, 8
		# large fleets are type 3, 6, 9
		# cargo fleets are type 10
		# skip all other types for now
		if not 1 <= enemy.type <= 10: continue
		exp[(enemy.type-1)%3] = enemy.exp
		if enemy.level < level[0]: level[0] = enemy.level
		if enemy.level > level[1]: level[1] = enemy.level

	# set template params for normal mob fleet xp and level
	if level[0] == level[1]:
		chapter_wiki_template["MobLevel"] = level[0]
	elif level[0] != 9999 and level[1] != -1:
		chapter_wiki_template["MobLevel"] = f"{level[0]}-{level[1]}"
	for i, xpval in enumerate(exp):
		if xpval != -1:
			chapter_wiki_template[f"MobExp{i+1}"] = exp[i]

	# add mob spawn order
	if chapter.mob_list:
		chapter_wiki_template["MobSpawnOrder"] = ",".join([str(el) for el in chapter.mob_spawn_pattern])
	if chapter.elite_list:
		chapter_wiki_template["EliteSpawnOrder"] = ",".join([str(el) for el in chapter.elite_spawn_pattern])

	### siren mob info
	if chapter.siren_list:
		# get siren xp and level values
		exp = -1
		level = [ 9999, -1 ]
		for enemyref in chapter.siren_list:
			if enemyref.id in [0, 1]: continue
			# if enemyref.id == 1: continue # possibly needed, from legacy code
			enemy = enemyref.load(api, client)
			if enemy.exp > exp: exp = enemy.exp
			if enemy.level < level[0]: level[0] = enemy.level
			if enemy.level > level[1]: level[1] = enemy.level

		# add xp and level values and spawn order to template data
		if level[0] == level[1]:
			chapter_wiki_template["SirenLevel"] = level[0]
		elif level[0] != 9999 and level[1] != -1:
			chapter_wiki_template["SirenLevel"] = f"{level[0]}-{level[1]}"
		if exp != -1:
			chapter_wiki_template["MobExpSiren"] = exp
		chapter_wiki_template["SirenSpawnOrder"] = ",".join([str(el) for el in chapter.siren_spawn_pattern])

	### boss info
	enemynameloader = EnemyNameLoader(api)
	if chapter.boss and chapter.boss.id != 0:
		boss_enemy = chapter.boss.load(api, client)
		#bossicons = set(chapter.icon).union(set(boss_enemy.icons))
		chapter_wiki_template["Boss"] = " and ".join([enemynameloader.name_from_icon(icon) for icon in chapter.icon])
		chapter_wiki_template["BossLevel"] = boss_enemy.level
		chapter_wiki_template["BossExp"] = boss_enemy.exp
	chapter_wiki_template["BossBattleReq"] = chapter.boss_refresh or "0"
	chapter_wiki_template["BossBattleClear"] = math.ceil(100/(chapter.progress_boss or 1))

	# other general chapter info
	chapter_wiki_template["AvoidRequire"] = chapter.avoid_require
	chapter_wiki_template["Star1"] = star_requirement(chapter.star_require_1, chapter.num_1)
	chapter_wiki_template["Star2"] = star_requirement(chapter.star_require_2, chapter.num_2)
	chapter_wiki_template["Star3"] = star_requirement(chapter.star_require_3, chapter.num_3)
	chapter_wiki_template["SuggestedAirSupremacy"] = chapter.best_air_dominance
	chapter_wiki_template["ActualAirSupremacy"] = chapter.air_dominance

	if chapter.use_oil_limit:
		chapter_wiki_template["OilCapMob"] = chapter.use_oil_limit[0]
		chapter_wiki_template["OilCapBoss"] = chapter.use_oil_limit[1]
		chapter_wiki_template["OilCapSub"] = chapter.use_oil_limit[2]

	### hard mode info
	if chapter.type == 2:
		# fleet type limitations
		for i in range(max(2, len(chapter.fleet_limitation))):
			if len(chapter.fleet_limitation) > i:
				chapter_wiki_template[f"Fleet{i+1}"] = fleet_retriction(chapter.fleet_limitation[i])
			else:
				chapter_wiki_template[f"Fleet{i+1}"] = "Not available"

		# stat restrictions
		stat_strs = []
		for ltype, lsign, lamount in chapter.property_limitation:
			stat_strs.append(f"{property_limit_text[ltype]} {property_limit_sign[lsign]} {lamount}")
		chapter_wiki_template["StatRestrictions"] = ", ".join(stat_strs)

	### Nodemap
	nodemap = ""
	current_row = -1
	for row, _, access, nodetype in chapter.get("grids"):
		if row == current_row:
			nodemap = "|"+nodemap
		else:
			if nodemap: nodemap = "\n	|" + nodemap
			current_row = row
		if not access: nodetype = -1
		nodemap = node_type_letter[nodetype] + nodemap
	chapter_wiki_template["NodeMap"] = "{{MapTable\n	|"+nodemap+"\n  }}"

	### drops
	shipdrops = [""]
	equipdrops = [""]
	map_drop_output_list = {"other": []}

	for award in chapter.awards:
		award = award.load(api, client)

		# ship drops
		if award.icon == "Props/54000":
			shipdrop_awards = award["display_icon"]
			for shipdrop_award in shipdrop_awards:
				shipdrop = Award(*shipdrop_award).load(api, client)
				shipdrop_wiki = wikifier.wikify_awardable(shipdrop)
				dropicon = WikiHelper.simple_template("IconHover", [shipdrop_wiki.name, shipdrop_wiki.rarity.rarity+1])
				shipdrops.append(dropicon)

		# equipment drops
		elif award.icon == "Props/55000":
			equipdrop_awards = award["display_icon"]
			for equipdrop_award in equipdrop_awards:
				equipdrop = Award(*equipdrop_award).load(api, client)
				equipdrop_wiki = wikifier.wikify_awardable(equipdrop)

				if m := TIER_EQUIP_NAME.match(equipdrop.name):
					equipdrop_name = m.group(1) + equipdrop_wiki.name
				elif m := DESIGN_EQUIP_NAME.match(equipdrop.name):
					equipdrop_name = m.group(2) + equipdrop_wiki.name.replace(m.group(1), "")
				else:
					equipdrop_name = equipdrop_wiki.name

				dropicon = WikiHelper.simple_template("EquipmentBox", [equipdrop_wiki.rarity.rarity+1,
					equipdrop_name, equipdrop_wiki.link, equipdrop_wiki.icon])
				equipdrops.append(dropicon)

		# other map drops
		else:
			isSpecialDrop = False
			for drop_key, key_dict in drop_const.items():
				if award.id in key_dict:
					isSpecialDrop = True
					map_drop_output_list[drop_key] = key_dict[award.id]
					break
			if not isSpecialDrop:
				map_drop_output_list["other"].append(award.name)

	map_drop_output = ""
	for drop_key in drop_const:
		if drop_key in map_drop_output_list:
			if map_drop_output: map_drop_output += ", "
			map_drop_output += map_drop_output_list[drop_key]

	chapter_wiki_template["ShipDrops"] = "\n".join(shipdrops)
	chapter_wiki_template["EquipmentDrops"] = "\n".join(equipdrops)
	chapter_wiki_template["MapDrops"] = map_drop_output
	return chapter_wiki_template


def main():
	parser = ArgumentParser()
	parser.add_argument("-c", "--client", required=True, choices=Client.__members__,
						help="client to gather information from")
	mapgroup = parser.add_mutually_exclusive_group(required=True)
	mapgroup.add_argument("-m", "--mapids", metavar="MAPID", type=int, nargs='+',
						help="indexes from sharecfg/chapter_template")
	mapgroup.add_argument("-e", "--eventid", type=int, nargs=1,
						help="index prefix from sharecfg/chapter_template for events")
	parser.add_argument("--mult", "--multiplier", type=int, nargs='?', default=10000,
						help="multiplier of the event id index prefix")
	args = parser.parse_args()

	client = Client[args.client]
	api = ALJsonAPI()

	if args.mapids:
		mapids = args.mapids
	elif args.eventid:
		eventid = args.eventid[0] * args.mult
		chapter_template = api.get_sharecfgmodule("chapter_template")
		ids = chapter_template.all_client_ids(client)
		mapids = filter(lambda mapid: 0 < (int(mapid) - eventid) < 100, ids)

	template_map = WikiHelper.MultilineTemplate("Map")
	mapstrings = []
	for mapid in sorted(mapids):
		mapdata = get_chapter(mapid, api, client)
		mapstrings.append( mapdata["ID"] + "=" + template_map.fill(mapdata) )

	wikitext = "<tabber>\n" + "\n|-|\n".join(mapstrings) + "\n</tabber>"
	Utility.output(wikitext)

if __name__ == "__main__":
	main()
