import sys
from pathlib import Path
from typing import Iterable, Optional

from . import downloader, versioncontrol
from .classes import *


def download_asset(cdnurl: str, filehash: str, useragent: str, save_destination: Path) -> Optional[bytes]:
	assetbinary = downloader.download_asset(cdnurl, filehash, useragent)
	if not assetbinary:
		print(f'ERROR: Cound not download asset {filehash} to {save_destination}.')
		return False

	save_destination.parent.mkdir(parents=True, exist_ok=True)
	with open(save_destination, 'wb') as f:
		f.write(assetbinary)
	return assetbinary

def remove_asset(filepath: Path):
	if filepath.exists():
		filepath.unlink()
	else:
		print(f"WARN: Tried to remove non-existant asset at {filepath}")


def compare_hashes(oldhashes: Iterable[HashRow], newhashes: Iterable[HashRow]) -> dict[str, CompareResult]:
	results = dict()
	for hashrow in newhashes:
		results[hashrow.filepath] = CompareResult(None, hashrow, CompareType.New)

	for hashrow in oldhashes or []:
		res: CompareResult = results.get(hashrow.filepath)
		if res is None:
			results[hashrow.filepath] = CompareResult(hashrow, None, CompareType.Deleted)
		elif hashrow == res.new_hash:
			res.current_hash = hashrow
			res.compare_type = CompareType.Unchanged
		else: # file has changed
			res.current_hash = hashrow
			res.compare_type = CompareType.Changed
	return results


def update_assets(version_type: VersionType, cdnurl: str, newhashes: Iterable[HashRow], userconfig: UserConfig, client_directory: Path) -> list[UpdateResult]:
	oldhashes = versioncontrol.load_hash_file(version_type, client_directory)
	comparison_results = compare_hashes(oldhashes, newhashes)

	assetbasepath = Path(client_directory, 'AssetBundles')
	update_files = list(filter(lambda r: r.compare_type != CompareType.Unchanged, comparison_results.values()))
	update_results = [UpdateResult(r, DownloadType.No, Path(assetbasepath, r.new_hash.filepath)) for r in filter(lambda r: r.compare_type == CompareType.Unchanged, comparison_results.values())]

	fileamount = len(update_files)
	for i, result in enumerate(update_files, 1):
		if result.compare_type in [CompareType.New, CompareType.Changed]:
			print(f'Downloading {result.new_hash.filepath} ({i}/{fileamount}).')
			assetpath = Path(assetbasepath, result.new_hash.filepath)
			if download_asset(cdnurl, result.new_hash.md5hash, userconfig.useragent, assetpath):
				update_results.append(UpdateResult(result, DownloadType.Success, assetpath))
			else:
				update_results.append(UpdateResult(result, DownloadType.Failed, assetpath))

		elif result.compare_type == CompareType.Deleted:
			print(f'Deleting {result.current_hash.filepath} ({i}/{fileamount}).')
			assetpath = Path(assetbasepath, result.current_hash.filepath)
			remove_asset(assetpath)
			update_results.append(UpdateResult(result, DownloadType.Removed, assetpath))
	return update_results

def download_hashes(version_result: VersionResult, cdnurl: str, userconfig: UserConfig):
	hashes = downloader.download_hashes(cdnurl, version_result.rawstring, userconfig.useragent)
	if not hashes:
		sys.exit('The server did not give a proper response, exiting update routine.')

	# hash filter function
	def _filter(row: HashRow):
		for path in userconfig.download_filter:
			if row.filepath.startswith(path):
				if not userconfig.download_isblacklist:
					return True
		return userconfig.download_isblacklist

	return filter(_filter, versioncontrol.parse_hash_rows(hashes))

def update(version_result: VersionResult, cdnurl: str, userconfig: UserConfig, client_directory: Path) -> list[UpdateResult]:
	oldversion = versioncontrol.load_version_string(version_result.version_type, client_directory)
	if oldversion != version_result.version:
		print(f'{version_result.version_type.name}: Current version {oldversion} is older than latest version {version_result.version}.')
		hashes = download_hashes(version_result, cdnurl, userconfig)
		update_results = update_assets(version_result.version_type, cdnurl, hashes, userconfig, client_directory)

		hashes_updated = []
		for update_result in update_results:
			if update_result.download_type in [DownloadType.Success, DownloadType.No]:
				hashes_updated.append(update_result.compare_result.new_hash)
			elif update_result.download_type == DownloadType.Failed:
				hashes_updated.append(update_result.compare_result.current_hash)
		versioncontrol.update_version_data2(version_result, client_directory, hashes_updated)
		return update_results
	else:
		print(f'{version_result.version_type.name}: Current version {oldversion} is latest.')