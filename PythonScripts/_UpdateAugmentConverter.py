from lib import ALJsonAPI, Constants
from lib.converter import augments_updater


def main():
	api = ALJsonAPI()
	augmentcache_fp = Constants.AUGMENT_CONVERT_CACHE_PATH
	augments_updater.update_converter(augmentcache_fp, api)

if __name__ == "__main__":
	main()
