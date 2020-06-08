package.path = package.path .. ";?.lua"
local cjson = require("cjson")
cjson.encode_sparse_array(true)

function Vector3(a, b, c)
    return {a, b, c}
end

ltable = require(arg[1])
print(cjson.encode(ltable))