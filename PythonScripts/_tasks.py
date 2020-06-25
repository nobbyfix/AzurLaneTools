from argparse import ArgumentParser
from AzurLane import Client
import WikiHelper, Utility

def tasks(client, taskids):
	JsonAPI = Utility.defaultJsonAPI()
	task_data_template = JsonAPI.load_sharecfg('task_data_template', client)

	for taskid in taskids:
		task = task_data_template.get(str(taskid))
		if not task:
			raise ValueError(f'Client {client.name} has no task with id {taskid}.')

		task_desc = task['desc'].strip()
		if '\n' in task_desc: task_desc = task_desc.replace('\n', '')
		awards_out = [WikiHelper.award_to_display(JsonAPI.load_award(*award)) for award in task.get('award_display')]
		awards_out = ' '.join(awards_out)
		yield task_desc, awards_out

def main():
	parser = ArgumentParser()
	parser.add_argument('taskids', metavar='INDEX', type=int, nargs='+', help='a list of indexes from sharecfg/task_data_template')
	parser.add_argument('-c', '--client', required=True, help='client to gather information from')
	parser.add_argument('-f', '--file', metavar='FILENAME', default='tasks', type=str, help='file to save to, default is "tasks"')
	args = parser.parse_args()
	
	client = Client[args.client]
	task_generator = tasks(client, args.taskids)
	result_strings = [f'| {desc}\n| {awards}' for desc, awards in task_generator]
	Utility.output(args.file, '{|\n' + '\n|-\n'.join(result_strings) + '\n|}')

if __name__ == "__main__":
	main()