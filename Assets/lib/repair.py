import hashlib
import itertools
from pathlib import Path
from typing import Generator

from lib import updater, versioncontrol
from lib.classes import HashRow, UserConfig, VersionType


def calc_md5hash(filepath: Path, buf_size: int = 65536):
	md5 = hashlib.md5()
	with open(filepath, 'rb') as f:
		while data := f.read(buf_size):
			md5.update(data)
	return md5.hexdigest()

def hashrows_from_files(client_directory: Path) -> Generator[HashRow, None, None]:
	assetbasepath = Path(client_directory, "AssetBundles")
	for filepath in assetbasepath.rglob("*"):
		if not filepath.is_dir():
			current_md5 = calc_md5hash(filepath)
			current_size = filepath.stat().st_size

			clean_filepath = str(filepath.relative_to(assetbasepath)).replace("\\", "/")
			yield HashRow(clean_filepath, current_size, current_md5)

def repair(cdnurl: str, userconfig: UserConfig, client_directory: Path):
	current_hashes = hashrows_from_files(client_directory)
	expected_hashes = itertools.chain(*[versioncontrol.load_hash_file(vtype, client_directory) for vtype in VersionType])
	comparison_results = updater.compare_hashes(current_hashes, expected_hashes)

	update_results = updater.update_assets(cdnurl, comparison_results, userconfig, client_directory)
	return update_results
