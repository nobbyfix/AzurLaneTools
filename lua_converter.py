import os
from os.path import join
import json
import hashlib
import subprocess
import multiprocessing as mp

def get_file_hash(filepath:str):
	md5 = hashlib.md5()
	with open(filepath, 'rb') as f:
		while True:
			data = f.read(32768)
			if not data: break
			md5.update(data)
	return md5.hexdigest()

def convert_lua(filepath, savedest):
	if 'sharecfg' in filepath:
		pgname = os.path.basename(filepath)
		try: result = subprocess.check_output(['lua', 'serializer.lua', filepath, pgname], stderr=subprocess.DEVNULL)
		except: return
	else:
		try: result = subprocess.check_output(['lua', 'serializer2.lua', filepath], stderr=subprocess.DEVNULL)
		except: return

	rstr = result.decode('utf8')
	if rstr.startswith('null'): return

	jsondata = json.loads(rstr)
	jsons = json.dumps(jsondata, indent=2, ensure_ascii=False)

	with open(savedest, 'w', encoding='utf8') as jfile:
		jfile.write(jsons)

clients = {
	'EN': 'en-US',
	'CN': 'zh-CN',
	'JP': 'ja-JP',
	'KR': 'ko-KR',
	'TW': 'zh-TW'
}

directory_destinations = [
	('sharecfg', 'sharecfg'),
	(join('gamecfg', 'buff'),  'buff'),
	(join('gamecfg', 'dungeon'), 'dungeon'),
	(join('gamecfg', 'skill'), 'skill'),
	(join('gamecfg', 'story'), 'story'),
]

def main():
	# convert client string to the one dim uses
	input_client = input('Type the game version to convert: ')
	conv_clinet = clients.get(input_client)
	if not conv_clinet:
		print('Unknown client, aborting.')
		return

	hashes = dict()
	HASHTABLE_PATH = join('SrcJson', 'Hashes', input_client+'.json')
	if os.path.exists(HASHTABLE_PATH):
		with open(HASHTABLE_PATH, 'r', encoding='utf8') as jfile:
			hashes = json.load(jfile)
	else: print('No hash file found, all files will be converted.')

	args = []

	for DIR_FROM, DIR_TO in directory_destinations:
		# set path constants
		if DIR_FROM.endswith('story') and input_client == 'JP': DIR_FROM += 'jp'
		CONVERT_FROM = join('Src', conv_clinet, DIR_FROM)
		CONVERT_TO = join('SrcJson', input_client, DIR_TO)
		os.makedirs(CONVERT_TO, exist_ok=True)

		for entry in os.scandir(CONVERT_FROM):
			if entry.is_dir(): continue
			fname_noext = entry.name.replace('.lua', '')

			oldhash = hashes.get(fname_noext)
			newhash = get_file_hash(entry.path)
			if oldhash == newhash: continue

			hashes[fname_noext] = newhash
			arg = (join(CONVERT_FROM, fname_noext), join(CONVERT_TO, fname_noext+'.json'))
			args.append(arg)

	pool = mp.Pool(processes=mp.cpu_count())
	pool.starmap(convert_lua, reversed(args))

	# save hashtable
	os.makedirs(os.path.dirname(HASHTABLE_PATH), exist_ok=True)
	with open(HASHTABLE_PATH, 'w', encoding='utf8') as jfile:
		json.dump(hashes, jfile, ensure_ascii=False)

if __name__ == '__main__':
	main()