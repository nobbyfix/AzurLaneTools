from argparse import ArgumentParser
from pathlib import Path
from itertools import chain
import multiprocessing as mp
import json

from lib import imgrecon
from lib.classes import Client


def get_file_list(filepath: Path):
	with open(filepath, 'r', encoding='utf8') as f:
		for line in f.readlines():
			if line == '': continue
			yield line.replace('\n', '')

def get_changed_files(parent_directory: Path):
	return get_file_list(Path(parent_directory, 'diff_changed.txt'))

def get_new_files(parent_directory: Path):
	return get_file_list(Path(parent_directory, 'diff_new.txt'))


def restore_painting(image, abpath: Path, imgname: str):
	mesh = imgrecon.load_mesh(abpath, imgname+'-mesh')
	if mesh is None:
		# for these images, the mesh is in the non-tex asset bundle for some reason
		if abpath.name in ['rexin_tex', 'susaikesi_tex']:
			return restore_painting(image, abpath.with_name(abpath.name[:-4]), imgname)
		return image
	return imgrecon.recon(image, mesh)

def extract_assetbundle(rootfolder: Path, filepath: str, targetfolder: Path):
	abpath = Path(rootfolder, filepath)
	for imageobj in imgrecon.load_images(str(abpath)):
		if imageobj.name == 'UISprite': continue # skip the UISprite element
		if 'char' in (imageobj.container or ''): continue # skip image if its of a chibi

		image = imageobj.image
		if filepath.split('/')[0] == 'painting':
			image = restore_painting(image, abpath, imageobj.name)
		
		target = Path(Path(targetfolder, filepath).parent, imageobj.name+'.png')
		target.parent.mkdir(parents=True, exist_ok=True)
		image.save(target)


def load_extractable_folders():
	with open(Path('config', 'extract_config.json'), 'r') as f:
		return json.load(f)['extractable_folder']

def extract_by_client(client: Client):
	client_directory = Path('ClientAssets', client.name)
	changed_files = get_changed_files(client_directory)
	new_files = get_new_files(client_directory)

	extract_directory = Path('ClientExtract', client.name)
	extractable_folder = load_extractable_folders()
	
	pool = mp.Pool(processes=mp.cpu_count()-1)
	async_results = []

	for assetpath in chain(changed_files, new_files):
		if assetpath.split('/')[0] in extractable_folder:
			async_result = pool.apply_async(extract_assetbundle, (Path(client_directory, 'AssetBundles'), assetpath, extract_directory,))
			async_results.append(async_result)
			#extract_assetbundle(Path(client_directory, 'AssetBundles'), assetpath, extract_directory)
	wait_and_close_pool(pool, async_results)


def wait_and_close_pool(pool: mp.Pool, asyncresults: list):
	for res in asyncresults:
		res.wait()
	pool.close()
	pool.join()


if __name__ == "__main__":
	parser = ArgumentParser()
	parser.add_argument('-c', '--client', help='client to extract assets from')
	args = parser.parse_args()
	
	clientname = args.client
	if clientname is None:
		clientname = input('Type which client to extract assets from: ')
	
	if clientname in Client.__members__:
		client = Client[clientname]
		extract_by_client(client)
	else:
		print(f'The client {clientname} is not supported or does not exist.')
		exit(1)