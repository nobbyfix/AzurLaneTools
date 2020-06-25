from argparse import ArgumentParser
from itertools import chain
from AzurLane import Client
import WikiHelper, Utility
from _tasks import tasks

template_mission = WikiHelper.MultilineTemplate('Mission')
template_mdouble = WikiHelper.MultilineTemplate('MissionDouble')

def task_single(task_result):
	task_result = list(task_result)
	for i in range(0, len(task_result)):
		desc, awards = task_result[i]
		content = {
			"descen": desc,
			"reward": awards,
			"notes": f"Day {i+1}"
		}
		yield template_mission.fill(content)

def task_double(task_result):
	task_result = list(task_result)
	for i in range(0, len(task_result)//2):
		desc1, awards1 = task_result[i*2]
		desc2, awards2 = task_result[i*2+1]
		content = {
			"descen1": desc1,
			"descen2": desc2,
			"reward1": awards1,
			"reward2": awards2,
			"notes": f"Day {i+1}"
		}
		yield template_mdouble.fill(content)

def event_tasks(client, eventid):
	JsonAPI = Utility.defaultJsonAPI()
	activity_template = JsonAPI.load_sharecfg("activity_template", client)

	# get task_id's from activity_template
	event = activity_template.get(str(eventid))
	if not event:
		raise ValueError(f'Client {client.name} has no activity with id {eventid}.')

	taskeventids = event["config_data"]
	taskids = list(chain(*taskeventids))
	task_result = tasks(client, taskids)
	if len(taskeventids[0]) == 1:
		task_days = task_single(task_result)
	else:
		task_days = task_double(task_result)
	return '{{MissionHeader}}\n' + '\n'.join(task_days) + '\n|}'

def main():
	parser = ArgumentParser()
	parser.add_argument('activityid', metavar='INDEX', type=int, nargs=1, help='an index from sharecfg/activity_template')
	parser.add_argument('-c', '--client', required=True, help='client to gather information from')
	parser.add_argument('-f', '--file', metavar='FILENAME', default='tasks_event', type=str, help='file to save to, default is "tasks_event"')
	args = parser.parse_args()
	
	client = Client[args.client]
	result = event_tasks(client, args.activityid[0])
	Utility.output(args.file, result)

if __name__ == "__main__":
	main()