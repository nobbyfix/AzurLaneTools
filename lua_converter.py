import json
import shutil
import subprocess
from enum import Enum
from pathlib import Path
import multiprocessing as mp


class Client(Enum):
	locale_code: str

	def __new__(cls, value, locale):
		obj = object.__new__(cls)
		obj._value_ = value
		obj.locale_code = locale
		return obj

	EN = (1, "en-US")
	CN = (2, "zh-CN")
	JP = (3, "ja-JP")
	KR = (4, "ko-KR")
	TW = (5, "zh-TW")


directory_destinations = [
	(Path("sharecfg"), "sharecfg"),
	(Path("gamecfg", "buff"),  "buff"),
	(Path("gamecfg", "dungeon"), "dungeon"),
	(Path("gamecfg", "skill"), "skill"),
	(Path("gamecfg", "story"), "story"),
]


def convert_lua(filepath: Path, savedest: Path):
	if "sharecfg" in filepath.parts:
		# if file is also modified to contain function blocks, remove them
		modified_file = False
		with open(filepath, "r", encoding="utf8") as f:
			content = f.read()
		if "function ()" in content and "end()" in content:
			content_replaced = content.replace("function ()", "").replace("end()", "")
			with open(filepath, "w", encoding="utf8") as f:
				f.write(content_replaced)
			modified_file = True

		# convert the file
		try:
			result = subprocess.check_output(["lua", "serializer.lua",
				str(filepath.with_suffix("")), filepath.stem], stderr=subprocess.DEVNULL)
		except: return
		finally:
			# revert the file, even if it fails to convert them
			if modified_file:
				with open(filepath, "w", encoding="utf8") as f:
					f.write(content)

	# convert non-sharecfg files with other lua serializer script
	else:
		try:
			result = subprocess.check_output(["lua", "serializer2.lua",
				str(filepath.with_suffix(""))], stderr=subprocess.DEVNULL)
		except: return

	json_string = result.decode("utf8")
	if json_string.startswith("null"): return

	json_data = json.loads(json_string)
	# if the parsed json is empty (or an empty structure), don't save that
	if not json_data: return
	json_string = json.dumps(json_data, indent=2, ensure_ascii=False)

	savedest.parent.mkdir(parents=True, exist_ok=True)
	with open(savedest, "w", encoding="utf8") as jfile:
		jfile.write(json_string)

# wrapper to pass into multiprocessing.Pool functions
_convert_lua = lambda args: convert_lua(*args)


def main():
	client_input = input("Type the game version to convert: ")
	if not client_input in Client.__members__:
		print(f"Unknown client {client_input}, aborting.")
		return
	client = Client[client_input]

	with mp.Pool(processes=mp.cpu_count()) as pool:
		for DIR_FROM, DIR_TO in directory_destinations:
			# jp has different folder for story files
			if DIR_FROM.name == "story" and client_input == "JP":
				DIR_FROM = DIR_FROM.with_name(DIR_FROM.name+"jp")

			# set path constants
			CONVERT_FROM = Path("Src", client.locale_code, DIR_FROM)
			CONVERT_TO = Path("SrcJson", client_input, DIR_TO)

			# find all files inside the folder
			for file in CONVERT_FROM.rglob("*.lua"):
				target = Path(CONVERT_TO, file.relative_to(CONVERT_FROM).with_suffix(".json"))
				pool.apply_async(convert_lua, (file, target,))
		pool.close()
		pool.join()

	# merge sublisted sharecfg files
	SHARECFG_JSON_FOLDER = Path("SrcJson", client_input, "sharecfg")
	for filetarget in SHARECFG_JSON_FOLDER.glob("*.json"):
		with open(filetarget, "r", encoding="utf8") as f:
			sharecfg_content = json.load(f)

		# check if sharecfg file is splitted
		if "subList" in sharecfg_content and "subFolderName" in sharecfg_content:
			subdir = Path(SHARECFG_JSON_FOLDER, sharecfg_content["subFolderName"].lower())
			json_content = {}

			# iterate over all subfiles
			for subfilename in sharecfg_content["subList"]:
				subfile = Path(subdir, subfilename+".json")
				if not subfile.exists(): continue

				with open(subfile, "r", encoding="utf8") as sf:
					subcontent = json.load(sf)
				json_content = json_content | subcontent

			# copy all other data over
			for k in sharecfg_content:
				if k not in ("subList", "subFolderName", "indexs"):
					json_content[k] = sharecfg_content[k]

			# save it all into a single file
			with open(filetarget, "w", encoding="utf8") as f:
				json.dump(json_content, f, indent=2, ensure_ascii=False)

			# remove sublistfolder after the data has been merged
			shutil.rmtree(subdir, ignore_errors=True)


if __name__ == "__main__":
	main()