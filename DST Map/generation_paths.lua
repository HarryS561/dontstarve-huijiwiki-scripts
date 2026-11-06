-- 常规森林/洞穴生成路径的候选关系；不执行随机数量或区域内容函数。
-- 对照 762172: map/maptags.lua、startlocations.lua、level.lua、forest_map.lua。
local M = {}

local function insert_unique(index, key, value)
    index[key] = index[key] or {}
    for _, old in ipairs(index[key]) do
        if old == value then return end
    end
    table.insert(index[key], value)
end
M.InsertUnique = insert_unique

local function tagged(room, tag)
    for _, value in ipairs(room.tags or {}) do
        if value == tag then return true end
    end
    return false
end

local function tag_rule(values, setting)
    return {
        layouts = values,
        selection = #values == 1 and "one" or "one_random",
        disabled_when = setting and {setting=setting, value="never"} or nil,
        skip_when_tagdata_false = true,
        sets_tagdata_false = true,
    }
end

function M.Register(data, needed)
    data.layout_to_task = {}
    data.layout_to_taskset = {}
    data.layout_to_level = {}
    -- network.lua 将占位成对替换；locations.lua 决定森林/洞穴的实体。
    data.layout_prefab_proxies = {
        WormholeGrass={wormhole_MARKER="wormhole"},
        TentaclePillar={wormhole_MARKER="tentacle_pillar"},
    }
    for setname, set in pairs(data.tasksets) do
        local available = {}
        for _, task in ipairs(set.tasks) do available[task] = true end
        for _, task in ipairs(set.optionaltasks) do available[task] = true end
        for layout, choice in pairs(set.set_pieces or {}) do
            needed[layout] = true
            insert_unique(data.layout_to_taskset, layout, setname)
            for _, task in ipairs(choice.tasks or {}) do
                if available[task] then insert_unique(data.layout_to_task, layout, task) end
            end
        end
        for layout in pairs(set.ocean_prefill_setpieces or {}) do
            insert_unique(data.layout_to_taskset, layout, setname)
        end
    end

    data.levels = require("levels")
    for levelname, level in pairs(data.levels) do
        local setname = (level.overrides or {}).task_set or (level.location == "cave" and "cave_default" or "default")
        local set = assert(data.tasksets[setname], "缺少预设任务集:" .. setname)
        for _, field in ipairs({"required_setpieces", "random_set_pieces"}) do
            for _, layout in ipairs(level[field] or {}) do
                needed[layout] = true
                insert_unique(data.layout_to_level, layout, levelname)
                insert_unique(data.layout_to_taskset, layout, setname)
                for _, taskfield in ipairs({"tasks", "optionaltasks"}) do
                    for _, taskname in ipairs(set[taskfield]) do
                        if not data.tasks[taskname].level_set_piece_blocker then
                            insert_unique(data.layout_to_task, layout, taskname)
                        end
                    end
                end
            end
        end
    end

    data.tag_layouts = {
        StagehandGarden = tag_rule({"StagehandGarden"}),
        Terrarium_Spawner = tag_rule({"Terrarium_Forest_Spiders", "Terrarium_Forest_Pigs", "Terrarium_Forest_Fire"}, "terrariumchest"),
        CharlieStage_Spawner = tag_rule({"Charlie1"}, "stageplays"),
        StatueHarp_HedgeSpawner = tag_rule({"Charlie2"}, "stageplays"),
        Junkyard_Spawner = tag_rule({"junk_yard"}, "junkyard"),
        Balatro_Spawner = tag_rule({"Balatro"}, "balatro"),
        BatBossCave_Spawner = tag_rule({"bat_boss_cave1", "bat_boss_cave2", "bat_boss_cave3"}, "batbosscave"),
    }
    data.tag_prefabs = {}
    for tag, prefab in pairs({Chester_Eyebone="chester_eyebone", Hutch_Fishbowl="hutch_fishbowl", Astral_1="moon_altar_astral_marker_1", Astral_2="moon_altar_astral_marker_2"}) do
        data.tag_prefabs[tag] = {
            prefabs={prefab}, selection="one", skip_when_tagdata_false=true, sets_tagdata_false=true,
        }
    end
    -- forest_map.lua: 迷宫死路生成的宝箱，数量由实际迷宫决定。
    data.tag_prefabs.Labyrinth = {
        prefabs={"pandoraschest"}, selection="maze_dead_ends", count="#function", source="map/forest_map.lua",
    }
    for roomname, room in pairs(data.rooms) do
        for _, tag in ipairs(room.tags or {}) do
            local rule = data.tag_layouts[tag]
            if rule then
                for _, layout in ipairs(rule.layouts) do
                    needed[layout] = true
                    insert_unique(data.layout_to_room, layout, roomname)
                end
            end
            local item_rule = data.tag_prefabs[tag]
            if item_rule then
                for _, prefab in ipairs(item_rule.prefabs) do
                    insert_unique(data.prefab_to_room, prefab, roomname)
                end
            end
        end
    end

    -- startlocations.lua 的常规森林/洞穴入口；不包含独立活动世界。
    data.startlocations = {
        default={location="forest", start_setpeice="DefaultStart", start_node="Clearing"},
        plus={location="forest", start_setpeice="DefaultPlusStart", start_node={"DeepForest", "Forest", "SpiderForest", "Plain", "Rocky", "Marsh"}},
        darkness={location="forest", start_setpeice="DarknessStart", start_node={"DeepForest", "Forest"}},
        caves={location="cave", start_setpeice="CaveStart", start_node={"RabbitArea", "RabbitTown", "RabbitSinkhole", "SpiderIncursion", "SinkholeForest", "SinkholeCopses", "SinkholeOasis", "GrasslandSinkhole", "GreenMushSinkhole", "GreenMushRabbits"}},
    }
    for _, start in pairs(data.startlocations) do
        needed[start.start_setpeice] = true
        for setname, set in pairs(data.tasksets) do
            if set.location == start.location then
                insert_unique(data.layout_to_taskset, start.start_setpeice, setname)
                for _, task in ipairs(set.valid_start_tasks or {}) do
                    if data.tasks[task] then insert_unique(data.layout_to_task, start.start_setpeice, task) end
                end
            end
        end
    end
