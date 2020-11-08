from typing import Any
import re, json, time, mwclient
from pathlib import Path
import Constants

class WikiClient():
	def __init__(self, execution_delay: float = 1, settings_path: Path = Path('data', 'wiki_settings.json')):
		self.settings_path = settings_path
		self.mwclient = None
		self.execution_delay = execution_delay
		self.last_execute_time = 0
	
	def login(self):
		if self.mwclient: return 

		# create wiki_settings.json file if not found
		print('reading wiki settings ...')
		if self.settings_path.exists():
			with open(self.settings_path, 'r', encoding='utf8') as settings_file:
				settings = json.load(settings_file)
			print('Loaded settings.')
		else:
			print(f'{self.settings_path} not found. Creating new file...')
			settings_data = dict()
			settings_data['username'] = input('Username: ')
			settings_data['password'] = input('Password: ')
			settings_data['url'] = input('URL: ')
			settings_data['useragent'] = input('Useragent: ')
			with open(self.settings_path, 'w', encoding='utf8') as settings_file:
				json.dump(settings_data, settings_file)
			print('Settings file created.')

		# log into wiki
		print('Logging into mediawiki...')
		site = mwclient.Site(settings.get('url'), clients_useragent=settings.get('useragent'))
		site.login(settings.get('username'), settings.get('password'))
		print('Logged in.')
		self.mwclient = site

	def execute(self, func: callable, *args, **kwargs):
		delta_last_execute = time.time() - self.last_execute_time
		if delta_last_execute < self.execution_delay:
			time.sleep(delta_last_execute)
		self.last_execute_time = time.time()
		return func(*args, **kwargs)


import warnings
def load_mwclient_site(settings_path: Path = Path('data', 'wiki_settings.json')) -> mwclient.Site:
	warnings.warn("Replace with usage of 'WikiClient' class.", DeprecationWarning)
	wikiclient = WikiClient(settings_path=settings_path)
	wikiclient.login()
	return wikiclient.mwclient

def simple_template(name: str, params: list) -> str:
	params.insert(0, name)
	wikitext = '|'.join([(str(param) if param != None else '') for param in params])
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
	
	def _param(self, key, val):
		if val == None: val = ''
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

	def fill(self, content: dict[str, Any], wiki_content: dict[str, Any]=dict()) -> str:
		filled_sections = self._fill_section(self.sections, content, wiki_content)
		
		# add all sections with one empty line spacing between them to result wikitext
		wikitext = "{{"+self.template_name+'\n'+filled_sections+'\n}}'
		return wikitext

COMMENT_REGEX = re.compile(r'<!--(.*?)-->')
COMMENT_PART = re.compile(r'(.*?)-->|<!--(.*)')
def remove_comments(wikitext:str) -> str:
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

def award_to_display(award) -> str:
	itemname = Constants.item_name(award.name.strip()) or ''

	if award.data_type == 4: icon = itemname+'Icon'
	else: icon = Constants.item_filename(itemname) or award.icon or award.data_id
	
	rarity = Constants.RARITY_NAME_ITEM[award.rarity]
	name = str(award.amount)+'x '+itemname
	return simple_template('Display', [str(icon), rarity, name])
