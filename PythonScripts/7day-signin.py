from argparse import ArgumentParser

from lib import ALJsonAPI, Client, WikiHelper, Utility
from lib.apiclasses import Award, ShipReward


def award_to_display(award: Award, wikifier: WikiHelper.Wikifier, client: Client) -> str:
	awardable = award.load_first(wikifier.api, client)
	wiki_awardable = wikifier.wikify_awardable(awardable)

	awardable_name = wiki_awardable.name
	# add link brackets for ship rewards
	if isinstance(awardable, ShipReward):
		awardable_name = f"[[{awardable_name}]]"

	wiki_display = WikiHelper.simple_template("Display",
		[wiki_awardable.filelink, wiki_awardable.rarity.label, f"{award.amount}x "+awardable_name])
	return wiki_display

def seven_day_signin(loginid: int, wikifier: WikiHelper.Wikifier, client: Client = None):
	client = [client] or Client

	activity_7_day_sign = wikifier.api.get_sharecfgmodule("activity_7_day_sign")
	signin_data = activity_7_day_sign.load_first(loginid, client)
	if not signin_data:
		client_names = ', '.join([c.name for c in client])
		raise ValueError(f"loginid {loginid} does not exist for clients '{client_names}'.")

	award_displays = [award_to_display(award, wikifier, client) for award in signin_data.front_drops]
	return '\n'.join(award_displays)

def main():
	parser = ArgumentParser()
	parser.add_argument("-c", "--client", choices=Client.__members__, default = "EN",
						help="client to gather information from (default: EN)")
	parser.add_argument('loginid', metavar='INDEX', type=int, nargs=1,
						help='an index from sharecfg/activity_7_day_sign')
	args = parser.parse_args()
	
	client = Client[args.client]
	api = ALJsonAPI()
	wikifier = WikiHelper.Wikifier(api)

	wikitext = seven_day_signin(args.loginid[0], wikifier, client)
	Utility.output(wikitext)

if __name__ == "__main__":
	main()
