from argparse import ArgumentParser
import Utility

JsonAPI = Utility.defaultJsonAPI()

def get_alternative_shipnames() -> str:
	shipnames = dict()
	activity_ins_ship_group_template = JsonAPI.load_multi_sharecfg('activity_ins_ship_group_template', JsonAPI.DEFAULT_CLIENTS)
	
	for clientdata in activity_ins_ship_group_template.values():
		for shipgroup in clientdata['all']:
			name = clientdata[str(shipgroup)]['name'].strip()
			shipname = JsonAPI.converter.get_shipname(shipgroup)
			if shipname not in shipnames:
				shipnames[shipname] = name
	
	# also add muse ships because for some reason they are used for the template
	for shipname in JsonAPI.converter.get_shipnames():
		if 'µ' not in shipname: continue
		shipname_nonmuse = shipname.replace(' µ', '')
		if shipname_nonmuse in shipnames:
			shipnames[shipname] = shipnames[shipname_nonmuse]

	return ',\n'.join([f"['{name_orig}'] = '{shipnames[name_orig]}'" for name_orig in sorted(shipnames)])

def main():
	parser = ArgumentParser()
	parser.add_argument('-f', '--file', metavar='FILENAME', type=str, default='juustagram_names', help='file to save to, default "juustagram_names"')
	args = parser.parse_args()
	Utility.output(args.file, get_alternative_shipnames())

if __name__ == "__main__":
	main()