import os
from os.path import join, dirname, abspath, exists
from AzurLane import ALJsonAPI

DEFAULT_JSON_SOURCE_PATH = join(dirname(dirname(abspath(__file__))), 'SrcJson')

def defaultJsonAPI() -> ALJsonAPI:
	return ALJsonAPI(DEFAULT_JSON_SOURCE_PATH)

def rreplace(s:str, old:str, new:str, occurrence:int):
	li = s.rsplit(old, occurrence)
	return new.join(li)

def makedirs(directorypath):
	"""
	faster than simply calling os.makedirs with exists_ok=True
	if the same directory gets checked even after its creation
	"""
	if not exists(directorypath):
		os.makedirs(directorypath, exist_ok=True)

def makedirsf(filepath):
	"""
	faster than simply calling os.makedirs with exists_ok=True
	if the same directory gets checked even after its creation
	"""
	dname = dirname(filepath)
	if not exists(dname):
		os.makedirs(dname, exist_ok=True)

def output(fname:str, text:str):
	makedirs('output')
	with open(join('output', fname+'.wikitext'), 'w', encoding='utf8') as f:
		f.write(text)

def dict_args_query(dict_input: dict, *args):
	for arg in args:
		if isinstance(dict_input, dict):
			dict_input = dict_input.get(arg)
	return dict_input