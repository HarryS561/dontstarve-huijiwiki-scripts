--程序入口
--require '.debug'
require 'constants'
require 'tiledefs' --Turfs

function deepcopy(t)
    if type(t)~='table' then
        return t
    end
    local copy={}
    for k,v in pairs(t) do
        copy[k]=deepcopy(v)
    end
    return copy
end
function string:split(sep)
    local sep, fields = sep or ":", {}
    local pattern = string.format("([^%s]+)", sep)
    self:gsub(pattern, function(c) fields[#fields+1] = c end)
    return fields
end
function ExtendedArray(orig, addition, mult)
	local ret = {}
	for k,v in pairs(orig) do
		ret[k] = v
	end
	mult = mult or 1
	for i=1,mult do
		table.insert(ret,addition)
	end
	return ret
end
function CreateInsert(dict, key, ...) --允许插入多个值
    if dict[key] == nil then
        dict[key] = {}
    end
    for _, v in ipairs{...} do
        table.insert(dict[key], v)
    end
end

DATA={}
DATA.turfs=Turfs

DATA.proxies={ --数量不多，暂且手填吧
    perma_grass = 'grass',
    perma_sapling = 'sapling',
    ground_twigs = 'twigs',
    lunar_island_rock1 = 'rock1',
    lunar_island_rock2 = 'rock2',
    lunar_island_rocks = 'rocks',
}

local TaskSet=require 'tasksets'
DATA.tasksets=TaskSet
TASK_NEEDED={}
ROOM_NEEDED={}
LAYOUT_NEEDED={}
for _,set in pairs(TaskSet) do
    for _,name in ipairs(set.tasks) do
        TASK_NEEDED[name]=true
    end
    for _,name in ipairs(set.optionaltasks) do
        TASK_NEEDED[name]=true
    end
    for _,name in ipairs(set.ocean_population or {}) do
        ROOM_NEEDED[name]=true
    end
    for name,v in pairs(set.ocean_prefill_setpieces or {}) do
        assert(type(v.count)=='number', '海洋布景数量非数值')
        LAYOUT_NEEDED[name]=v.count
    end
end

local taskdata=require 'tasks'
DATA.tasks=taskdata[1]
DATA.room_to_task=taskdata[2]

local roomdata=require 'rooms'
DATA.rooms=roomdata[1]
DATA.prefab_to_room=roomdata[2]
DATA.layout_to_room=roomdata[3]

for name in pairs(TASK_NEEDED) do
    if not DATA.tasks[name] then
        print('缺少生物群系:'..name)
    end
end
for name in pairs(ROOM_NEEDED) do
    if not DATA.rooms[name] then
        print('缺少区块:'..name)
    end
end

DATA.layouts={}
DATA.prefab_to_layout={}
--非固定布景过于复杂，以后再说
local Layouts=require('map/layouts').Layouts

for name in pairs(LAYOUT_NEEDED) do
    local lo=Layouts[name]
    assert(lo, '缺少布景:'..name)
    DATA.layouts[name]=lo
    local defs=lo.defs or {}
    for prefab in pairs(lo.layout or lo.count) do
        prefab = DATA.proxies[prefab] or defs[prefab] or prefab
        if type(prefab)=='table' then
            for _, p in ipairs(prefab) do
                CreateInsert(DATA.prefab_to_layout, p, name)
            end
        else
            CreateInsert(DATA.prefab_to_layout, prefab, name)
        end
    end
end

-- require 'json'
-- io.open('output.json','w'):write(json.encode(DATA))

local function serialize(tbl, indent)
    indent = indent or ""
    local nextIndent = indent .. "    "
    if type(tbl) ~= "table" then
        error("Expected a table, got " .. type(tbl))
    end
    local lines = {"{"}
    for k, v in pairs(tbl) do
        local keyStr
        if (type(k) == "string" and k:match("^%a[%w_]*$")) then
            keyStr = k
        elseif type(k) == "number" then
            keyStr = "[" .. tostring(k) .. "]"
        else
            keyStr = "[\"" .. tostring(k) .. "\"]"
        end

        local valueStr
        if type(v) == "table" then
            valueStr = serialize(v, nextIndent)
        elseif type(v) == "string" then
            valueStr = string.format("%q", v)
        elseif type(v) == "function" then
            valueStr = "\"#function\""
        else
            valueStr = tostring(v)
        end

        table.insert(lines, string.format("%s%s = %s,", nextIndent, keyStr, valueStr))
    end
    table.insert(lines, indent .. "}")
    return table.concat(lines, "\n")
end

-- 保存 table 到文件
local function save_table_to_file(tbl, filename, varname)
    local file = assert(io.open(filename, "w"))
    varname = varname or "data"
    file:write(varname .. " = ")
    file:write(serialize(tbl))
    file:close()
end

save_table_to_file(DATA, "./output.lua", "DATA")
