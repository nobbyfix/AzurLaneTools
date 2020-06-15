from argparse import ArgumentParser
from AzurLane import Award, Client
import WikiHelper, Utility

JsonAPI = Utility.defaultJsonAPI()

def login_rewards(client, loginid):
	activity_7_day_sign = JsonAPI.load_sharecfg('activity_7_day_sign', client)
	signin_data = activity_7_day_sign.get(str(loginid))
	if not signin_data: raise ValueError(f'{client.name} has no loginid {loginid}.')
	for award_d in signin_data["front_drops"]:
		yield JsonAPI.load_award(award_d[0], award_d[1], award_d[2])

def seven_day_signin(client, loginid):
	award_displays = [WikiHelper.award_to_display(award) for award in login_rewards(client, loginid)]
	return '\n'.join(award_displays)

def main():
	parser = ArgumentParser()
	parser.add_argument('loginid', metavar='INDEX', type=int, nargs=1, help='an index from sharecfg/activity_7_day_sign')
	parser.add_argument('-c', '--client', required=True, help='client to gather information from')
	parser.add_argument('-f', '--file', metavar='FILENAME', default='7day_signin', type=str, help='file to save to, default is "7day_signin"')
	args = parser.parse_args()
	
	client = Client[args.client]
	result = seven_day_signin(client, args.loginid[0])
	Utility.output(args.file, result)

if __name__ == "__main__":
	main()