from argparse import ArgumentParser
from itertools import chain
from AzurLane import Client
import WikiHelper, Utility
from _tasks import tasks

template_mdouble = WikiHelper.MultilineTemplate('MissionDouble')

def task_double(client, eventid):
	JsonAPI = Utility.defaultJsonAPI()
	activity_template = JsonAPI.load_sharecfg("activity_template", client)

	# get task_id's from activity_template
	event = activity_template.get(str(eventid))
	if not event:
		raise ValueError(f'Client {client.name} has no activity with id {eventid}.')

	tasksids = list(chain(*event["config_data"]))
	task_result = tasks(client, tasksids)
	
	task_days = []
	for i in range(0, len(tasksids)//2):
		desc1, awards1 = next(task_result)
		desc2, awards2 = next(task_result)

		# output all information in wikitext format
		content = {
			"descen1": desc1,
			"descen2": desc2,
			"reward1": awards1,
			"reward2": awards2,
			"notes": f"Day {i+1}"
		}
		task_days.append(template_mdouble.fill(content))
	return '{{MissionHeader}}\n' + '\n'.join(task_days) + '\n|}'

def main():
	parser = ArgumentParser()
	parser.add_argument('activityid', metavar='INDEX', type=int, nargs=1, help='an index from sharecfg/activity_template')
	parser.add_argument('-c', '--client', required=True, help='client to gather information from')
	parser.add_argument('-f', '--file', metavar='FILENAME', default='task_double', type=str, help='file to save to, default is "task_double"')
	args = parser.parse_args()
	
	client = Client[args.client]
	result = task_double(client, args.activityid[0])
	Utility.output(args.file, result)


if __name__ == "__main__":
	main()