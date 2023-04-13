#!/usr/bin/env python3.9
import io
import re
import sys
import json
import shutil
from argparse import ArgumentParser
from zipfile import ZipFile
from pathlib import Path

from lib import versioncontrol, updater, config
from lib.classes import BundlePath, Client, CompareType, DownloadType, UpdateResult


def unpack(zipfile: ZipFile, client: Client):
	# load config data from files
	userconfig = config.load_user_config()
	CLIENT_ASSET_DIR = Path(userconfig.asset_directory, client.name)
	CLIENT_ASSET_DIR.mkdir(parents=True, exist_ok=True)

	print('Unpacking archive...')
	for versiontype, suffix in versioncontrol.version_file_suffix.items():
		versionfname = 'version'+suffix+'.txt'
		if not 'assets/'+versionfname in zipfile.namelist():
			print(f'{versiontype.name}: The file {versionfname} could not be found in the archive. Has the archive been modified?')
			continue

		# read version string from obb
		with zipfile.open('assets/'+versionfname, 'r') as zf:
			obbversion = zf.read().decode('utf8')

		# if a version file already exists, compare the versions
		# if the obbversion is smaller (older), don't extract data from obb
		currentversion = versioncontrol.load_version_string(versiontype, CLIENT_ASSET_DIR)
		if currentversion and tuple(obbversion.split('.')) < tuple(currentversion.split('.')):
			print(f'{versiontype.name}: Current version {currentversion} is same or newer than obb version {obbversion}.')
			continue

		# read hash files from obb and current file and compare them
		with zipfile.open('assets/hashes'+suffix+'.csv', 'r') as hashfile:
			obbhashes = versioncontrol.parse_hash_rows(hashfile.read().decode('utf8'))
		currenthashes = versioncontrol.load_hash_file(versiontype, CLIENT_ASSET_DIR)
		comparison_results = updater.compare_hashes(currenthashes, obbhashes)

		# extract and delete files
		assetbasepath = Path(CLIENT_ASSET_DIR, 'AssetBundles')
		update_files = list(filter(lambda r: r.compare_type != CompareType.Unchanged, comparison_results.values()))
		update_results = [UpdateResult(r, DownloadType.NoChange, BundlePath.construct(assetbasepath, r.new_hash.filepath)) for r in filter(lambda r: r.compare_type == CompareType.Unchanged, comparison_results.values())]

		fileamount = len(update_files)
		for i, result in enumerate(update_files, 1):
			if result.compare_type in [CompareType.New, CompareType.Changed]:
				print(f'Saving {result.new_hash.filepath} ({i}/{fileamount}).')
				assetpath = BundlePath.construct(assetbasepath, result.new_hash.filepath)
				extract_asset(zipfile, assetpath.inner, assetpath.full)
				update_results.append(UpdateResult(result, DownloadType.Success if assetpath.full.exists() else DownloadType.Failed, assetpath))
			elif result.compare_type == CompareType.Deleted:
				print(f'Deleting {result.current_hash.filepath} ({i}/{fileamount}).')
				assetpath = BundlePath.construct(assetbasepath, result.current_hash.filepath)
				updater.remove_asset(assetpath.full)
				update_results.append(UpdateResult(result, DownloadType.Removed, assetpath))

		# update version string, hashes and difflog
		hashes_updated = updater.filter_hashes(update_results)
		versioncontrol.update_version_data(versiontype, CLIENT_ASSET_DIR, obbversion, hashes_updated)
		versioncontrol.save_difflog(versiontype, update_results, CLIENT_ASSET_DIR)
		return update_results


def extract_asset(zipfile: ZipFile, filepath: str, target: Path):
	target.parent.mkdir(exist_ok=True, parents=True)
	
	if "." in Path(filepath).name:
		assetpath = "assets/AssetBundles/"+filepath
	else:
		assetpath = "assets/AssetBundles/"+filepath+".ys"

	with zipfile.open(assetpath, 'r') as zf, open(target, 'wb') as f:
		shutil.copyfileobj(zf, f)


def extract_obb(path: Path):
	for client in Client:
		if client.package_name and re.match(rf".*{client.package_name}\.obb", path.name):
			print(f'Determined client {client.name} from filename.')
			with ZipFile(path, 'r') as zipfile:
				unpack(zipfile, client)
			break
	else:
		sys.exit(f'Filename "{path.name}" could not be associated with any known client.')

def extract_xapk(path: Path):
	with ZipFile(path, 'r') as xapk_archive:
		# read the manifest file for information about the client, obbs and the apk paths inside the archive
		with xapk_archive.open('manifest.json', 'r') as manifestfile:
			manifest = json.loads(manifestfile.read().decode('utf8'))
		
		# determine the client the xpak comes from
		if client := Client.from_package_name(manifest['package_name']):
			print(f'Determined client {client.name} from manifest.json file.')
			# find all obb archives and extract files from them
			for obb_expansion in manifest['expansions']:
				with xapk_archive.open(obb_expansion['file'], 'r') as mainobbfile:
					# need to load the full obb into memory, otherwise it has to constantly read the whole obb again and performance gets shit
					mainobb_filedata = io.BytesIO(mainobbfile.read())
					with ZipFile(mainobb_filedata, 'r') as main_obb:
						unpack(main_obb, client)
		else:
			print("Could not determine client from xapk manifest.json.")


def extract(path: Path):
	if not path.exists():
		sys.exit('This file does not exist.')

	if path.suffix == '.obb':
		print('File has .obb extension.')
		extract_obb(path)
	elif path.suffix == '.apk':
		print('File has .apk extension, assuming CN client.')
		with ZipFile(path, 'r') as zipfile:
			unpack(zipfile, Client.CN)
	elif path.suffix == '.xapk':
		print('File has .xapk extension.')
		extract_xapk(path)
	else:
		sys.exit(f'Unknown file extesion "{path.suffix}".')


def main():
	parser = ArgumentParser()
	parser.add_argument('file', nargs=1, help='obb/apk file to extract')
	args = parser.parse_args()
	extract(Path(args.file[0]))

if __name__ == "__main__":
	main()
