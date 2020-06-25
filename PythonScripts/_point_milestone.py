from argparse import ArgumentParser
from AzurLane import Client
import WikiHelper, Utility

def milestone(client, event_id:int, pt_filename:str, columns:int=3) -> str:
	JsonAPI = Utility.defaultJsonAPI()
	activity_event_pt = JsonAPI.load_sharecfg('activity_event_pt', client)
	event_milestone = activity_event_pt[str(event_id)]
	# a little dirty, but the easiest way to get the name of event points
	pt_name = JsonAPI.load_award(1, event_milestone['pt']).name.strip()

	wikitext = '{| class="wikitable" style="text-align:center"\n'
	for _ in range(columns):
		wikitext += '!'+WikiHelper.put_icon(pt_filename+'.png', pt_name, nolink=True)+'\n!Reward\n'

	point_targets = event_milestone['target'] # point targets to reach to receive rewards
	for targetid in range(0, len(point_targets)):
		# go to next row every x columns
		if (targetid % columns) == 0: wikitext += '|-\n'
		awarddata = event_milestone['drop_client'][targetid]
		wikitext += '|'+str(point_targets[targetid])+'\n'
		award = JsonAPI.load_award(*awarddata)
		wikitext += '|'+WikiHelper.award_to_display(award)+'\n'
	wikitext += '|}\n'
	return wikitext

def main():
	parser = ArgumentParser()
	parser.add_argument('eventid', metavar='INDEX', type=int, nargs=1, help='an index from sharecfg/activity_event_pt')
	parser.add_argument('-c', '--client', required=True, help='client to gather information from')
	parser.add_argument('-pt', '--pointfile', default='', type=str, help='filename of the point icon on the wiki')
	parser.add_argument('-col', '--columns', default=3, type=int, help='amount of rows to spread the data on the result wikitable, default is 3')
	parser.add_argument('-f', '--file', metavar='FILENAME', default='point_milestone', type=str, help='file to save to, default is "point_milestone"')
	args = parser.parse_args()
	
	client = Client[args.client]
	result = milestone(client, args.eventid[0], args.pointfile, args.columns)
	Utility.output(args.file, result)

if __name__ == "__main__":
	main()