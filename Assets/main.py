import argparse
from pathlib import Path

from lib import config, protobuf, versioncontrol, updater
from lib.classes import Client


def main(client: Client, force_refresh: bool = False):
	# load config data from files
	userconfig = config.load_user_config()
	clientconfig = config.load_client_config(client)

	CLIENT_ASSET_DIR = Path(userconfig.asset_directory, client.name)
	CLIENT_ASSET_DIR.mkdir(parents=True, exist_ok=True)

	if force_refresh:
		print("All asset types will be checked for different hashes.")

	version_response = protobuf.get_version_response(clientconfig.gateip, clientconfig.gateport)
	versionlist = [versioncontrol.parse_version_string(v) for v in version_response.pb.version if v.startswith("$")]
	for vresult in versionlist:
		if update_assets := updater.update(vresult, clientconfig.cdnurl, userconfig, CLIENT_ASSET_DIR, force_refresh):
			versioncontrol.save_difflog(vresult.version_type, update_assets, CLIENT_ASSET_DIR)


if __name__ == "__main__":
	# setup argument parser
	parser = argparse.ArgumentParser()
	parser.add_argument("client", type=str, choices=Client.__members__,
		help="client to update")
	parser.add_argument("--force-refresh", type=bool, default=False, action=argparse.BooleanOptionalAction,
		help="compares asset hashes even when the version file is up to date")
	args = parser.parse_args()

	# execute
	main(Client[args.client], args.force_refresh)