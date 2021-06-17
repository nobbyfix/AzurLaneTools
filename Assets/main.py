import sys
from pathlib import Path
from argparse import ArgumentParser

from lib import config, protobuf, versioncontrol, updater
from lib.classes import Client


def main(client: Client):
	# load config data from files
	userconfig = config.load_user_config()
	clientconfig = config.load_client_config(client)

	CLIENT_ASSET_DIR = Path("ClientAssets", client.name)
	if not CLIENT_ASSET_DIR.exists():
		CLIENT_ASSET_DIR.mkdir(parents=True)

	version_response = protobuf.get_version_response(clientconfig.gateip, clientconfig.gateport)
	versionlist = [versioncontrol.parse_version_string(v) for v in version_response.pb.Version if v.startswith("$")]
	for vresult in versionlist:
		updater.update(vresult, clientconfig.cdnurl, userconfig.useragent, CLIENT_ASSET_DIR)

if __name__ == "__main__":
	# setup argument parser
	parser = ArgumentParser()
	parser.add_argument("client", metavar="CLIENT", type=str, help="client to update")
	args = parser.parse_args()

	# parse arguments
	clientname = args.client
	if not clientname in Client._member_names_:
		sys.exit(f"The client {clientname} is not supported or does not exist.")
	client = Client[clientname]

	# execute
	main(client)
