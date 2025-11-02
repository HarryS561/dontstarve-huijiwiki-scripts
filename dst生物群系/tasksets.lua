local datas={}

function AddTaskSet(id,data)
    datas[id]=data
end

STRINGS={UI={CUSTOMIZATIONSCREEN={TASKSETNAMES={CAVE_DEFAULT='地下', CLASSIC='经典', DEFAULT='联机版'}}}}

--map/tasksets/forest.lua
AddTaskSet("default", {
		name = STRINGS.UI.CUSTOMIZATIONSCREEN.TASKSETNAMES.DEFAULT,
        location = "forest",
		tasks = {
			"Make a pick",
			"Dig that rock",
			"Great Plains",
			"Squeltch",
			"Beeeees!",
			"Speak to the king",
			"Forest hunters",
			"Badlands",
			"For a nice walk",
			"Lightning Bluff",

			-- meteor island
			"MoonIsland_IslandShards",
			"MoonIsland_Beach",
			"MoonIsland_Forest",
			"MoonIsland_Baths",
			"MoonIsland_Mine",
		},
		numoptionaltasks = 5,
		optionaltasks = {
			"Befriend the pigs",
			"Kill the spiders",
			"Killer bees!",
			"Make a Beehat",
			"The hunters",
			"Magic meadow",
			"Frogs and bugs",
			"Mole Colony Deciduous",
			"Mole Colony Rocks",
			"MooseBreedingTask",
		},
        valid_start_tasks = {
            "Make a pick",
        },
		required_prefabs = {
			"gravestone",
			"sculpture_rook",
			"sculpture_bishop",
			"sculpture_knight",
			"terrariumchest",
			"charlie_stage_post",
			"statueharp_hedgespawner",
			"balatro_machine",
		},
		set_pieces = {
			["ResurrectionStone"] = { count = 2, tasks={"Make a pick", "Dig that rock", "Great Plains", "Squeltch", "Beeeees!", "Speak to the king", "Forest hunters", "Badlands" } },
			["WormholeGrass"] = { count = 8, tasks={"Make a pick", "Dig that rock", "Great Plains", "Squeltch", "Beeeees!", "Speak to the king", "Forest hunters", "Befriend the pigs", "For a nice walk", "Kill the spiders", "Killer bees!", "Make a Beehat", "The hunters", "Magic meadow", "Frogs and bugs", "Badlands"} },
			["MooseNest"] = { count = 9, tasks={"Make a pick", "Beeeees!", "Speak to the king", "Forest hunters", "Befriend the pigs", "For a nice walk", "Make a Beehat", "Magic meadow", "Frogs and bugs"} },
			["CaveEntrance"] = { count = 10, tasks={"Make a pick", "Dig that rock", "Great Plains", "Squeltch", "Beeeees!", "Speak to the king", "Forest hunters", "Befriend the pigs", "For a nice walk", "Kill the spiders", "Killer bees!", "Make a Beehat", "The hunters", "Magic meadow", "Frogs and bugs"} },
			["MoonAltarRockGlass"] = { count = 1, tasks={"MoonIsland_Mine"} },
			["MoonAltarRockIdol"] = { count = 1, tasks={"MoonIsland_Mine"} },
			["MoonAltarRockSeed"] = { count = 1, tasks={"MoonIsland_Mine"} },
            ["BathbombedHotspring"] = {count = 1, tasks={"MoonIsland_Baths"}},
            ["MoonFissures"] = {count = 1, tasks={"MoonIsland_Fissures","MoonIsland_Mine","MoonIsland_Forest"}},
		},
		ocean_prefill_setpieces = {
			["BrinePool1"] = {count = 4}, -- todo: make this scale based on world gen size
			["BrinePool2"] = {count = 2}, -- todo: make this scale based on world gen size
			["BrinePool3"] = {count = 2}, -- todo: make this scale based on world gen size
			["Waterlogged1"] = {count = 3}, -- todo: make this scale based on world gen size
		},

		ocean_population = {
            "OceanCoastalShore",
			"OceanCoastal",
			"OceanSwell",
			"OceanRough",
			"OceanHazardous",
		},
		-- ocean_population_setpieces =
		-- {
		-- },
	})

