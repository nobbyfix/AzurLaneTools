#!/usr/bin/env python3.9
import sys
import shutil
from argparse import ArgumentParser
from zipfile import ZipFile
from pathlib import Path

from lib import versioncontrol, updater, config
from lib.classes import BundlePath, Client, CompareType, DownloadType, UpdateResult


appnames = {
	'com.YoStarEN.AzurLane.obb': Client.EN,
	'com.YoStarJP.AzurLane.obb': Client.JP,
	'kr.txwy.and.blhx.obb': Client.KR,
	'com.hkmanjuu.azurlane.gp.obb': Client.TW,
}


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
	with zipfile.open('assets/AssetBundles/'+filepath, 'r') as zf, open(target, 'wb') as f:
		shutil.copyfileobj(zf, f)


def extract_obb(path: Path):
	for appname, client in appnames.items():
		if path.name.endswith(appname):
			print(f'Determined client {client.name} from filename.')
			with ZipFile(path, 'r') as zipfile:
				unpack(zipfile, client)
			break
	else:
		sys.exit(f'Filename "{path.name}" could not be associated with any known client.')

def extract_apk():
	raise NotImplementedError("Extract the obb manually from the xapk and use obb_import on that file.")

def main(path: Path):
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
		extract_apk()
	else:
		sys.exit(f'Unknown file extesion "{path.suffix}".')


def main():
	parser = ArgumentParser()
	parser.add_argument('file', nargs=1, help='obb/apk file to extract')
	args = parser.parse_args()
	main(Path(args.file[0]))

if __name__ == "__main__":
	main()