from os.path import join, dirname, abspath
from AzurLane import ALJsonAPI

DEFAULT_JSON_SOURCE_PATH = join(dirname(dirname(abspath(__file__))), 'SrcJson')

def defaultJsonAPI() -> ALJsonAPI:
	return ALJsonAPI(DEFAULT_JSON_SOURCE_PATH)

def rreplace(s:str, old:str, new:str, occurrence:int):
	li = s.rsplit(old, occurrence)
	return new.join(li)

def output(fname:str, text:str):
	with open(join('output', fname+'.wikitext'), 'w', encoding='utf8') as f:
		f.write(text)