AddTaskSet("classic", {
		name = STRINGS.UI.CUSTOMIZATIONSCREEN.TASKSETNAMES.CLASSIC,
        location = "forest",
		tasks = {
			"Make a pick",
			"Dig that rock",
			"Great Plains",
			"Squeltch",
			"Beeeees!",
			"Speak to the king classic",
			"Forest hunters",
			"For a nice walk",
		},
		numoptionaltasks = 4,
		optionaltasks = {
			"Befriend the pigs",
			"Kill the spiders",
			"Killer bees!",
			"Make a Beehat",
			"The hunters",
			"Magic meadow",
			"Frogs and bugs",
		},
        valid_start_tasks = {
            "Make a pick",
			"sculpture_rook",
			"sculpture_bishop",
			"sculpture_knight",
        },
		required_prefabs = {
			"gravestone",
		},
		set_pieces = {
			["ResurrectionStone"] = { count=2, tasks={"Make a pick", "Dig that rock", "Great Plains", "Squeltch", "Beeeees!", "Speak to the king", "Forest hunters" } },
			["WormholeGrass"] = { count=8, tasks={"Make a pick", "Dig that rock", "Great Plains", "Squeltch", "Beeeees!", "Speak to the king", "Forest hunters", "Befriend the pigs", "For a nice walk", "Kill the spiders", "Killer bees!", "Make a Beehat", "The hunters", "Magic meadow", "Frogs and bugs" } },
			["CaveEntrance"] = { count = 10, tasks={"Make a pick", "Dig that rock", "Great Plains", "Squeltch", "Beeeees!", "Speak to the king classic", "Forest hunters", "Befriend the pigs", "For a nice walk", "Kill the spiders", "Killer bees!", "Make a Beehat", "The hunters", "Magic meadow", "Frogs and bugs"} },
		},
	})


--map/tasksets/caves.lua
AddTaskSet("cave_default", {
    name = STRINGS.UI.CUSTOMIZATIONSCREEN.TASKSETNAMES.CAVE_DEFAULT,
    location = "cave",
    tasks={
        "MudWorld",
        "MudCave",
        "MudLights",
        "MudPit",

        "BigBatCave",
        "RockyLand",
        "RedForest",
        "GreenForest",
        "BlueForest",
        "SpillagmiteCaverns",

        "MoonCaveForest",
        "ArchiveMaze",

        "CaveExitTask1",
        "CaveExitTask2",
        "CaveExitTask3",
        "CaveExitTask4",
        "CaveExitTask5",
        "CaveExitTask6",
        "CaveExitTask7",
        "CaveExitTask8",
        "CaveExitTask9",
        "CaveExitTask10",
		
        "CentipedeCaveTask",

		"ToadStoolTask1",
		"ToadStoolTask2",
		"ToadStoolTask3",

        -- ruins
        "LichenLand",
        "Residential",
        "Military",
        "Sacred",
        "TheLabyrinth",
        "SacredAltar",
        "AtriumMaze",
    },
    numoptionaltasks = 8,
    optionaltasks = {
        "SwampySinkhole",
        "CaveSwamp",
        "UndergroundForest",
        "PleasantSinkhole",
        "FungalNoiseForest",
        "FungalNoiseMeadow",
        "BatCloister",
        "RabbitTown",
        "RabbitCity",
        "SpiderLand",
        "RabbitSpiderWar",

        --ruins
        "MoreAltars",
        "CaveJungle",
        "SacredDanger",
        "MilitaryPits",
        "MuddySacred",
        "Residential2",
        "Residential3",
    },
    valid_start_tasks = {
        "CaveExitTask1",
        "CaveExitTask2",
        "CaveExitTask3",
        "CaveExitTask4",
        "CaveExitTask5",
        "CaveExitTask6",
        "CaveExitTask7",
        "CaveExitTask8",
        "CaveExitTask9",
        "CaveExitTask10",
    },
    required_prefabs = {
        "tentacle_pillar_atrium",
        "tentacle_pillar_atrium",
    },
    set_pieces = { -- if you add or remove tasks, don't forget to update this list!
        ["TentaclePillar"] = { count = 10, tasks= {
            "MudWorld", "MudCave", "MudLights", "MudPit", "BigBatCave", "RockyLand", "RedForest", "GreenForest", "BlueForest", "SpillagmiteCaverns", "SwampySinkhole", "CaveSwamp", "UndergroundForest", "PleasantSinkhole", "FungalNoiseForest", "FungalNoiseMeadow", "BatCloister", "RabbitTown", "RabbitCity", "SpiderLand", "RabbitSpiderWar", "CentipedeCaveTask",
        } },
        ["ResurrectionStone"] = { count = 2, tasks={
            "MudWorld", "MudCave", "MudLights", "MudPit", "BigBatCave", "RockyLand", "RedForest", "GreenForest", "BlueForest", "SpillagmiteCaverns", "SwampySinkhole", "CaveSwamp", "UndergroundForest", "PleasantSinkhole", "FungalNoiseForest", "FungalNoiseMeadow", "BatCloister", "RabbitTown", "RabbitCity", "SpiderLand", "RabbitSpiderWar", "CentipedeCaveTask",
        } },
        ["skeleton_notplayer"] = { count = 1, tasks={
            "MudWorld", "MudCave", "MudLights", "MudPit", "BigBatCave", "RockyLand", "RedForest", "GreenForest", "BlueForest", "SpillagmiteCaverns", "SwampySinkhole", "CaveSwamp", "UndergroundForest", "PleasantSinkhole", "FungalNoiseForest", "FungalNoiseMeadow", "BatCloister", "RabbitTown", "RabbitCity", "SpiderLand", "RabbitSpiderWar", "CentipedeCaveTask",
        } },
        ["TentaclePillarToAtrium"] = { count = 1, tasks={ "BigBatCave", "GreenForest", "CentipedeCaveTask" } }, -- This set piece data connects it to the atrium_start set piece.
    },
})

return datas