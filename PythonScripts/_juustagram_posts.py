from argparse import ArgumentParser
from AzurLane import Client
import WikiHelper, Utility

JsonAPI = Utility.defaultJsonAPI()
template_juu = WikiHelper.MultilineTemplate('Juustagram')

def get_message(client, gameset_key:str) -> str:
	"""
	returns empty string if gameset_key not available
	"""
	gameset_language_client = JsonAPI.load_sharecfg('gameset_language_client', client)
	if gameset_key not in gameset_language_client: return ''
	return JsonAPI.replace_namecode(gameset_language_client[gameset_key]['value'].strip(), client)

def get_comment(client, ins_comment_id:int, recursion=1):
	activity_ins_npc_template = JsonAPI.load_sharecfg('activity_ins_npc_template', client)
	if not ins_comment_id in activity_ins_npc_template['all']:
		raise ValueError(f'Client {client.name} has no juustagram comment with id {ins_comment_id}')
	
	comment_data = activity_ins_npc_template[str(ins_comment_id)]
	shipname = JsonAPI.converter.get_shipname(comment_data['ship_group'])
	msg = ('*'*recursion)+' ['+shipname+'] '

	gameset_id = comment_data['message_persist']
	if gameset_id == '' or (gameset_msg := get_message(client, gameset_id)) == '':
		print(f'For Client {client.name}, juustagram comment {ins_comment_id} has no message.')
	else:
		msg += gameset_msg
	comments = [msg]
	
	for ins_comment_id in comment_data['npc_reply_persist']:
		comments.extend(get_comment(client, ins_comment_id, recursion+1))
	return comments
	
def get_post(client, ins_template_id:int) -> str:
	activity_ins_template = JsonAPI.load_sharecfg('activity_ins_template', client)
	if not ins_template_id in activity_ins_template['all']:
		raise ValueError(f'Client {client.name} has no juustagram with id {ins_template_id}.')
	
	post_data = activity_ins_template[str(ins_template_id)]
	shipname = JsonAPI.converter.get_shipname(post_data['ship_group'])
	msg = '* ['+shipname+'] '

	gameset_id = post_data['message_persist']
	if gameset_id == '' or (gameset_msg := get_message(client, gameset_id)) == '':
		print(f'For Client {client.name}, juustagram post {ins_template_id} has no message.')
	else:
		msg += gameset_msg
	comments = ['', msg]

	for ins_comment_id in post_data['npc_discuss_persist']:
		comments.extend(get_comment(client, ins_comment_id))

	template_content = {'pict': str(ins_template_id), 'post': '\n'.join(comments)}
	wikitext = template_juu.fill(template_content)
	return wikitext

def main():
	parser = ArgumentParser()
	parser.add_argument('-c', '--client', required=True, help='client to gather information from')
	parser.add_argument('-s', '--start', required=True, type=int, help='output new posts from')
	parser.add_argument('-e', '--end', required=True, type=int, help='output new posts to')
	parser.add_argument('-f', '--file', metavar='FILENAME', type=str, default='juustagram', help='file to save to, default depends on the mode selected')
	args = parser.parse_args()
	
	client = Client[args.client]
	posts = [get_post(client, postid) for postid in range(args.start, args.end+1)]
	Utility.output(args.file, '\n\n'.join(posts))

if __name__ == "__main__":
	main()