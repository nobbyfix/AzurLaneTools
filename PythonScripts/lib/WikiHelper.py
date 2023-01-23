import re
import json
import time
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field
import mwclient
from mwclient import APIError

from . import ALJsonAPI, WikiConstants
from .apiclasses import Awardable, EquipStat, Item, ShipReward, Furniture


class WikiClient():
	def __init__(self, execution_delay: float = 1.5, settings_path: Path = Path('data', 'wiki_settings.json')):
		self.settings_path = settings_path
		self.execution_delay = execution_delay
		self.last_execute_time = 0.0

		### INIT MWCLIENT ###
		print('reading wiki settings ...')
		if settings_path.exists():
			settings = self.load_settings()
			print('Loaded settings.')
		else:
			print(f'{settings_path} not found. Creating new file...')
			settings = {
				"username": "",
				"password": "",
				"url": input("Wiki Url: "),
				"useragent": input("Useragent: "),
			}
			self.save_settings(settings)
			print('Settings file created.')
		self.mwclient = mwclient.Site(settings['url'], clients_useragent=settings['useragent'])
		self.settings = settings
		self.logged_in = False

	def load_settings(self) -> dict:
		with open(self.settings_path, 'r', encoding='utf8') as settings_file:
			return json.load(settings_file)

	def save_settings(self, settings: dict) -> None:
		with open(self.settings_path, 'w', encoding='utf8') as settings_file:
			json.dump(settings, settings_file)	


	def login(self) -> 'WikiClient':
		if self.logged_in: return self

		if not self.settings['username']:
			print("You can leave the username empty, but it will prompt to input one during the next run.")
			if username := input("Username: "):
				self.settings['username'] = username
				self.settings['password'] = input("Password: ")
				self.save_settings(self.settings)

		# log into wiki
		print('Logging into mediawiki...')
		self.mwclient.login(self.settings['username'], self.settings['password'])
		print('Logged in.')
		return self

	def execute(self, func: callable, *args, **kwargs):
		delta_last_execute = time.time() - self.last_execute_time
		if delta_last_execute < self.execution_delay:
			time.sleep(delta_last_execute)

		try:
			result = func(*args, **kwargs)
		except APIError as error:
			if error.code == "ratelimited":
				exec_delay_saved = self.execution_delay
				self.execution_delay = (self.execution_delay+5)*2
				result = self.execute(func, *args, **kwargs)
				self.execution_delay = exec_delay_saved
			else:
				raise error

		self.last_execute_time = time.time()
		return result


def simple_template(name: str, params: list) -> str:
	params.insert(0, name)
	wikitext = '|'.join([(str(param) if param is not None else '') for param in params])
	return '{{'+wikitext.rstrip('|')+'}}'


class MultilineTemplate():
	def __init__(self, template: str):
		with open('templates/'+template+'.json', 'r') as jfile:
			jsontemplate = json.load(jfile)
		self.template_name = jsontemplate["template_name"]
		self.sections = jsontemplate['template_sections']
		self.behavior = jsontemplate['behavior']
		self.default_behavior = self.behavior['default']
		self.prefer_wiki_params = jsontemplate['prefer-wiki-data']

	def _param(self, key, val) -> str:
		if val is None: val = ''
		return f' | {key} = {str(val)}'

	def _fill_section(self, section, content, wiki_content) -> str:
		# add all template parameter of current section
		section_params = []
		for param in section.get('params', []):
			value = content.get(param)
			if param in self.prefer_wiki_params:
				value = wiki_content.get(param)

			p_behavior = self.behavior.get(param, self.default_behavior)
			p_behav_type = p_behavior['type']
			if p_behav_type == 'keep':
				section_params.append(self._param(param, value))
			elif p_behav_type == 'remove_empty':
				if not (value is None or value == ''):
					section_params.append(self._param(param, value))
			elif p_behav_type == 'dependency':
				dependency_type = p_behavior['dependency']['type']
				dependend_on = p_behavior['dependency']['dependent_params']
				if sum([param in content for param in dependend_on]) == 0: continue
				if dependency_type == 'keep_empty':
					if not value is None:
						section_params.append(self._param(param, value))
				elif dependency_type == 'remove_empty':
					if not (value is None or value == ''):
						section_params.append(self._param(param, value))
				elif dependency_type == 'keep_always':
					section_params.append(self._param(param, value))
				else: raise NotImplementedError(f'Unknown dependency behavior type {dependency_type}')
			else: raise NotImplementedError(f'Unknown behavior type {p_behav_type}')

		# recursively fill all subsections
		sub_wikitexts = []
		for subsection in section.get('sections', []):
			sub_wikitext = self._fill_section(subsection, content, wiki_content)
			if sub_wikitext:
				sub_wikitexts.append(sub_wikitext)

		# compile section_wikitext if any parameters were added from this section
		# section_wikitext consists of the comment before params, then the block of params, each on a new line
		if section_params:
			sub_wikitexts.insert(0, '\n'.join(section_params))
		if sub_wikitexts:
			comment = section['comment']
			comment = comment and comment+'\n'
			return comment+'\n\n'.join(sub_wikitexts).rstrip('\n')

	def fill(self, content: dict[str, Any], wiki_content: dict[str, Any] = None) -> str:
		filled_sections = self._fill_section(self.sections, content, wiki_content or {})

		# add all sections with one empty line spacing between them to result wikitext
		wikitext = "{{"+self.template_name+'\n'+filled_sections+'\n}}'
		return wikitext

