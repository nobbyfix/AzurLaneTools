package.path = package.path .. ";?.lua"
local cjson = require("cjson")
cjson.encode_sparse_array(true)

require(arg[1])

print(cjson.encode(pg[arg[2]]))