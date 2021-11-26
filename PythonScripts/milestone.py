from argparse import ArgumentParser

from lib import ALJsonAPI, Client, Utility
from lib.apiclasses import ShipReward
from lib.WikiHelper import Wikifier, put_icon, simple_template


class MilestoneQuery:
	api: ALJsonAPI
	wikifier: Wikifier

	def __init__(self, api: ALJsonAPI = None, wikifier: Wikifier = None) -> None:
		if not api:
			api = ALJsonAPI()
		if not wikifier:
			wikifier = Wikifier(api)
		self.api = api
		self.wikifier = wikifier

	def get(self, client: Client, event_id: int, pt_filename: str, columns: int = 3) -> str:
		activity_event_pt = self.api.get_sharecfgmodule("activity_event_pt")
		event_milestone = activity_event_pt.load_client(event_id, client)
		if not event_milestone:
			raise ValueError(f"A milestone with id {event_id} does not exist.")

		pt_name = event_milestone.point.load(self.api, client).name
		wikitext = '{| class="wikitable" style="text-align:center"\n'
		for _ in range(columns):
			wikitext += "!"+put_icon(pt_filename, pt_name, nolink=True)+"\n!Reward\n"

		for targetid, targetnum in enumerate(event_milestone.target):
			# go to next row every x columns
			if (targetid % columns) == 0: wikitext += "|-\n"
			award = event_milestone.rewards[targetid]
			awardable = award.load(self.api, client)
			wiki_awardable = self.wikifier.wikify_awardable(awardable)

			awardable_name = wiki_awardable.name
			# add link brackets for ship rewards
			if isinstance(awardable, ShipReward):
				awardable_name = f"[[{awardable_name}]]"

			wiki_display = simple_template("Display",
				[wiki_awardable.filelink, wiki_awardable.rarity.label, f"{award.amount}x "+awardable_name])

			wikitext += "|"+str(targetnum)+"\n|"+wiki_display+"\n"
		wikitext += "|}\n"
		return wikitext

def main():
	parser = ArgumentParser()
	parser.add_argument("eventid", metavar="INDEX", type=int, nargs=1,
						help="an index from sharecfg/activity_event_pt")
	parser.add_argument("-c", "--client", required=True, choices=Client.__members__,
						help="client to gather information from")
	parser.add_argument("-pt", "--pointfile", default="Pt.png", type=str,
						help="filename of the point icon on the wiki")
	parser.add_argument("-col", "--columns", default=3, type=int,
						help="amount of rows to spread the data on the result wikitable")
	args = parser.parse_args()

	result = MilestoneQuery().get(Client[args.client], args.eventid[0], args.pointfile, args.columns)
	Utility.output(result)

if __name__ == "__main__":
	main()