COMMENT_REGEX = re.compile(r'<!--(.*?)-->')
COMMENT_PART = re.compile(r'(.*?)-->|<!--(.*)')
def remove_comments(wikitext: str) -> str:
	a, _ = COMMENT_REGEX.subn('', wikitext)
	b, _ = COMMENT_PART.subn('', a)
	return b

PARAMS_RE = re.compile(r'\n\ *\|')
def parse_multiline_template(wikitext: str, do_remove_comments: bool = True) -> str:
	if do_remove_comments: wikitext = remove_comments(wikitext)
	template = dict()
	params = PARAMS_RE.split(wikitext[2:-2])
	for param in params:
		if '=' in param:
			key, value = param.split('=', 1)
			template[key.strip()] = value.strip()
	return template

def put_icon(filename: str, itemname: str = '', size: str = 'x22px', nolink: bool = False) -> str:
	nolink = 'link=' if nolink else ''
	args = [filename, size, itemname, nolink]
	args = [arg for arg in args if arg != '']
	return '[[File:'+'|'.join(args).strip('|')+']]'

parttype = {
	'General': 'Aux',
	'Torpedo': 'Torp',
	'Aircraft': 'Plane',
	'Anti-Air Gun': 'AA',
	'Main Gun': 'Gun',
	'Random Gear': 'Unknown',
}
RE_BLUEPRINT_TEMPLATE = re.compile(r"^(T[0-9])\s(\w+)\sRetrofit\sBlueprint")
RE_PACK_TEMPLATE = re.compile(r"^(\w+)\s(T[0-9])\sTech\sPack")
def item_icontemplate(name: str) -> str:
	if not name: return ''
	if m := RE_BLUEPRINT_TEMPLATE.match(name):
		return "{{Blueprint|"+ m.group(1) + "|" + m.group(2) + "}}"

	if ' Part' in name:
		name = name.split(' ', 1)
		ptype = name[1].rsplit(' ', 1)[0]
		ptype = parttype.get(ptype)
		return f'{{{{Plate|{name[0]}|{ptype}}}}}'
	
	if m := RE_PACK_TEMPLATE.match(name):
		return "{{Box|"+ m.group(2) + "}}"

	name = {
		'Oil': 'Oil',
		'Coins': 'Coin',
		'Wisdom Cube': 'Cube',
		'Cognitive Chips': 'Module',
		'Gems': 'Gem',
	}.get(name)
	if name: return '{{'+name+'}}'

def item_icontemplate_legacy(name: str) -> str:
	if ' Retrofit Blueprint' in name:
		tier = name.split(' ', 1)[0]
		bptype = name.split(' ', 2)[1]
		return '{{Blueprint|'+tier+'|'+bptype+'}}'

	if ' Part' in name:
		name = name.split(' ', 1)
		parttype = name[1].rsplit(' ', 1)[0]
		parttype = {
			'General': 'Aux',
			'Torpedo': 'Torp',
			'Aircraft': 'Plane',
			'Anti-Air Gun': 'AA',
			'Main Gun': 'Gun',
			'Random Gear': 'Unknown'
		}.get(parttype)
		return f'{{{{Plate|{name[0]}|{parttype}}}}}'

	name = {
		'Oil': 'Oil',
		'Coins': 'Coin',
		'Wisdom Cube': 'Cube',
		'Cognitive Chips': 'Module',
		'Gems': 'Gem',
	}.get(name)
	if name: return '{{'+name+'}}'


@dataclass
class WikiAwardable(Awardable):
	link: str = field(default=None)
	filelink: str = field(default=None)
	icontemplate: str = field(default=None)


@dataclass
class Wikifier:
	api: ALJsonAPI = field(repr=False)

	def wikify_awardable(self, awardable: Awardable) -> WikiAwardable:
		# overrides
		if isinstance(awardable, Item):
			awardable.icon = awardable.icon.replace("Props/", "").replace("Equips/", "")

		# default conversion
		name = WikiConstants.item_name(awardable.name)
		link = WikiConstants.item_link(name)
		filelink = WikiConstants.item_filename(name) or WikiConstants.item_filename(awardable.icon) or awardable.icon

		# type based switches
		if isinstance(awardable, EquipStat) or (isinstance(awardable, Item) and awardable.type == 9):
			equip_convert_data = self.api.equip_converter.from_equipid(int(awardable.icon))
			if not equip_convert_data: equip_convert_data = self.api.equip_converter.from_icon(int(awardable.icon))
			if not equip_convert_data: equip_convert_data = self.api.equip_converter.from_equipid(awardable.id)
			if not equip_convert_data: equip_convert_data = self.api.equip_converter.from_equipid(awardable.name)

			name = ''
			if equip_convert_data:
				name = equip_convert_data.wikiname
			else:
				name = awardable.name

			link = name or ''
			name = name or awardable.name
			filelink = awardable.icon

		elif isinstance(awardable, ShipReward):
			name = self.api.ship_converter.get_shipname(awardable.shipid.groupid)
			link = name
			filelink = name+"Icon"

		elif isinstance(awardable, Furniture):
			filelink = "FurnIcon_"+awardable.icon

		icontemplate = item_icontemplate(name)
		return WikiAwardable(name=name, link=link, filelink=filelink, icontemplate=icontemplate,
			rarity=awardable.rarity, icon=awardable.icon)
