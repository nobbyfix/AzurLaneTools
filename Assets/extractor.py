import sys
import json
from argparse import ArgumentParser
from pathlib import Path
from itertools import chain
import multiprocessing as mp

from lib import imgrecon, config
from lib.classes import Client


def get_file_list(filepath: Path):
	with open(filepath, 'r', encoding='utf8') as f:
		for line in f.readlines():
			if line == '': continue
			yield line.replace('\n', '')

def get_changed_files(parent_directory: Path):
	return get_file_list(Path(parent_directory, 'difflog', 'diff_azl_changed.txt'))

def get_new_files(parent_directory: Path):
	return get_file_list(Path(parent_directory, 'difflog', 'diff_azl_new.txt'))


def restore_painting(image, abpath: Path, imgname: str, do_retry:bool):
	mesh = imgrecon.load_mesh(str(abpath), imgname+'-mesh')
	if mesh is not None:
		return imgrecon.recon(image, mesh)

	if not do_retry:
		return image

	# for some images, the mesh is in the non-tex asset bundle for some reason
	if abpath.name.endswith('_tex'):
		return restore_painting(image, abpath.with_name(abpath.name[:-4]), imgname, False)

	return restore_painting(image, abpath.with_name(abpath.name+'_tex'), imgname, False)

def extract_assetbundle(rootfolder: Path, filepath: str, targetfolder: Path):
	abpath = Path(rootfolder, filepath)
	for imageobj in imgrecon.load_images(str(abpath)):
		if imageobj.name == 'UISprite': continue # skip the UISprite element
		if 'char' in (imageobj.container or ''): continue # skip image if its of a chibi

		image = imageobj.image
		if filepath.split('/')[0] == 'painting':
			image = restore_painting(image, abpath, imageobj.name, True)

		target = Path(Path(targetfolder, filepath).parent, imageobj.name+'.png')
		target.parent.mkdir(parents=True, exist_ok=True)

		while True:
			if target.exists():
				print(f'ERROR: Tried to save "{imageobj.name}" from "{abpath}" to "{target}", but the file already exists.')
				target = target.with_name(target.stem + "_" + target.suffix)
			else:
				image.save(target)
				break
		return target


def load_extractable_folders():
	with open(Path('config', 'extract_config.json'), 'r') as f:
		return json.load(f)['extractable_folder']

def extract_by_client(client: Client):
	client_directory = Path('ClientAssets', client.name)
	changed_files = get_changed_files(client_directory)
	new_files = get_new_files(client_directory)

	extract_directory = Path('ClientExtract', client.name)
	extractable_folder = config.load_user_config().extract_filter
	
	with mp.Pool(processes=mp.cpu_count()) as pool:
		for assetpath in chain(changed_files, new_files):
			if assetpath.split('/')[0] in extractable_folder:
				pool.apply_async(extract_assetbundle, (Path(client_directory, 'AssetBundles'), assetpath, extract_directory,))

		# explicitly join pool
		# this causes the pool to wait for all asnyc tasks to complete
		pool.close()
		pool.join()

def extract_single_assetbundle(client: Client, assetpath: str):
	client_directory = Path('ClientAssets', client.name, 'AssetBundles')
	extract_directory = Path('ClientExtract', client.name)
	return extract_assetbundle(client_directory, assetpath, extract_directory)

if __name__ == "__main__":
	# setup argument parser
	parser = ArgumentParser(description="Extracts image assets as pngs.",
		epilog="If '--file' is not set, all files from the latest update will be extracted.")
	parser.add_argument("client", metavar="CLIENT", type=str, choices=Client._member_names_, help="client to extract files of")
	parser.add_argument("-f", "--filepath", type=str, help="Path to the file to extract only this single file")
	args = parser.parse_args()

	# parse arguments and execute
	client = Client[args.client]
	if filepath := args.filepath:
		extract_single_assetbundle(client, filepath)
	else:	
		extract_by_client(client)