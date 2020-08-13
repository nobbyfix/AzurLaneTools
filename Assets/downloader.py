import requests

def download_hashes(cdnurl, versionhash, useragent):
	response = requests.get(f'{cdnurl}/android/hash/{versionhash}', headers={'user-agent': useragent})
	if response.status_code == 200:
		return response.text

def download_asset(cdnurl, filehash, useragent):
	response = requests.get(f'{cdnurl}/android/resource/{filehash}', headers={'user-agent': useragent})
	if response.status_code == 200:
		return response.content