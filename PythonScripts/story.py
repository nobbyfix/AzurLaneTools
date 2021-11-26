import re
import json
from pathlib import Path
from typing import Union

from lib import Client, ALJsonAPI, WikiHelper, Utility, DEFAULT_CLIENTS


api = ALJsonAPI()
memory_group = api.get_sharecfgmodule("memory_group")
memory_template = api.get_sharecfgmodule("memory_template")
ship_skin_template = api.get_sharecfgmodule("ship_skin_template")
STORY_TEMPLATE = WikiHelper.MultilineTemplate('Story')

with open(Path('data', 'ship_painting_convert.json'), 'r', encoding='utf8') as f:
	SHIP_PAINTING_NAMES = json.load(f)


HTML_TAG = re.compile(r"<[^>]*>")
def sanitize(v:str) -> str:
	return HTML_TAG.sub("", v).strip()

def actor(atype, name, skincat, nameoverride, skinname):
	res = f"{atype}:{name}/{skincat}:{nameoverride}:{skinname}"
	return res.strip(":").strip("/").strip(":")

non_commander_tags = [
	"flashin",
	"flashN",
]
def is_commander(story_segment):
	return story_segment.keys().isdisjoint(non_commander_tags)

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
			#else:
			#	if is_commander(story_segment):
			#		actorstr = "O:Commander"

			optionstr = ''
			if 'optionFlag' in story_segment:
				optionstr = f"'''If Option {story_segment['optionFlag']}:''' "

			lines_result.append(f"[{actorstr}] {optionstr}"+sanitize(story_segment['say']))
		if 'sequence' in story_segment:
			sequence_sanitized = [sanitize(line[0]) for line in story_segment['sequence']]
			sequence_text = "<br>".join(sequence_sanitized)
			lines_result.append("[] "+sequence_text)

		if 'options' in story_segment:
			option_sanitized = [f"'''Option {line['flag']}:''' "+sanitize(line['content']) for line in story_segment['options']]
			option_text = "<br>".join(option_sanitized)
			lines_result.append("[O:Commander] "+option_text)

	return lines_result

def memory(memoryid: Union[int, str], client: Client):
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

def memories(memory_groupid: Union[int, str], client: Client):
	memory_groupdata = memory_group.load_client(memory_groupid, client)
	memory_collection = [f'Chapter {i}=\n'+memory(memoryid, client) for i, memoryid in enumerate(memory_groupdata['memories'], 1)]
	return "<tabber>\n"+"\n|-|\n".join(memory_collection)+"\n</tabber>"


tabber_name = {
	Client.EN: "English",
	Client.CN: "Chinese",
	Client.JP: "Japanese",
}

if __name__ == "__main__":
	MEMORY_ID = 203
	TITLE = "The Flame-Touched Dagger"

	clients_result = []
	for client in DEFAULT_CLIENTS:
		clients_result.append(tabber_name[client]+" Story=\n"+memories(MEMORY_ID, client))
	
	wikitext = [
		"{{#tag:tabber|",
		"\n{{!}}-{{!}}\n".join(clients_result),
		"}}",
		"{{StoryList}}",
		f"[[Category:Memories|{TITLE}]]",
		f"[[Category:Major Event Memories|{TITLE}]]",
	]

	Utility.output("\n".join(wikitext))