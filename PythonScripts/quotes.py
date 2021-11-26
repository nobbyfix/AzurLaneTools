import re
import enum
from typing import Union
import mwparserfromhell
from dataclasses import dataclass
from collections import Counter

import _add_valentine
from lib import DEFAULT_CLIENTS, Client, ALJsonAPI, WikiHelper, Constants, Utility
from lib.Utility import rreplace


VOICE_TYPE_CONVERT = {
	'skill': 'SkillActivation',
	#'main': 'SecretaryIdle', // needs custom implementation
	'feeling1': 'AffinityDisappointed',
	'feeling2': 'AffinityStranger',
	'feeling3': 'AffinityFriendly',
	'feeling4': 'AffinityLike',
	'feeling5': 'AffinityLove',
	'touch': 'SecretaryTouch',
	'battle': 'MissionStart',
	'drop_descrip': 'ShipDescription',
	'mail': 'Mail',
	'propose': 'Pledge',
	'lose': 'Defeat',
	'hp_warning': 'LowHP',
	'detail': 'Details',
	'win_mvp': 'MVP',
	'touch2': 'SpecialTouch',
	'headtouch': 'Headpat',
	'mission': 'Task',
	'mission_complete': 'TaskComplete',
	'home': 'MissionFinished',
	'login': 'Login',
	'unlock': 'Acquisition',
	'upgrade': 'Strengthening',
	'profile': 'SelfIntro',
	#'vote': '', //Doesn't seen to be used
	'expedition': 'Commission',
	#'couple_encourage': 'Additional' // needs custom implementation
}

# tabber tab names
TAB_NAMES = {
	Client.CN: 'Chinese Server',
	Client.JP: 'Japanese Server',
	Client.EN: 'English Server'
}


class QuoteType(enum.Enum):
	BASE = enum.auto()
	POST_OATH = enum.auto()
	MAX_AFFECTION = enum.auto()

	@property
	def skinname_suffix(self):
		if self == QuoteType.POST_OATH:
			return "(EXTRA: Post-Oath)"
		if self == QuoteType.MAX_AFFECTION:
			return "(EXTRA: 100+ Affection)"
		return ""

	def skin_type(self, skinid: int):
		if self == QuoteType.BASE:
			if skinid == 0:
				return ""
			return f"Skin{skinid}"
		if self in [QuoteType.POST_OATH, QuoteType.MAX_AFFECTION]:
			if skinid == 0: return "BasePostPledge"
			return f"Skin{skinid}PostPledge"
		raise NotImplementedError(f'Unknown combination of QuoteType ({self.name}) and SkinID ({skinid}).')

@dataclass
class SkinQuotes:
	lines: dict
	display_name: str
	quote_type: QuoteType


COLORTAG_START = re.compile(r'<color=#(\w+)>')
def clean_value(v: str) -> str:
	v = v.strip()
	if v.startswith('*'): v = v.replace('*', '<nowiki/>*', 1)
	elif v.startswith('#'): v = v.replace('#', '<nowiki/>*', 1)
	if '\n' in v: v = v.replace('\n', '<br>')
	if v.endswith(',0'): v = v.replace(',0', '')

	# remove color tags
	if '</color>' in v: v = v.replace('</color>', '')
	v = COLORTAG_START.sub('', v)
	return v


# initialize API, sharecfg data, wiki interface and templates
api = ALJsonAPI()
ship_skin_words = api.get_sharecfgmodule("ship_skin_words")
ship_skin_words_extra = api.get_sharecfgmodule("ship_skin_words_extra")
ship_skin_template = api.get_sharecfgmodule("ship_skin_template")
ShipConverter = api.ship_converter
wikiclient = WikiHelper.WikiClient().login()
template_general = WikiHelper.MultilineTemplate('ShipQuote')
template_en = WikiHelper.MultilineTemplate('ShipQuoteEN')

