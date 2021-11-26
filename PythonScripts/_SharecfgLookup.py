from lib import Client, ALJsonAPI


if __name__ == "__main__":
	api = ALJsonAPI()

	while True:
		module = None
		modulename = input("Module: ")

		try:
			module = api.get_sharecfgmodule(modulename)
		except: pass
		if not module:
			try:
				module = api.get_apimodule(modulename)
			except: pass

		if module: break
		else: print("FAILED: Module does not exist.")

	while True:
		dataid = input("ID: ")
		client = input("Client: ")

		try:
			if client:
				client = Client[client]
				print(module.load_client(dataid, client)._json)
			else:
				print(module.load_first(dataid, Client)._json)
		except:
			print("FAILED: Maybe the module does not have this id?")