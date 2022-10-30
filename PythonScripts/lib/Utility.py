import sys
from os import PathLike
from typing import Any, Iterable
from pathlib import Path


def rreplace(s: str, old: str, new: str, occurrence: int) -> str:
	"""
	reverse replacement for strings
	"""
	li = s.rsplit(old, occurrence)
	return new.join(li)

def mkdir(directory: Path) -> None:
	"""
	faster than simply calling os.makedirs with exists_ok=True
	if the same directory gets checked even after its creation
	"""
	if not directory.exists():
		directory.mkdir(parents=True, exist_ok=True)

def mkdirf(file: Path) -> None:
	"""
	faster than simply calling os.makedirs with exists_ok=True
	if the same directory gets checked even after its creation
	"""
	mkdir(file.parent)

def output(text: str, filepath: PathLike = None) -> None:
	"""
	Tries to print the output to console, if it fails write it to the specified file in the output directory.
	"""
	try:
		print(text)
	except UnicodeEncodeError:
		if filepath:
			fpath = Path(filepath)
		else:
			fpath = Path("output", Path(sys.argv[0]).stem + ".wikitext")

		mkdirf(fpath)
		with open(fpath, 'w', encoding='utf8') as f:
			f.write(text)
		print("Failed to print to console, output has been written into output directory.")

def dict_args_query(dict_input: dict, *args) -> Any:
	"""
	Recursively searches a dict for the given list of keys.
	"""
	for arg in args:
		if isinstance(dict_input, dict):
			dict_input = dict_input.get(arg)
			if not dict_input: return
	return dict_input

def pop_zeros(items: Iterable) -> Iterable:
	while items and items[-1] == 0:
		del items[-1]
	return items
