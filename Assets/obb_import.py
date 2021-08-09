import sys
import shutil
from argparse import ArgumentParser
from zipfile import ZipFile
from pathlib import Path

from lib import versioncontrol, updater
from lib.classes import Client, CompareType


appnames = {
	'com.YoStarEN.AzurLane.obb': Client.EN,
	'com.YoStarJP.AzurLane.obb': Client.JP,
	'kr.txwy.and.blhx.obb': Client.KR,
	'com.hkmanjuu.azurlane.gp.obb': Client.TW,
}


def unpack(zipfile: ZipFile, client: Client):
	print('Unpacking archive...')
	extract_to_folder = Path('ClientAssets', client.name)
	if not extract_to_folder.exists(): extract_to_folder.mkdir(parents=True)

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
		currentversion = versioncontrol.load_version_string(versiontype, extract_to_folder)
		if currentversion and tuple(obbversion.split('.')) < tuple(currentversion.split('.')):
			print(f'{versiontype.name}: Current version {currentversion} is same or newer than obb version {obbversion}.')
			continue

		# read hash files from obb and current file and compare them
		with zipfile.open('assets/hashes'+suffix+'.csv', 'r') as hashfile:
			obbhashes = hashfile.read().decode('utf8')
		currenthashes = versioncontrol.load_hash_file(versiontype, extract_to_folder)
		hash_compare_results = updater.compare_hashes(currenthashes, obbhashes)

		# extract and delete files
		abpath = Path(extract_to_folder, 'AssetBundles')
		version_diff_output = {t: [] for t in CompareType}
		fileamount = len(hash_compare_results.values())
		for i, result in enumerate(hash_compare_results.values(), 1):
			version_diff_output[result.compare_type].append(result.filepath)
			assetpath = Path(abpath, result.filepath)
			if result.compare_type in [CompareType.New, CompareType.Changed]:
				print(f'Saving {result.filepath} ({i}/{fileamount}).')
				extract_asset(zipfile, result.filepath, assetpath)
			elif result.compare_type == CompareType.Deleted:
				print(f'Deleting {result.filepath} ({i}/{fileamount}).')
				updater.remove_asset(assetpath)

		# write difflog files
		for comp_type, filepaths in version_diff_output.items():
			fileoutpath = Path(extract_to_folder, 'difflog', f'diff_{versiontype.name.lower()}_{comp_type.name.lower()}.txt')
			fileoutpath.parent.mkdir(exist_ok=True)
			with open(fileoutpath, 'w', encoding='utf8') as f:
				f.write('\n'.join(filepaths))

		# update local version and hashfile
		versioncontrol.update_version_data(versiontype, extract_to_folder, obbversion, obbhashes)

def extract_asset(zipfile: ZipFile, filepath: str, target: Path):
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

if __name__ == "__main__":
	parser = ArgumentParser()
	parser.add_argument('file', nargs=1, help='obb/apk file to extract')
	args = parser.parse_args()
	main(Path(args.file[0]))