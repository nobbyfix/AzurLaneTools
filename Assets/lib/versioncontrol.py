from pathlib import Path
from typing import Optional

from .classes import VersionType, VersionResult


version_hash_name = {
	'azhash': VersionType.AZL,
	'cvhash': VersionType.CV,
	'l2dhash': VersionType.L2D,
	'pichash': VersionType.PIC,
	'bgmhash': VersionType.BGM,
}
version_file_suffix = {
	VersionType.AZL: '',
	VersionType.CV: '-cv',
	VersionType.L2D: '-live2d',
	VersionType.PIC: '-pic',
	VersionType.BGM: '-bgm',
}


def parse_version_string(rawstring: str) -> VersionResult:
	parts = rawstring.split('$')[1:]
	versionname = parts[0]
	versiontype = version_hash_name.get(versionname)
	if not versiontype:
		raise NotImplementedError(f'Unknown versionname {versionname}.')

	if versiontype == VersionType.AZL:
		version = '.'.join(parts[1:-1])
		return VersionResult(version, parts[-1], rawstring, versiontype)
	return VersionResult(parts[1], parts[2], rawstring, versiontype)


def load_version_string(version_type: VersionType, relative_parent_dir: Path) -> Optional[str]:
	fname = 'version'+version_file_suffix[version_type]+'.txt'
	fpath = Path(relative_parent_dir, fname)
	if fpath.exists():
		with open(fpath, 'r') as f:
			return f.read()

def save_version_string(version_type: VersionType, relative_parent_dir: Path, content: str):
	fname = 'version'+version_file_suffix[version_type]+'.txt'
	with open(Path(relative_parent_dir, fname), 'w') as f:
		f.write(content)

def save_version_string2(version_result: VersionResult, relative_parent_dir: Path):
	save_version_string(version_result.version_type, relative_parent_dir, version_result.version)


def load_hash_file(version_type: VersionType, relative_parent_dir: Path) -> Optional[str]:
	fname = 'hashes'+version_file_suffix[version_type]+'.csv'
	fpath = Path(relative_parent_dir, fname)
	if fpath.exists():
		with open(fpath, 'r') as f:
			return f.read()

def save_hash_file(version_type: VersionType, relative_parent_dir: Path, content: str):
	fname = 'hashes'+version_file_suffix[version_type]+'.csv'
	with open(Path(relative_parent_dir, fname), 'w') as f:
		f.write(content)

def update_version_data(version_type: VersionType, relative_parent_dir: Path, version_string: str, hashes: str):
	save_version_string2(version_type, relative_parent_dir, version_string)
	save_hash_file(version_type, relative_parent_dir, hashes)

def update_version_data2(version_result: VersionResult, relative_parent_dir: Path, hashes: str):
	save_version_string2(version_result, relative_parent_dir)
	save_hash_file(version_result.version_type, relative_parent_dir, hashes)