from argparse import ArgumentParser
from zipfile import ZipFile
from zipfile import Path as ZipPath
from pathlib import Path
import shutil

from classes import Client, VersionType


appnames = {
	'com.YoStarEN.AzurLane.obb': Client.EN,
	'com.YoStarJP.AzurLane.obb': Client.JP,
	'kr.txwy.and.blhx.obb': Client.KR,
	'com.hkmanjuu.azurlane.gp.obb': Client.TW,
}

version_file_suffix = {
	VersionType.AZL: '',
	VersionType.CV: '-cv',
	VersionType.L2D: '-live2d',
	VersionType.PIC: '-pic',
	VersionType.BGM: '-bgm',
}


def unpack(path: Path, client: Client):
	print('Unpacking archive...')
	with ZipFile(path, 'r') as zipfile:
		extract_to_folder = Path('ClientAssets', client.name)
		if not extract_to_folder.exists(): extract_to_folder.mkdir(parents=True)

		for versiontype, suffix in version_file_suffix.items():
			versionfname = 'version'+suffix+'.txt'
			if not 'assets/'+versionfname in zipfile.namelist():
				print(f'The file {versionfname} could not be found in the archive. Has the archive been modified?')
				continue

			versionpath = Path(extract_to_folder, versionfname)
			with zipfile.open('assets/'+versionfname, 'r') as zf:
				obbversion = zf.read().decode('utf8') 

			# if a version file already exists, compare the versions
			# if the obbversion is smaller, don't extract data from obb
			if versionpath.exists():
				with open(versionpath, 'r') as f:
					currentversion = f.read()
				
				if tuple(obbversion.split('.')) < tuple(currentversion.split('.')):
					print(f'Current version {currentversion} is higher or same as obb version {obbversion} for {versionfname}.')
					continue

			# write new version to file
			with open(versionpath, 'w') as f:
				f.write(obbversion)
			
			# extract corresponding hashfile
			with open(Path(extract_to_folder, 'hashes'+suffix+'.csv'), 'wb') as fh:
				with zipfile.open('assets/hashes'+suffix+'.csv', 'r') as zfh:
					shutil.copyfileobj(zfh, fh)
			# also extract all assets
			if versiontype == VersionType.AZL:
				# remove all existing asset bundles
				abpath = Path(extract_to_folder, 'AssetBundles')
				shutil.rmtree(abpath, ignore_errors=True)

				# extract assets now
				zipabpath = ZipPath(zipfile, 'assets/AssetBundles/')
				extract_folder(zipfile, zipabpath, zipabpath, abpath)

def extract_folder(zipfile: ZipFile, rootfolder: ZipPath, folderpath: ZipPath, target: Path):
	for entry in folderpath.iterdir():
		if entry.is_dir(): extract_folder(zipfile, rootfolder, entry, target)
		elif entry.is_file():
			file_target = Path(target, entry.at.replace(rootfolder.at, ''))
			file_target.parent.mkdir(parents=True, exist_ok=True)
			with zipfile.open(entry.at, 'r') as zf, open(file_target, 'wb') as f:
				f.write(zf.read())

def main(path: Path):
	if not path.exists():
		print('This file does not exist.')
		exit(1)

	if path.suffix == '.obb':
		print('File has .obb extension.')
		for appname, client in appnames.items():
			if path.name.endswith(appname):
				print(f'Determined client {client.name} from filename.')
				unpack(path, client)
				break
		else:
			print(f'Filename "{path.name}" could not be associated with any known client.')

	elif path.suffix == '.apk':
		print('File has .apk extension, assuming CN client.')
		unpack(path, Client.CN)
	else:
		print(f'Unknown file extesion "{path.suffix}".')

if __name__ == "__main__":
	parser = ArgumentParser()
	parser.add_argument('-f', '--file', help='obb/apk file to extract')
	args = parser.parse_args()
	main(Path(args.file))
