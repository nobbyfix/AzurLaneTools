from lib import ALJsonAPI, Constants
from lib.converter import equips_updater


if __name__ == "__main__":
	api = ALJsonAPI()
	equipcache_fp = Constants.EQUIP_CONVERT_CACHE_PATH
	wikicache_fp = Constants.EQUIP_WIKIDATA_PATH
	equips_updater.update_converter(equipcache_fp, wikicache_fp, api)