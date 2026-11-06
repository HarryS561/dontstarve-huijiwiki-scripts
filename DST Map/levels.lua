-- 仅收集当前 PC 森林/洞穴的世界生成预设；界面文本、游玩设置与活动世界不导出。
local data = {}
local function strings_table()
    return setmetatable({}, {__index=function(t, key)
        local value = strings_table()
        rawset(t, key, value)
        return value
    end})
end
local function ignore() end
local env = {
    STRINGS=strings_table(), LEVELTYPE={SURVIVAL="SURVIVAL"},
    IsConsole=function() return false end,
    AddLevel=ignore, AddSettingsPreset=ignore, AddPlaystyleDef=ignore,
    AddWorldGenLevel=function(_, definition)
        if definition.hideinfrontend then return end
        local result = {}
        for _, key in ipairs({"id", "location", "overrides", "required_setpieces", "numrandom_set_pieces", "random_set_pieces", "background_node_range"}) do
            result[key] = definition[key]
        end
        data[definition.id] = result
    end,
}
setmetatable(env, {__index=_G})
for _, filename in ipairs({"map/levels/forest.lua", "map/levels/caves.lua"}) do
    local chunk = assert(loadfile(filename))
    setfenv(chunk, env)
    chunk()
end
return data