valentine20, valentine21 = _add_valentine.main(api)

# get all skinids from all versions
skinids = dict()
for client in Client:
	for groupid, shipskinids in ship_skin_template._load("get_id_list_by_ship_group", client).items():
		if groupid in skinids:
			skinids[groupid].update(shipskinids)
		else:
			skinids[groupid] = set(shipskinids)


def full_clean_value(client: Client, value: str) -> str:
	value = clean_value(value)
	return api.replace_namecode(value, client)

def format_or_list(values: list) -> str:
	s = ", ".join(values)
	return rreplace(s, ",", " or", 1)



def getGameQuoteSingleBase(client: Client, fullid: Union[int, str]) -> SkinQuotes:
	"""Returns a dict containing ALL quotes of a single skin.
	The keys are named after parameters complying with Template:ShipQuote for easy convertability.
	"""
	skinquotes = dict()
	quotes_data = ship_skin_words.load_client(fullid, client)
	if not quotes_data: return

	# fetch skinname from single_id or ship_skin_template
	if fullid % 10 == 0: skinname = 'Default Skin'
	elif fullid % 10 == 9: skinname = 'Retrofit Skin'
	else:
		skin_data = ship_skin_template.load_client(fullid, client)
		if skin_data:
			skinname = api.replace_namecode(skin_data.name, client)
		if not client == Client.EN:
			if skin_data_en := ship_skin_template.load_client(fullid, Client.EN):
				skinname_en = api.replace_namecode(skin_data_en.name, Client.EN)
				skinname += ' / '+skinname_en

	# get normal voice lines
	for voice_key in VOICE_TYPE_CONVERT:
		line = quotes_data.get(voice_key)
		if not line: continue
		template_param = VOICE_TYPE_CONVERT[voice_key]
		skinquotes[template_param] = full_clean_value(client, line)

	# get secretary idle lines
	secidles = quotes_data.main.split('|')
	for i, line in enumerate(secidles):
		if (not line) or (line == 'nil'): continue
		skinquotes[f'SecretaryIdle{i+1}'] = full_clean_value(client, line)

	# get additional lines
	additionals = quotes_data.couple_encourage
	if additionals != '0' and not isinstance(additionals, str):
		for i, additional in enumerate(additionals):
			if len(additional) != 4:
				print(f"Add {i}, {fullid}, {client.name}: Wrong formatting.")
				continue
			sortie_with, min_amount, line, quote_type = additional
			line = full_clean_value(client, line)

			sortie_with_str = ''
			if quote_type == 0: # shiplist
				shipnames = []
				for groupid in sortie_with:
					shipname = ShipConverter.convert(groupid)
					if shipname:
						shipnames.append(shipname)
					else:
						print(f"Add {i}, {fullid}, {client.name}: Wrong groupid {groupid}.")
				if min_amount < len(shipnames): sortie_with_str = f'at least {min_amount} of: '
				sortie_with_str += ', '.join([shipname for shipname in shipnames if shipname is not None])
			
			elif quote_type == 1: # shiptype
				shiptypes = []
				for shiptypeid in sortie_with:
					if shiptype := Constants.ShipType.from_id(shiptypeid):
						shiptypes.append(shiptype.typename+('s' if min_amount > 1 else ''))
					else:
						print(f"Add {i}, {fullid}, {client.name}: Wrong shiptypeid {shiptypeid}.")
				sortie_with_str = f'at least {min_amount} other '+format_or_list(shiptypes)

			elif quote_type == 2: # rarity
				shiprarities = []
				for rarityid in sortie_with:
					if rarity := Constants.Rarity.from_id(rarityid):
						shiprarities.append(rarity.label)
					else:
						print(f"Add {i}, {fullid}, {client.name}: Wrong rarityid {rarityid}.")
				sortie_with_str = f'at least {min_amount} ' + format_or_list(shiprarities) + ' ships'

			elif quote_type == 3: # nation
				shipnations = []
				for nationid in sortie_with:
					if nation := Constants.Nation.from_id(nationid):
						shipnations.append(nation.label)
					else:
						print(f"Add {i}, {fullid}, {client.name}: Wrong nationid {nationid}.")
				sortie_with_str = f'at least {min_amount} ' + format_or_list(shipnations) + ' ships'

			elif quote_type == 4: # artist
				sortie_with_str = f'at least {min_amount} other ships designed by the same [[Artists|artist]]'

			else:
				raise ValueError(f"Add {i}, {fullid}, {client.name}: Unknown additional type {quote_type}.")

			skinquotes[f'Additional{i+1}'] = f'(Sortie with {sortie_with_str}) {line}'

	return SkinQuotes(skinquotes, skinname, QuoteType.BASE)

