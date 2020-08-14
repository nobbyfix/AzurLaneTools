import socket, json
from argparse import ArgumentParser
from pathlib import Path

import protobuf, versioncontrol, updater
from classes import Client, UserConfig


def get_sc10801(gateip, gateport):
	cs10800 = protobuf.BasicCommand(10800)
	cs10800.pb.State = 21
	cs10800.pb.Platform = "0"

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((gateip, gateport))
	s.send(protobuf.serialize_pb(cs10800))
	return protobuf.deserialize_pb(s.recv(1024))


def load_client_config(client:Client):
	with open('client_config.json', 'r', encoding='utf8') as f:
		configdata = json.load(f)
		if not client.name in configdata: raise NotImplementedError(f'Client {client.name} has not been configured yet.')
		return configdata[client.name]


def load_user_config():
	configpath = Path('user_config.json')
	if not configpath.exists():
		print('User config file has not been found. This is normal on the first startup.')
		return create_user_config()

	with open('user_config.json', 'r', encoding='utf8') as f:
		configdata = json.load(f)
		useragent = configdata.get('useragent')
		if not useragent:
			return create_user_config()
		return UserConfig(useragent)

def create_user_config():
	useragent = input('Type your desired useragent: ')
	uconfig = UserConfig(useragent)
	save_user_config(uconfig)
	return uconfig

def save_user_config(userconfig:UserConfig):
	with open('user_config.json', 'w', encoding='utf8') as f:
		configdata = {'useragent':userconfig.useragent}
		json.dump(configdata, f)


def main(client:Client):
	config = load_client_config(client)
	GATE_IP = config['gateip']
	GATE_PORT = config['gateport']
	CDN_URL = config['cdnurl']
	USERAGENT = load_user_config().useragent

	CLIENTPATH = Path('ClientAssets', client.name)
	if not CLIENTPATH.parent.exists(): CLIENTPATH.parent.mkdir(parents=True)

	sc10801 = get_sc10801(GATE_IP, GATE_PORT)
	versionlist = [versioncontrol.parse_version_string(v) for v in sc10801.pb.Version if v.startswith('$')]
	for vresult in versionlist:
		updater.update(vresult, CDN_URL, USERAGENT, CLIENTPATH)

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
		exit(1)