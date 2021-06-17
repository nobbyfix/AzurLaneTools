import json
import subprocess
from enum import Enum
from pathlib import Path


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

	@staticmethod
	def from_locale(locale):
		for client in Client:
			if client.locale_code == locale:
				return client


def dump_json(target_path, content):
	with open(target_path, "w", encoding="utf8") as f:
		json.dump(content, f, indent=2, ensure_ascii=False)


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
	if json_string.startswith("null"):
		return

	# parse json, if its empty (or an empty structure), skip
	if not (json_data := json.loads(json_string)):
		return

	savedest.parent.mkdir(parents=True, exist_ok=True)
	dump_json(savedest, json_data)