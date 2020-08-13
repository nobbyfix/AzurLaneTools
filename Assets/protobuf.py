from proto import p10_pb2

CONFIGURED_COMMANDS = {
	10800: p10_pb2.Cs10800,
	10801: p10_pb2.Sc10801,
}

class BasicCommand():
	def __init__(self, command_id:int, index:int=0):
		if not command_id in CONFIGURED_COMMANDS:
			raise NotImplementedError(f'Command {command_id} is not registered.')
		self.command_id = command_id
		self.index = index
		self.pb = CONFIGURED_COMMANDS[command_id]()


ADV_HEADER_LEN = 7
HEADER_LEN = 2
HEADER_NOID_LEN = ADV_HEADER_LEN - HEADER_LEN

def serialize_pb(basic_pb_command):
	payload = bytearray(basic_pb_command.pb.SerializeToString())
	
	header_bytes = ((len(payload) or 1) + HEADER_NOID_LEN).to_bytes(2, byteorder='big')
	command_id_bytes = basic_pb_command.command_id.to_bytes(2, byteorder='big')
	index_bytes = basic_pb_command.index.to_bytes(2, byteorder='big')

	command_bytes = bytearray(ADV_HEADER_LEN)
	command_bytes[0] = header_bytes[0]
	command_bytes[1] = header_bytes[1]
	command_bytes[3] = command_id_bytes[0]
	command_bytes[4] = command_id_bytes[1]
	command_bytes[5] = index_bytes[0]
	command_bytes[6] = index_bytes[1]
	command_bytes.extend(payload)
	return command_bytes

def deserialize_pb(command_bytes):
	command_id = command_bytes[3] << 8 | command_bytes[4]
	basiccmd = BasicCommand(command_id)
	basiccmd.pb.ParseFromString(command_bytes[7:])
	return basiccmd