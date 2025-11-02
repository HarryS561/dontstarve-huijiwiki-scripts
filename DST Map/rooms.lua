require ("map/room_functions")
--local Layouts=require('map/layouts').Layouts
--local MazeLayouts=require('map/maze_layouts').Layouts

local rooms = {}
local modrooms = {}
local prefab_to_room={}
local layout_to_room={}

local function GetRoomByName(name)
    for mod,roomset in pairs(modrooms) do
        if roomset[name] ~= nil then
            return roomset[name]
        end
    end

    return rooms[name]
end

local function PrefabToRoom(p,r)
    CreateInsert(prefab_to_room,p,r)
end

local function LayoutToRoom(l,r)
    LAYOUT_NEEDED[l]=true
    if not layout_to_room[l] then
        layout_to_room[l]={r}
    else
        table.insert(layout_to_room[l],r)
    end
end

function AddRoom(name, data)
    if not ROOM_NEEDED[name] then
        --print('不需要'..name)
        return
    end

    assert(GetRoomByName(name) == nil, "Adding a room '"..name.."' failed, it already exists!")
    rooms[name] = data

    local contents=data.contents
    if not contents then
        --print(name)
        return
    end

    local countprefabs=contents.countprefabs
    if countprefabs then
        for k,v in pairs(countprefabs) do
            PrefabToRoom(k,name)
            if type(v)=='function' then
                countprefabs[k]='#function'
            end
        end
    end

    local countstaticlayouts=contents.countstaticlayouts
    if countstaticlayouts then
        for k,v in pairs(countstaticlayouts) do
            LayoutToRoom(k,name)
            if type(v)=='function' then
                countstaticlayouts[k]='#function'
            end
        end
    end

    if not contents.distributeprefabs then
        --print(name)
        return
    end
    for k,v in pairs(contents.distributeprefabs) do
        if type(v)=='table' then
            for _,p in ipairs(v.prefabs) do
                PrefabToRoom(p,name)
            end
        else
            PrefabToRoom(k,name)
        end
    end
end

--以下至return前直接复制
-- "Special" rooms
require("map/rooms/test")

require("map/rooms/forest/pigs")
require("map/rooms/forest/merms")
require("map/rooms/forest/chess")
require("map/rooms/forest/spider")
require("map/rooms/forest/walrus")
require("map/rooms/forest/wormhole")
require("map/rooms/forest/beefalo")
require("map/rooms/forest/graveyard")
require("map/rooms/forest/tallbird")
require("map/rooms/forest/bee")
require("map/rooms/forest/mandrake")
require("map/rooms/forest/giants")

require("map/rooms/cave/bats")
require("map/rooms/cave/bluemush")
require("map/rooms/cave/fungusnoise")
require("map/rooms/cave/generic")
require("map/rooms/cave/greenmush")
require("map/rooms/cave/mud")
require("map/rooms/cave/rabbits")
require("map/rooms/cave/redmush")
require("map/rooms/cave/rocky")
require("map/rooms/cave/sinkhole")
require("map/rooms/cave/spillagmites")
require("map/rooms/cave/swamp")
require("map/rooms/cave/toadstoolarena")
require("map/rooms/cave/vents")

require("map/rooms/cave/ruins")

-- ... adventure?
require("map/rooms/forest/blockers")
require("map/rooms/forest/starts")

-- "Background" rooms

require("map/rooms/forest/terrain_dirt")
require("map/rooms/forest/terrain_forest")
require("map/rooms/forest/terrain_grass")
require("map/rooms/forest/terrain_impassable")
require("map/rooms/forest/terrain_marsh")
require("map/rooms/forest/terrain_noise")
require("map/rooms/forest/terrain_rocky")
require("map/rooms/forest/terrain_savanna")
require("map/rooms/forest/terrain_moonisland")
require("map/rooms/forest/terrain_ocean")

require("map/rooms/cave/terrain_mazes")

require("map/rooms/forest/DLCrooms")

------------------------------------------------------------------------------------
-- EXIT ROOM -----------------------------------------------------------------------
------------------------------------------------------------------------------------
AddRoom("Exit", {
					colour={r=0.3,g=0.2,b=0.1,a=0.3},
					value = WORLD_TILES.FOREST,
					contents =  {
					                countprefabs= {
					                	teleportato_base = 1,
					                    spiderden = function () return 5 + math.random(3) end,
					                    gravestone = function () return 4 + math.random(4) end,
					                    mound = function () return 4 + math.random(4) end
					                }
					            }
					})


------------------------------------------------------------------------------------
-- BLANK ROOM ----------------------------------------------------------------------
------------------------------------------------------------------------------------
AddRoom("Blank", {
					colour={r=1.0,g=1.0,b=1.0,a=0.1},
					value = WORLD_TILES.IMPASSABLE,
                    type = NODE_TYPE.Blank,
					contents =  {
					            }
					})


return {rooms, prefab_to_room, layout_to_room}
