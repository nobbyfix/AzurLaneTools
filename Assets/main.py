import sys
import json
from shutil import copy
from pathlib import Path
from argparse import ArgumentParser
import yaml

from lib import protobuf, versioncontrol, updater
from lib.classes import Client, UserConfig, ClientConfig


YAML_CONFIG_PATH = Path("config", "user_config.yml")
YAML_TEMPLATE_PATH = Path("config", "user_config_template.yml")
CLIENT_CONFIG_PATH = Path('config', 'client_config.json')

def load_user_config() -> UserConfig:
	if not YAML_CONFIG_PATH.exists():
		print("Userconfig does not exist. A new one will be created.")
		print("Note that the useragent is empty and it is advised to set one.")
		copy(YAML_TEMPLATE_PATH, YAML_CONFIG_PATH)
		return load_user_config()

	with open(YAML_CONFIG_PATH, 'r', encoding='utf8') as file:
		yamlconfig = yaml.safe_load(file)

	try:
		userconfig = UserConfig(
			useragent=yamlconfig['useragent'],
			download_isblacklist=yamlconfig['download-folder-listtype'] == 'blacklist',
			download_filter=yamlconfig['download-folder-list'],
			extract_isblacklist=yamlconfig['extract-folder-listtype'] == 'blacklist',
			extract_filter=yamlconfig['extract-folder-list'])
	except KeyError:
		print("There is an error inside the userconfig file. Delete it or change the wrong values.")
		sys.exit(1)

	return userconfig

def load_client_config(client: Client) -> ClientConfig:
	with open(CLIENT_CONFIG_PATH, 'r', encoding='utf8') as f:
		configdata = json.load(f)

	if not client.name in configdata:
		raise NotImplementedError(f'Client {client.name} has not been configured yet.')

	config = configdata[client.name]
	try:
		clientconfig = ClientConfig(config['gateip'], config['gateport'], config['cdnurl'])
	except KeyError:
		print("The clientconfig has been wrongly configured.")
		sys.exit(1)

	return clientconfig


def main(client: Client):
	userconfig = load_user_config()
	clientconfig = load_client_config(client)

	CLIENTPATH = Path('ClientAssets', client.name)
	if not CLIENTPATH.parent.exists(): CLIENTPATH.parent.mkdir(parents=True)

	version_response = protobuf.get_version_response(clientconfig.gateip, clientconfig.gateport)
	versionlist = [versioncontrol.parse_version_string(v) for v in version_response.pb.Version if v.startswith('$')]
	for vresult in versionlist:
		updater.update(vresult, clientconfig.cdnurl, userconfig.useragent, CLIENTPATH)

if __name__ == "__main__":
	parser = ArgumentParser()
	parser.add_argument('-c', '--client', help='client to update')
	args = parser.parse_args()

	clientname = args.client
	if clientname is None:
		clientname = input('Type which client to update: ')

	if clientname in Client.__members__:
		client = Client[clientname]
		main(client)
	else:
		print(f'The client {clientname} is not supported or does not exist.')
		sys.exit(1)