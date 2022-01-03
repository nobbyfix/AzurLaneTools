import sys
from pathlib import Path
from enum import Enum, auto
from mwclient import APIError

from lib import WikiHelper


class UploadResult(Enum):
	SUCCESS = auto()
	FAILURE = auto()
	FAILURE_SAME = auto()
	WARNING_EXIST = auto()
	WARNING_DELETED = auto()
	WARNING_SIMILAR_NAME = auto()


def do_upload(wikiclient: WikiHelper.WikiClient, *args, **kwargs) -> UploadResult:
	try:
		result = wikiclient.execute(wikiclient.mwclient.upload, *args, **kwargs)
	except APIError as error:
		# handle additional duplicate error otherwise raise the exception again
		if error.code == 'fileexists-no-change':
			print('Is duplicate, skipping.')
			return UploadResult.FAILURE_SAME
		raise error

	# handle other return type
	if 'upload' in result:
		result = result['upload']

	if result:
		if result['result'] == 'Success':
			print('Done.')
			return UploadResult.SUCCESS

		if result['result'] == 'Warning':
			if 'exists' in result['warnings']:
				if not (('no-change' in result['warnings']) or ('duplicate-version' in result['warnings'])):
					return UploadResult.WARNING_EXIST
				print("Warning (exists):")
				print(result)
			elif 'was-deleted' in result['warnings']:
				print("Waning: File was previously deleted.")
				i = input("Retry uploading? (y/n): ")
				if i.lower() == 'y':
					return UploadResult.WARNING_DELETED
			elif 'page-exists' in result['warnings']:
				print("Waning: File page already exists, but has no file.")
				i = input("Retry uploading? (y/n): ")
				if i.lower() == 'y':
					return UploadResult.WARNING_EXIST
			elif 'exists-normalized' in result['warnings']:
				return UploadResult.WARNING_SIMILAR_NAME
			else:
				print("Warning:")
				print(result)

		else:
			print('Failed with Unknown Error:')
			print(result)

	else:
		print('Failed to upload.')
	return UploadResult.FAILURE

def upload_file(wikiclient: WikiHelper.WikiClient, filepath: Path):
	print(f'Uploading {filepath.name}... ', end='')
	result = do_upload(wikiclient, open(filepath, 'rb'), filename=filepath.name)
	while True:
		if result in (UploadResult.SUCCESS, UploadResult.FAILURE, UploadResult.FAILURE_SAME):
			break
		if result in (UploadResult.WARNING_EXIST, UploadResult.WARNING_DELETED, UploadResult.WARNING_SIMILAR_NAME):
			result = do_upload(wikiclient, open(filepath, 'rb'), filename=filepath.name, ignore=True)


def main():
	wikiclient = WikiHelper.WikiClient().login()
	args = sys.argv[1:]

	for arg in args:
		argpath = Path(arg)
		if not argpath.exists():
			print(f"Input File {arg} does not exist.")
			continue

		if argpath.is_dir():
			for fp in argpath.rglob("*"):
				upload_file(wikiclient, fp)
		else:
			upload_file(wikiclient, argpath)

if __name__ == "__main__":
	main()