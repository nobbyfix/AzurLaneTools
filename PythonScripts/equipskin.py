from argparse import ArgumentParser
from typing import Union

from lib import ALJsonAPI, Client, WikiHelper, Utility
from lib.apiclasses import BackyardTheme


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

def equipment_theme_skinlist(client, skinids: list):
	theme_skins = [equipment_skin(client, eqskinid) for eqskinid in skinids]
	return '\n'.join(theme_skins)

def equipment_theme(client, theme: BackyardTheme) -> str:
	skinlist = equipment_theme_skinlist(client, theme['ids'])
	return WikiHelper.simple_template('EquipSkinHeader', [theme.name])+'\n'+skinlist+'\n|}'

def get_theme_from_id(client: Client, themeid: Union[str, int]) -> BackyardTheme:
	equip_skin_theme_template = api.get_sharecfgmodule('equip_skin_theme_template')
	theme = equip_skin_theme_template.load_client(themeid, client)
	if not theme:
		raise ValueError(f'Equipment theme {themeid} does not exist.')
	return theme

def get_theme_from_name(client: Client, themename: str) -> BackyardTheme:
	equip_skin_theme_template = api.get_sharecfgmodule('equip_skin_theme_template')
	for theme in equip_skin_theme_template.all_client(client):
		if theme.name == themename:
			return theme
	raise ValueError(f"Equipment theme with name '{themename}' does not exist.")

def main():
	parser = ArgumentParser()
	parser.add_argument('-i', '--themeids', type=int, nargs='*', default=[],
		help='a list of indexes from sharecfg/equip_skin_theme_template')
	parser.add_argument('-n', '--themenames', type=str, nargs='*', default=[],
		help='a list of names of themes from sharecfg/equip_skin_theme_template')
	parser.add_argument('-c', '--client', required=True, help='client to gather information from')
	args = parser.parse_args()

	client = Client[args.client]

	themes = [get_theme_from_id(client, themeid) for themeid in args.themeids]
	themes.extend([get_theme_from_name(client, themename) for themename in args.themenames])

	formatted_themes = [equipment_theme(client, theme) for theme in themes]
	Utility.output('\n'.join(formatted_themes))

if __name__ == "__main__":
	main()
