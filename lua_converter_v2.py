import re
from pathlib import Path
import multiprocessing as mp
from argparse import ArgumentParser
from git import Repo

from lua_convert import Client, convert_lua


ALLOWED_GAMECFG_FOLDERS = {"buff", "dungeon", "skill", "story", "storyjp", "backyardtheme", "guide"}

LUA_REPO_NAME = "Src"
JSON_REPO_NAME = "SrcJson"
REGEX = re.compile(r"\[(..-..)\] AZ: (\d+\.\d+\.\d+)")


class SrcRepo(Repo):
	def pull(self):
		"""
		Pulls from origin and returns old commit

		:return: the old commit before pulling
		"""
		print("Pulling new changes from origin...")
		pullinfo = self.remotes.origin.pull()[0]
		oldcommit = pullinfo.old_commit
		if oldcommit is None: print("No new commits available.")
		else: print("New commits have been pulled.")
		return pullinfo.old_commit

	def pull_and_get_changes(self, override_old_commit=None):
		old_commit = self.pull()

		if override_old_commit is not None: old_commit = self.commit(override_old_commit)
		if old_commit is None: return

		commits = []
		for commit in self.iter_commits():
			if commit.hexsha == old_commit.hexsha:
				break
			commits.append(commit)

		for commit in reversed(commits):
			changes = self.changes_from_commit(commit)
			if changes: yield changes

	def changes_from_commit(self, commit):
		"""
		:return: the tuple (client, version, files)
		where client is a string, version is a string and files a list

		or None, if the commit is not a valid commit
		"""
		re_result = REGEX.findall(commit.message)
		if re_result:
			diff_index = commit.parents[0].diff(commit)
			files = [diff.b_path for diff in diff_index if diff.change_type in ["A", "M"]]
			return *re_result[0], files


def is_allowed_gamecfg(path: Path):
	return bool(ALLOWED_GAMECFG_FOLDERS.intersection(path.parts))

def normalize_gamecfg_paths(path: Path):
	if "storyjp" in path.parts:
		return Path(str(path).replace("storyjp", "story"))
	return path


def convert_new_files(override_commit: str = None):
	repo = SrcRepo(LUA_REPO_NAME)
	repo_json = SrcRepo(JSON_REPO_NAME)

	for client, version, files in repo.pull_and_get_changes(override_commit):
		client = Client.from_locale(client)

		with mp.Pool(processes=mp.cpu_count()) as pool:
			for filepath in files:
				filepath = Path(filepath)
				index = 1
				if "gamecfg" in filepath.parts:
					if not is_allowed_gamecfg(filepath):
						continue
					index += 1
				elif "sharecfg" not in filepath.parts:
					continue
				# else is sharecfg file
				path2 = filepath.relative_to(*filepath.parts[:index])

				lua_require = Path(LUA_REPO_NAME, filepath)
				json_destination = normalize_gamecfg_paths( Path(JSON_REPO_NAME, client.name, path2.with_suffix(".json")) )
				pool.apply_async(convert_lua, (lua_require, json_destination,))

			# explicitly join the pool
			# since the pool only receives async tasks, this waits for their completion
			pool.close()
			pool.join()

		repo_json.git.add(client.name) # adds only all files inside the current clients directory
		repo_json.git.commit("-m", f"{client.name} {version}", "--allow-empty")
	repo_json.remotes.origin.push()


def main():
	parser = ArgumentParser()
	parser.add_argument("-c", "--commit-sha", type=str, help="commit sha from which to start converting")
	args = parser.parse_args()

	if sha := args.commit_sha:
		convert_new_files(sha)
	else:
		convert_new_files()

if __name__ == "__main__":
	main()
