import os
from pathlib import Path

from . import downloader, versioncontrol
from .classes import CompareType, CompareResult, VersionType, VersionResult


def download_asset(cdnurl, filehash, useragent, save_destination):
	assetbinary = downloader.download_asset(cdnurl, filehash, useragent)
	if not assetbinary:
		print(f'ERROR: Cound not download asset {filehash} to {save_destination}.')
		return
	save_destination.parent.mkdir(parents=True, exist_ok=True)
	with open(save_destination, 'wb') as f:
		f.write(assetbinary)
	return assetbinary

def remove_asset(filepath:Path):
	if filepath.exists():
		filepath.unlink()
	else:
		print(f"WARN: Tried to remove non-existant asset at {filepath}")

def compare_hashes(oldhashes, newhashes):
	results = dict()
	for assetinfo in newhashes.splitlines():
		if assetinfo == '': continue
		path, size, md5hash = assetinfo.split(',')
		res = CompareResult(path, size, size, md5hash, md5hash, CompareType.New)
		results[path] = res

	if oldhashes:
		for assetinfo in oldhashes.splitlines():
			if assetinfo == '': continue
			path, size, md5hash = assetinfo.split(',')
			res = results.get(path)
			if res is None:
				res = CompareResult(path, size, 0, md5hash, None, CompareType.Deleted)
				results[path] = res
			elif res.size != size or res.md5hash != md5hash:
				res.size = size
				res.md5hash = md5hash
				res.compare_type = CompareType.Changed
				results[path] = res
			else:
				results.pop(path) # remove if file is unchanged
	return results


def update_assets(cdnurl, newhashes, useragent, client_directory: Path):
	oldhashes = versioncontrol.load_hash_file(VersionType.AZL, client_directory)
	comparison_results = compare_hashes(oldhashes, newhashes)

	assetbasepath = Path(client_directory, 'AssetBundles')
	version_diff_output = {t: [] for t in CompareType}
	for result in comparison_results.values():
		version_diff_output[result.compare_type].append(result.filepath)
		assetpath = Path(assetbasepath, result.filepath)
		if result.compare_type == CompareType.New:
			download_asset(cdnurl, result.md5hash_new, useragent, assetpath)
		elif result.compare_type == CompareType.Changed:
			download_asset(cdnurl, result.md5hash_new, useragent, assetpath)
		elif result.compare_type == CompareType.Deleted:
			remove_asset(assetpath)
	
	for comp_type, filepaths in version_diff_output.items():
		fileoutpath = Path(client_directory, 'diff_'+comp_type.name.lower()+'.txt')
		with open(fileoutpath, 'w', encoding='utf8') as f:
			f.write('\n'.join(filepaths))

def update(version_result: VersionResult, cdnurl, useragent, client_directory: Path):
	oldversion = versioncontrol.load_version_string(version_result.version_type, client_directory)
	if oldversion != version_result.version:
		hashes = downloader.download_hashes(cdnurl, version_result.rawstring, useragent)

		if version_result.version_type == VersionType.AZL:
			update_assets(cdnurl, hashes, useragent, client_directory)

		versioncontrol.save_version_string(version_result, client_directory)
		versioncontrol.save_hash_file(version_result.version_type, client_directory, hashes)