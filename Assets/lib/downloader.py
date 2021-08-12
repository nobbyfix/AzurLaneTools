import requests


def download_hashes(cdnurl, versionhash, useragent):
	while True:
		try:
			response = requests.get(f'{cdnurl}/android/hash/{versionhash}', headers={'user-agent': useragent}, timeout=30)
			break
		except TimeoutError:
			print("Hash request timed out, retrying.")

	if response.status_code == 200:
		return response.text

def download_asset(cdnurl, filehash, useragent):
	while True:
		try:
			response = requests.get(f'{cdnurl}/android/resource/{filehash}', headers={'user-agent': useragent}, timeout=20)
			break
		except TimeoutError:
			print("Asset request timed out, retrying.")

	if response.status_code == 200:
		return response.content