from argparse import ArgumentParser

from lib import ALJsonAPI, Client, WikiHelper, Utility


EQUIPMENTTYPE_USAGE = {
	1: '{{DD}} DD Main Gun',
	2: '{{CL}} CL Main Gun',
	3: '{{CA}} CA Main Gun',
	4: '{{BB}} BB Main Gun',
	5: '{{Torpedo}} Torpedo',
#	6: 'AA Gun',
	7: '{{CV}} Fighter',
	8: '{{CV}} Torpedo Bomber',
	9: '{{CV}} Dive Bomber',
#	10: 'Auxiliary',
#	11: None,
	12: '{{CV}} Seaplane',
	13: '{{Torpedo}} Sub Torpedo',
#	14: 'Auxiliary',
	15: '{{CV}} ASW Plane',
#	17: 'Helicopter'
}


api = ALJsonAPI()

def equipment_skin(client, eqid):
	equip_skin_template = api.get_sharecfgmodule('equip_skin_template')
	eqskin = equip_skin_template.load_client(eqid, client)
	if not eqskin: raise ValueError(f'Equipment skinid {eqid} does not exist.')

	name = eqskin['name'].strip()
	icon = eqskin['icon']
	desc = eqskin['desc'].strip()
	usages = [EQUIPMENTTYPE_USAGE[eqtype] for eqtype in eqskin['equip_type'] if eqtype in EQUIPMENTTYPE_USAGE]
	return WikiHelper.simple_template('EquipSkinRow', [name, icon, desc, '<br>'.join(usages)])

def equipment_theme_skinlist(client, skinids:list):
	theme_skins = [equipment_skin(client, eqskinid) for eqskinid in skinids]
	return '\n'.join(theme_skins)

def equipment_theme(client, themeid):
	equip_skin_theme_template = api.get_sharecfgmodule('equip_skin_theme_template')
	theme = equip_skin_theme_template.load_client(themeid, client)
	if not theme: raise ValueError(f'Equipment theme {themeid} does not exist.')
	
	themename = theme['name'].strip()
	skinlist = equipment_theme_skinlist(client, theme['ids'])
	return WikiHelper.simple_template('EquipSkinHeader', [themename])+'\n'+skinlist+'\n|}'

def main():
	parser = ArgumentParser()
	parser.add_argument('themeids', metavar='INDEX', type=int, nargs='+', help='a list of indexes from sharecfg/equip_skin_theme_template')
	parser.add_argument('-c', '--client', required=True, help='client to gather information from')
	args = parser.parse_args()
	
	client = Client[args.client]
	themes = [equipment_theme(client, themeid) for themeid in args.themeids]
	Utility.output('\n'.join(themes))

if __name__ == "__main__":
	main()