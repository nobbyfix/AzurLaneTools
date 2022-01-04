from argparse import ArgumentParser
from pathlib import Path
import multiprocessing as mp
from typing import Generator

from lib import imgrecon, config
from lib.classes import Client, DownloadType, VersionType


def get_file_list(filepath: Path) -> Generator[str, None, None]:
	with open(filepath, 'r', encoding='utf8') as f:
		for line in f.readlines():
			if line == '': continue
			yield line.replace('\n', '')

def get_diff_files(parent_directory: Path, vtype: VersionType, dtype: DownloadType) -> Generator[str, None, None]:
	fname = f'diff_{vtype.name.lower()}_{dtype.name.lower()}.txt'
	p = Path(parent_directory, 'difflog', fname)
	return get_file_list(p)


def restore_painting(image, abpath: Path, imgname: str, do_retry: bool):
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


def extract_by_client(client: Client):
	userconfig = config.load_user_config()
	client_directory = Path(userconfig.asset_directory, client.name)
	extract_directory = Path(userconfig.extract_directory, client.name)
	downloaded_files = get_diff_files(client_directory, VersionType.AZL, DownloadType.Success)

	def _filter(assetpath: str):
		if assetpath.split('/')[0] in userconfig.extract_filter:
			return (not userconfig.extract_isblacklist)
		return userconfig.extract_isblacklist

	with mp.Pool(processes=mp.cpu_count()-1) as pool:
		for assetpath in filter(_filter, downloaded_files):
			pool.apply_async(extract_assetbundle, (Path(client_directory, 'AssetBundles'), assetpath, extract_directory,))

		# explicitly join pool
		# this causes the pool to wait for all asnyc tasks to complete
		pool.close()
		pool.join()

def extract_single_assetbundle(client: Client, assetpath: str):
	userconfig = config.load_user_config()
	client_directory = Path(userconfig.asset_directory, client.name, 'AssetBundles')
	extract_directory = Path(userconfig.extract_directory, client.name)
	return extract_assetbundle(client_directory, assetpath, extract_directory)


def main():
	# setup argument parser
	parser = ArgumentParser(description="Extracts image assets as pngs.",
		epilog="If '-f/--filepath' is not set, all files from the latest update will be extracted.")
	parser.add_argument("client", metavar="CLIENT", type=str, choices=Client._member_names_, help="client to extract files of")
	parser.add_argument("-f", "--filepath", type=str, help="Path to the file to extract only this single file")
	args = parser.parse_args()

	# parse arguments and execute
	client = Client[args.client]
	if filepath := args.filepath:
		extract_single_assetbundle(client, filepath)
	else:	
		extract_by_client(client)

if __name__ == "__main__":
	main()