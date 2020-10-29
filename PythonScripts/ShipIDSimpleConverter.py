import Utility

JsonAPI = Utility.defaultJsonAPI()
ShipConverter = JsonAPI.converter

groupid = int(input("Input GroupID: "))
print(ShipConverter.get_shipname(groupid))
input("Press Enter to Exit...")