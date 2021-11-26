from lib import ALJsonAPI, Constants
from lib.converter import ships_updater


if __name__ == "__main__":
	api = ALJsonAPI()
	convert_fp = Constants.SHIPID_CONVERT_CACHE_PATH
	override_fp = Constants.SHIPID_CONVERT_OVERRIDE_PATH
	ships_updater.update_converter(convert_fp, override_fp, api)