end

function M.AddMazeLayouts(data, layouts, needed)
    local all = require("map/maze_layouts").AllLayouts
    data.maze_layouts = {}
    local function add_group(group, taskname, task)
        local variants = assert(all[group], "缺少迷宫布局组:" .. group)
        data.maze_layouts[group] = data.maze_layouts[group] or {}
        for orientation, layout in pairs(variants) do
            local id = "maze/" .. layout.layout_file:gsub("^map/static_layouts/rooms/", "")
            data.maze_layouts[group][orientation] = {layout=id, force_rotation=layout.force_rotation}
            if not layouts[id] then
                layouts[id] = deepcopy(layout)
                layouts[id].force_rotation = nil -- 方向由上面的出口形状映射保留。
            end
            needed[id] = true
            insert_unique(data.layout_to_task, id, taskname)
            for roomname in pairs(task.room_choices or {}) do
                if data.rooms[roomname] and tagged(data.rooms[roomname], "Maze") then
                    insert_unique(data.layout_to_room, id, roomname)
                end
            end
        end
    end
    local function visit(value, taskname, task)
        if type(value) == "table" then
            for key, item in pairs(value) do
                if type(key) == "number" and type(item) == "string" then
                    add_group(item, taskname, task)
                elseif type(item) == "table" then
                    visit(item, taskname, task)
                end
            end
        end
    end
    for name, task in pairs(data.tasks) do visit(task.maze_tiles, name, task) end
end

-- 仅列出函数可能返回的实体；数量、概率和初始化属性仍由原 areas 函数占位保留。
local area_candidates = {
    saltstack_area={"saltstack"}, kelp_area={"bullkelp_plant"}, seastack_area={"seastack"}, stack_area={"seastack"},
    tree_area={"moon_tree"}, cave_hole_area={"cave_hole"}, randomtree={"evergreen", "deciduoustree"},
    grass_area={"grass", "evergreen_stump"}, balatro_card_area={"playing_card"},
    treearea={"oceantree", "oceanvine", "oceanvine_deco", "watertree_root", "oceanvine_cocoon", "fireflies"},
    monkeyisland_prefabs={"bananabush", "monkeytail", "palmconetree_short", "palmconetree_normal", "palmconetree_tall", "pirate_flag_pole", "lightcrab"},
    monkeyhut_area={"monkeyhut"}, monkeyisland_docksafearea={"monkeyisland_dockgen_safeareacenter"},
    rubble={}, debris={"rocks"}, creature_area={"archive_centipede_husk"}, archive_sound_area={"archive_ambient_sfx"},
    archive_cookpot_area={"archive_cookpot"}, mothden_area_low={"dustmothden"}, mothden_area_high={"dustmothden"},
    innertrees={"evergreen"}, outertrees={"evergreen", "sapling"}, grassarea={"grass"},
    plants={"cave_fern", "lichen", "flower_cave", "flower_cave_double", "flower_cave_triple"},
    relics={"ruins_plate", "ruins_bowl", "ruins_chair", "ruins_chipbowl", "ruins_vase", "ruins_table", "ruins_rubble_table", "ruins_rubble_chair", "ruins_rubble_vase", "thulecite_pieces", "rocks"},
    pumpkincarver={"pumpkincarver1", "pumpkincarver2", "pumpkincarver3"}, -- NUM_HALLOWEEN_PUMPKINCARVERS = 3
}
local specific_candidates = {
    AbandonedBoat1={item_area1={"spoiled_fish_small", "spoiled_fish"}, item_area2={"twigs", "cutgrass"}},
    AbandonedBoat2={item_area1={"oar", "oar_driftwood"}, item_area2={"twigs", "cutgrass"}, fishing_item_area={"oceanfishinglure_hermit_snow", "oceanfishinglure_hermit_heavy"}},
    OceanWhirlBigPortal={mast_area={"boards", "twigs", "cutgrass"}},
    Sculptures_2={sculpture_random={"statue_marble_muse", "statue_marble_pawn", "sculpture_knight", "sculpture_bishop"}},
    Sculptures_5={sculpture_random={"statue_marble", "marblepillar", "sculpture_knight", "sculpture_bishop"}},
}

function M.AreaPrefabs(name, layout)
    local result = {}
    for area, definition in pairs(layout.areas or {}) do
        -- 没有该区域标记的定义不会在这个布局生成任何东西。
        if layout.layout and layout.layout[area] then
            local candidates
            if type(definition) == "table" then
                candidates = {}
                for _, item in ipairs(definition) do
                    local prefab = type(item) == "table" and item.prefab or item
                    if type(prefab) == "string" then table.insert(candidates, prefab) end
                end
            else
                candidates = (specific_candidates[name] or {})[area] or area_candidates[area]
            end
            if candidates then
                result[area] = {prefabs=candidates, count=type(definition) == "table" and #definition or "#function", count_scope="per_area"}
            end
        end
    end
    return result
end

function M.FinishRelations(data)
    for layout, rooms in pairs(data.layout_to_room) do
        for _, room in ipairs(rooms) do
            for _, task in ipairs(data.room_to_task[room] or {}) do
                insert_unique(data.layout_to_task, layout, task)
            end
        end
    end
end

return M
