import re
import json
from pathlib import Path
from argparse import ArgumentParser

from lib import Client, ALJsonAPI, WikiHelper, Utility, DEFAULT_CLIENTS


api = ALJsonAPI()
memory_group = api.get_sharecfgmodule("memory_group")
memory_template = api.get_sharecfgmodule("memory_template")
ship_skin_template = api.get_sharecfgmodule("ship_skin_template")
STORY_TEMPLATE = WikiHelper.MultilineTemplate('Story')

with open(Path('data', 'ship_painting_convert.json'), 'r', encoding='utf8') as f:
	SHIP_PAINTING_NAMES = json.load(f)

tabber_name = {
	Client.EN: "English",
	Client.CN: "Chinese",
	Client.JP: "Japanese",
}


HTML_TAG = re.compile(r"<[^>]*>")
def sanitize(v: str) -> str:
	return HTML_TAG.sub("", v).strip()

def sanitize_w_namecode(v: str, client: Client) -> str:
	return api.replace_namecode(sanitize(v), client)

def actor(atype, name, skincat, nameoverride, skinname):
	res = f"{atype}:{name}/{skincat}:{nameoverride}"
	return res.strip(":").strip("/").strip(":")

def story(storyname: str, client: Client):
	lines_result = []

	storydata = api.loader.load_story(storyname.lower(), client)
	for story_segment in storydata['scripts']:
		if 'say' in story_segment:
			actorstr = ''
			if 'actor' in story_segment:
				actorid = story_segment['actor']
				if actorid > 0:
					actor_skindata = ship_skin_template.load_client(actorid, client)
					actor_painting = actor_skindata['painting']
					skinname = actor_skindata['name'].strip().replace('μ', 'µ')
					if actor_painting in SHIP_PAINTING_NAMES:
						pcn = SHIP_PAINTING_NAMES[actor_painting]
						shipname = pcn['shipname']
						category = pcn['category']
						if shipname == skinname: skinname = ""
						actorstr = actor("S", shipname, category, "", skinname)
					else:
						actorstr = "O:"+actor_skindata['name'].strip()
				else: raise NotImplementedError('Unsupported ActorID')

			optionstr = ''
			if 'optionFlag' in story_segment:
				optionstr = f"'''If Option {story_segment['optionFlag']}:''' "

			lines_result.append(f"[{actorstr}] {optionstr}"+sanitize_w_namecode(story_segment['say'], client))
		if 'sequence' in story_segment:
			sequence_sanitized = [sanitize_w_namecode(line[0], client) for line in story_segment['sequence']]
			sequence_text = "<br>".join(sequence_sanitized)
			lines_result.append("[] "+sequence_text)

		if 'options' in story_segment:
			option_sanitized = [f"'''Option {line['flag']}:''' "+sanitize_w_namecode(line['content'], client) for line in story_segment['options']]
			option_text = "<br>".join(option_sanitized)
			lines_result.append("[O:Commander] "+option_text)

	return lines_result

def memory(memoryid: int | str, client: Client):
	memory_data = memory_template.load_client(memoryid, client)
	story_lines = story(memory_data['story'], client)

	template_params = {
		"Title": memory_data['title'],
		"Unlock": memory_data['condition'],
		"Language": client.name,
	}
	story_lines = "\n | ".join(story_lines)
	template_params['Language'] += "\n | "+story_lines
	return STORY_TEMPLATE.fill(template_params)

def memorygroup(memorygroup_id: int | str, client: Client):
	memorygroup_data = memory_group.load_client(memorygroup_id, client)
	memory_collection = [f'Chapter {i}=\n'+memory(memoryid, client) for i, memoryid in enumerate(memorygroup_data['memories'], 1)]
	return tabber_name[client] + " Story=\n<tabber>\n" + "\n|-|\n".join(memory_collection) + "\n</tabber>"


def main():
	parser = ArgumentParser()
	parser.add_argument('memoryid', metavar='INDEX', type=int,
						help='an index from sharecfg/memory_template')
	args = parser.parse_args()

	TITLE = "Tower of Transcendence"
	clients_result = [memorygroup(args.memoryid, client) for client in DEFAULT_CLIENTS]

	wikitext = [
		"{{#tag:tabber|",
		"\n{{!}}-{{!}}\n".join(clients_result),
		"}}",
		"{{StoryList}}",
		f"[[Category:Memories|{TITLE}]]",
		f"[[Category:Major Event Memories|{TITLE}]]",
	]
	Utility.output("\n".join(wikitext))

if __name__ == "__main__":
	main()