def getGameQuoteSingleEX(client: Client, fullid: Union[int, str]) -> SkinQuotes:
	"""Returns a dict containing ALL quotes of a single EXTRA skin.
	The keys are named after parameters complying with Template:ShipQuote for easy convertability.
	"""
	skinquotes = dict()
	quotes_data = ship_skin_words_extra.load_client(fullid, client)
	if not quotes_data: return

	# get normal voice lines
	for voice_key in VOICE_TYPE_CONVERT:
		linedata = quotes_data.get(voice_key)
		if not linedata: continue
		line = linedata[0][1]
		template_param = VOICE_TYPE_CONVERT[voice_key]
		skinquotes[template_param] = full_clean_value(client, line)

	# get secretary idle lines
	if secidledata := quotes_data.main:
		secidles = secidledata[0][1].split('|')
		for i, line in enumerate(secidles):
			if (not line) or (line == 'nil'): continue
			skinquotes['SecretaryIdle'+str(i+1)] = full_clean_value(client, line)
	
	affection_counter = []
	for linedata in quotes_data._json.values():
		if not linedata: continue
		if isinstance(linedata, (str, int)): continue
		affection_counter.append(linedata[0][0])

	counter_result = Counter(affection_counter).most_common()
	if counter_result[0][0] == 100:
		quote_type = QuoteType.MAX_AFFECTION
	elif counter_result[0][0] == 1100:
		quote_type = QuoteType.POST_OATH
	else: raise NotImplementedError(f'Unknown affection value {counter_result[0][0]}.')
	return SkinQuotes(skinquotes, '', quote_type)

def getGameQuoteSingle(client: Client, fullid: Union[int, str]) -> dict[QuoteType, SkinQuotes]:
	result = {}
	if basequotes := getGameQuoteSingleBase(client, fullid):
		result[basequotes.quote_type] = basequotes
	if ex_quotes := getGameQuoteSingleEX(client, fullid):
		if basequotes:
			ex_quotes.display_name = " ".join([basequotes.display_name, ex_quotes.quote_type.skinname_suffix])
		result[ex_quotes.quote_type] = ex_quotes
	return result

def getGameQuoteData(client: Client, groupid: int) -> dict:
	"""Returns a dict containing ALL quotes of all skins of a given ship.
	The keys are named after parameters complying with Template:ShipQuote for easy convertability.
	"""
	total_add_ids = 0
	quotes = dict()
	for skinid in skinids[str(groupid)]: # iterate through all skinids of current ship
		if groupid == skinid//10:
			singleid = skinid % 10
		else: # if groupid does not match, the skin must have a singleid >= 10
			singleid = 10+total_add_ids
			total_add_ids += 1
		quotedata = getGameQuoteSingle(client, skinid) 
		if quotedata: quotes[singleid] = quotedata
	return quotes


