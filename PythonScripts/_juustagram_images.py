import os, requests
from argparse import ArgumentParser
from AzurLane import Client
import Utility

JsonAPI = Utility.defaultJsonAPI()

def download_image(client, ins_template_id:int, filename:str=None):
	activity_ins_template = JsonAPI.load_sharecfg('activity_ins_template', client)
	if not ins_template_id in activity_ins_template['all']:
		raise ValueError(f'Client {client.name} has no juustagram with id {ins_template_id}.')
	
	ins_post = activity_ins_template[str(ins_template_id)]
	img_link = ins_post['picture_persist']
	if img_link == '':
		print(f'For client {client.name}, juustagram post {ins_template_id} has no picture.')
		return
	
	if not filename:
		filename = 'Juustagram_'+str(ins_template_id)+'.png'
	filepath = os.path.join('output', 'juustagram', filename)

	Utility.makedirsf(filepath)
	with open(filepath,'wb') as f:
		f.write(requests.get(img_link).content)

def download_all_images(client, start=1):
	activity_ins_template = JsonAPI.load_sharecfg('activity_ins_template', client)
	all_ids = activity_ins_template['all']
	for ins_template_id in filter(lambda x: x >= start, all_ids):
		download_image(client, ins_template_id)

def main():
	parser = ArgumentParser()
	parser.add_argument('-c', '--client', required=True, help='client to gather information from')
	parser.add_argument('start', metavar='INDEX_START', type=int, nargs='?', default=1, help='the id at which juustagram images should be started to get downloaded\nan index from sharecfg/activity_ins_template')
	args = parser.parse_args()
	
	client = Client[args.client]
	download_all_images(client, args.start)

if __name__ == "__main__":
	main()