def getWikiQuoteData(shipname=None, quotepage=None) -> dict:
	"""Returns a dict containing ALL quotes of all skins of a given ship from the WIKI.
	The keys are named after parameters complying with Template:ShipQuote for easy convertability.

	Either shipname or quotepage has to be given, otherwise None is returned.
	"""
	quote_wikidata = dict()
	if not quotepage:
		if not shipname: return None
		quotepage = wikiclient.execute(wikiclient.mwclient.pages.get, shipname+'/Quotes')
	if quotepage.exists:
		mwparser = mwparserfromhell.parse(quotepage.text())
		templates = mwparser.filter_templates()
		for template in templates:
			if not 'ShipQuote' in template.name: continue
			parsed_template_data = WikiHelper.parse_multiline_template(str(template))
			client = parsed_template_data.get('Region')
			skinname = parsed_template_data.get('Skin').replace('Skin', '').replace('Base', '') or '0'
			singleid = int(skinname.replace('PostPledge', '') or 0)

			# create client sub-dict and skinid sub-dict if not existing
			if not quote_wikidata.get(client): quote_wikidata[client] = dict()
			if not quote_wikidata[client].get(singleid): quote_wikidata[client][singleid] = dict()

			if 'PostPledge' in skinname:
				quote_wikidata[client][singleid][QuoteType.POST_OATH] = parsed_template_data
			else:
				quote_wikidata[client][singleid][QuoteType.BASE] = parsed_template_data
	return quote_wikidata

def updateQuotePage(shipname, saveToFile=False) -> bool:
	"""Updates the quote page of a given ship.

	:return:
	 true if gallery page update was successful, otherwise false.
	"""
	# retrieve data from wiki and gamefiles
	groupid = ShipConverter.convert(shipname)
	quotes_gamedata = {client: getGameQuoteData(client, groupid) for client in DEFAULT_CLIENTS}
	quotepage = wikiclient.execute(wikiclient.mwclient.pages.get, shipname+'/Quotes')
	quotes_wikidata = dict()#getWikiQuoteData(quotepage=quotepage)

	# merge game and wiki data
	wikitext = []

	for client in DEFAULT_CLIENTS:
		if client not in quotes_gamedata: continue
		client_game_quotes = quotes_gamedata[client]
		if not client_game_quotes: continue
		if wikitext:
			wikitext.append("|-|")
		wikitext.append(TAB_NAMES[client]+"=")

		for skinid in [0,-1,9,8,1,2,3,4,5,6,7]+list(range(10,max(client_game_quotes or [0])+1)):
			if skinid not in client_game_quotes: continue

			client_skin_game_quotes = client_game_quotes[skinid]
			for quotetype, skin_game_quotes in client_skin_game_quotes.items():
				if not skin_game_quotes: continue

				skin_wiki_quotes = Utility.dict_args_query(quotes_wikidata, client.name, skinid, quotetype) or Utility.dict_args_query(quotes_wikidata, client.name, skinid, QuoteType.POST_OATH) or {}
				skin_wiki_quotes = {k: clean_value(v) for k,v in skin_wiki_quotes.items()}
				skin_result_template = {**skin_wiki_quotes, **skin_game_quotes.lines}

				# add further values to template
				skin_result_template['Region'] = client.name
				skin_result_template['Skin'] = skin_game_quotes.quote_type.skin_type(skinid)

				# generate wikitext and add to wikitext list
				wikitext.append('==='+skin_game_quotes.display_name+'===')
				if client == Client.EN:
					wikitext.append(template_en.fill(skin_result_template))
				else:
					wikitext.append(template_general.fill(skin_result_template))


	wikitext = ["{{ShipTabber}}", "<tabber>"]+wikitext+["</tabber>"]
	wikitext = "\n".join(wikitext)

	if saveToFile:
		Utility.output('ship-quotes', wikitext)
	else:
		wikiclient.execute(quotepage.save, wikitext, summary='Added missing lines/updated changed information')

def main():
	#updateQuotePage("Hatakaze", True)
	for ship in sorted(ShipConverter.ship_to_id.keys()):
		updateQuotePage(ship)


if __name__ == "__main__":
	main()