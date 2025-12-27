import math
import zipfile
import random
import copy
import time
import re
from typing import Optional

from luaparser.ast import parse, walk, to_pretty_str
from luaparser.astnodes import (
    Table,
    Function,
    LocalFunction,
    Method,
    AnonymousFunction,
)

from lua_types import LuaTable, DummyTable, Entity, LuaUnpack
from constants import SCRIPTS_PATH

# built-in
lua_math = LuaTable()


def _math_random(a=None, b=None):
    if a is None and b is None:
        a = 0
        b = 1
    elif a is not None and b is None:
        return a * random.random()
    return random.randint(a, b)


def _math_clamp(num, min, max):
    return num <= min and min or (num >= max and max or num)


lua_math._data = {
    "pi": math.pi,
    "huge": math.inf,  # float("inf")相同
    "sqrt": math.sqrt,
    "ceil": math.ceil,
    "floor": math.floor,
    "pow": math.pow,  # 运算符^不能处理小数整数混合的情况
    "sin": math.sin,
    "cos": math.cos,
    "abs": abs,
    "asin": math.asin,
    "random": _math_random,
    "max": max,
    "min": min,
    "atan2": math.atan2,
    "clamp": _math_clamp,
}

lua_table = LuaTable()


def _table_insert(tbl, val, index=None):
    assert isinstance(tbl, LuaTable), "table.insert only call on a luatable"
    idx = index or 1
    while True:
        if idx not in tbl._data:
            tbl._data[idx] = val
            return
        idx = idx + 1


def _table_unpack(tbl: LuaTable, i=None, j=None):
    if tbl is None:
        return None
    i = i or 1
    res = []
    while True:
        if i in tbl._data:
            res.append(tbl._data[i])
        else:
            break
        if j:
            if i > j:
                break
        i += 1
    return LuaUnpack(*res)


def _table_concat(tbl, sep="", i=0, j=None):
    list_ = []
    i = i + 1
    if j is None:
        j = len(tbl)
    while i <= j:
        list_.append(str(tbl[i]))
        i = i + 1
    return sep.join(list_)


def _table_contains(tbl: Optional[LuaTable], ele):
    return ele in tbl._data.values()


def _table_remove(tbl: LuaTable, index=None):
    max_idx = tbl.max_pos()
    if index is None:
        del tbl._data[max_idx]
        return
    if max_idx:
        idx = index
        while idx < max_idx:
            tbl._data[idx] = tbl._data[idx + 1]
            idx += 1
    else:
        # 表里没有数字索引
        raise Exception("no number idx in LuaTable while remove")


lua_table._data = {
    "insert": _table_insert,
    "unpack": _table_unpack,
    "concat": _table_concat,
    "contains": _table_contains,
    "remove": _table_remove,
}

LUA_MODULES = {}


def _require(interpreter, arg: str):
    if arg in LUA_MODULES:
        return LUA_MODULES[arg]
    if arg.startswith("stategraphs/"):
        # 暂时无视状态图
        return None
    if arg.startswith("screens/"):
        return None
    if arg.startswith("widgets/"):
        return None
    if arg == "strings":
        return None
    with zipfile.ZipFile(SCRIPTS_PATH) as zip_ref:
        scripts_path = zipfile.Path(zip_ref, "scripts/")
        sub_path = arg
        path = scripts_path.joinpath(sub_path + ".lua")
        if not path.exists():
            raise Exception(f"require path {sub_path} not exists")
        lua_code = path.read_text(errors="ignore")
    tree = parse(lua_code)
    res = interpreter.visit(tree)
    LUA_MODULES[arg] = res
    return res


_require.need_interp = True

lua_string = LuaTable()


def _string_len(s):
    return len(s)


def _string_find(s, pattern, init=1, plain=False):
    # (fixme)瞎写的
    s = s[init - 1 :]
    start = s.find(pattern) + 1
    end = start + len(pattern)
    return start + init - 1, end + init - 1


def _string_gsub(s, pattern, repl, n=None):
    # (fixme)没考虑正则，没考虑repl是表和function的情况
    count = n if n is not None else -1
    return s.replace(pattern, repl, count)


def _string_char(*args):
    s = ""
    for arg in args:
        s += chr(arg)
    return s


def _string_sub(s, i, j=None):
    if i >= 0:
        i = i - 1
    if j is None:
        return s[i:]
    else:
        if j > 0:
            j = j - 1
        return s[i:j]


def _string_match(s, pattern):
    match = re.search(pattern, s)
    if match:
        return match.group(1)
    return None


lua_string._data = {
    "len": _string_len,
    "find": _string_find,
    "gsub": _string_gsub,
    "char": _string_char,
    "upper": str.upper,
    "lower": str.lower,
    "format": str.format,
    "sub": _string_sub,
    "match": _string_match,
}


def lua_type(obj):
    if obj is None:
        return "nil"
    elif isinstance(obj, (int, float)):
        return "number"
    elif isinstance(obj, str):
        return "string"
    elif isinstance(obj, LuaTable):
        return "table"
    elif isinstance(obj, (Function, LocalFunction, Method, AnonymousFunction)):
        return "function"
    else:
        raise Exception(f"unknown type {obj}")


def _set_metatable(interp, tbl, mt):
    # (fixme)
    tbl._meta_table = mt


_set_metatable.need_interp = True


def lua_assert(interp, expr, message="no assert msg"):
    if not interp.visit(expr):
        msg = interp.visit(message)
        print(f"Lua Assert: {msg}")


lua_assert.need_interp = True


def _next(obj):
    if isinstance(obj, LuaTable):
        iter_ = iter(obj._data)
        try:
            next_key = next(iter_)
        except StopIteration:
            return
        else:
            return obj._data[next_key]
    return


# dst
# tech_tree = LuaTable()
# tech_tree.AVAILABLE_TECH = {
#     "SCIENCE",
#     "MAGIC",
#     "ANCIENT",
#     "CELESTIAL",
#     "MOON_ALTAR",
#     "SHADOW",
#     "CARTOGRAPHY",
#     "SEAFARING",
#     "SCULPTING",
#     "ORPHANAGE",
#     "PERDOFFERING",
#     "WARGOFFERING",
#     "PIGOFFERING",
#     "CARRATOFFERING",
#     "BEEFOFFERING",
#     "CATCOONOFFERING",
#     "RABBITOFFERING",
#     "DRAGONOFFERING",
#     "MADSCIENCE",
#     "CARNIVAL_PRIZESHOP",
#     "CARNIVAL_HOSTSHOP",
#     "FOODPROCESSING",
#     "FISHING",
#     "WINTERSFEASTCOOKING",
#     "HERMITCRABSHOP",
#     "TURFCRAFTING",
#     "MASHTURFCRAFTING",
#     "SPIDERCRAFT",
#     "ROBOTMODULECRAFT",
#     "BOOKCRAFT",
#     "LUNARFORGING",
#     "SHADOWFORGING",
#     "CARPENTRY",
# }
# def _create(t):
#     r = LuaTable()
#     for v in tech_tree.AVAILABLE_TECH:
#         if v not in t:
#             t[v] = 0
#     return t
# tech_tree.Create = _create

# 一个简单的WORLD_TILES定义表
tree = parse(
    """
local a = {
    INVALID = 65535,
    IMPASSABLE = 1,
    ROAD = 2,
    ROCKY = 3,
    DIRT = 4,
    SAVANNA = 5,
    GRASS = 6,
    FOREST = 7,
    MARSH = 8,
    WEB = 9,
    WOODFLOOR = 10,
    CARPET = 11,
    CHECKER = 12,
    CAVE = 13,
    FUNGUS = 14,
    SINKHOLE = 15,
    UNDERROCK = 16,
    MUD = 17,
    BRICK = 18,
    BRICK_GLOW = 19,
    TILES = 20,
    TILES_GLOW = 21,
    TRIM = 22,
    TRIM_GLOW = 23,
    FUNGUSRED = 24,
    FUNGUSGREEN = 25,
    DECIDUOUS = 30,
    DESERT_DIRT = 31,
    SCALE = 32,
    LAVAARENA_FLOOR = 33,
    LAVAARENA_TRIM = 34,
    QUAGMIRE_PEATFOREST = 35,
    QUAGMIRE_PARKFIELD = 36,
    QUAGMIRE_PARKSTONE = 37,
    QUAGMIRE_GATEWAY = 38,
    QUAGMIRE_SOIL = 39,
    QUAGMIRE_CITYSTONE = 41,
    PEBBLEBEACH = 42,
    METEOR = 43,
    SHELLBEACH = 44,
    ARCHIVE = 45,
    FUNGUSMOON = 46,
    FARMING_SOIL = 47,
    FUNGUSMOON_NOISE = 120,
    METEORMINE_NOISE = 121,
    METEORCOAST_NOISE = 122,
    DIRT_NOISE = 123,
    ABYSS_NOISE = 124,
    GROUND_NOISE = 125,
    CAVE_NOISE = 126,
    FUNGUS_NOISE = 127,
    UNDERGROUND = 128,
    WALL_ROCKY = 151,
    WALL_DIRT = 152,
    WALL_MARSH = 153,
    WALL_CAVE = 154,
    WALL_FUNGUS = 155,
    WALL_SINKHOLE = 156,
    WALL_MUD = 157,
    WALL_TOP = 158,
    WALL_WOOD = 159,
    WALL_HUNESTONE = 160,
    WALL_HUNESTONE_GLOW = 161,
    WALL_STONEEYE = 162,
    WALL_STONEEYE_GLOW = 163,
    FAKE_GROUND = 200,
    OCEAN_START = 201,
    OCEAN_COASTAL = 201,
    OCEAN_COASTAL_SHORE = 202,
    OCEAN_SWELL = 203,
    OCEAN_ROUGH = 204,
    OCEAN_BRINEPOOL = 205,
    OCEAN_BRINEPOOL_SHORE = 206,
    OCEAN_HAZARDOUS = 207,
    OCEAN_WATERLOG = 208,
    OCEAN_END = 247,
}
"""
)
world_tiles = LuaTable()
for node in walk(tree):
    if isinstance(node, Table):
        for field in node.fields:
            world_tiles._data[field.key.id] = field.value.n

SCANNED_PREFABS = {}


def _prefab(interp, name, fn, assets=None, deps=None, force_path_search=False):
    inst = interp._execute_call(fn, [])
    if inst is None:
        print(f"Prefab:{name} resolve to None")
    else:
        SCANNED_PREFABS[name] = inst
        # print(
        #     f"{name}",
        #     f":{inst.prefab_name_override}" \
        #         if inst.prefab_name_override else "",
        #     # f"tags:{inst.tags}",
        #     f"assets:{assets}" if assets else "",
        #     )
        return inst


_prefab.need_interp = True


def _create_entity(*args):
    return Entity()


loot_tables = LuaTable()


def _set_shared_loot_table(name: str, tbl: LuaTable):
    loot_tables[name] = tbl


class Vector3:
    def __init__(self, x=0, y=0, z=0, *args) -> None:
        # args是多余的，但是代码中有错误的四个参数的调用
        self.x = x
        self.y = y
        self.z = z

    def __str__(self) -> str:
        return f"Vector3({self.x}, {self.y}, {self.z})"

    def __getitem__(self, index):
        if index in "xyz":
            return getattr(self, index)
        elif index == "Get":
            return lambda x: LuaTable(self.x, self.y, self.z)
        return None


class Asset:
    def __init__(self, type, file=None, param=None) -> None:
        self.type = type
        self.file = file
        self.param = param

    def __str__(self) -> str:
        return f"Asset:{self.type}|{self.file}"


class DummyString:
    # STRINGS的假体实现 节省资源
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent

    def __getitem__(self, index):
        return DummyString(name=index, parent=self)

    def __str__(self) -> str:
        obj = self
        names = []
        while obj.parent:
            names.append(obj.name)
            obj = obj.parent
        return ".".join(names)

    def __iter__(self):
        for k, v in (
            ("DUMMY_K_A", DummyString("DUMMY_K_A", self)),
            ("DUMMY_K_B", DummyString("DUMMY_K_B", self)),
        ):
            yield k, v


def _deepcopy(obj):
    return copy.deepcopy(obj)


def _the_world_push_event(self, *args, **kwds):
    return None


_the_world = LuaTable()
_the_world_state = LuaTable()
_the_world_state._data = {
    # worldstate.lua
    "season": "autumn",
    "isautumn": True,
    "iswinter": False,
    "isspring": False,
    "issummer": False,
    "israining": False,
    "remainingdaysinseason": 15,
    "snowlevel": 0,
    "iswet": False,
    "cycles": 5,
    "issnowcovered": False,
    "issnowing": False,
    "time": 1,
    "isday": True,
    "isdusk": False,
    "isnight": False,
    "iscaveday": True,
    "iscavenight": False,
    "isfullmoon": False,
    "isacidraining": False,
    "timeinphase": 0.2,
    "temperature": 25,
    "precipitationrate": 0.5,
    "autumnlength": 20,
    "winterlength": 15,
    "sprintlength": 20,
    "summerlength": 15,
    "wetness": 0,
    "phase": "day",
    "lunarhaillevel": 0,
}
_the_world._data = {
    "ismastersim": False,
    "state": _the_world_state,
    "HasTag": lambda x, y: True,
    "components": DummyTable(),
    "PushEvent": _the_world_push_event,
}

_the_sim = LuaTable()
_the_sim._data = {
    "GetTickTime": lambda x: 0.03333,
    "AtlasContains": lambda x, y, z: True,
}

_the_net = LuaTable()
_the_net._data = {
    "IsDedicated": lambda x: True,
    "GetIsClient": lambda x: False,
    "GetServerGameMode": lambda x: dict(
        modded_mode=True,
        text="game_mode_text",
        description="",
        level_type="survival",
        mod_game_mode=True,
        spawn_mode="fixed",
        resource_renewal=False,
        ghost_sanity_drain=False,
        ghost_enabled=True,
        portal_rez=True,
        reset_time=True,
        invalid_recipes={},
    ),
}

_loc = LuaTable()
_loc._data = {
    "GetTextScale": lambda: 1,
}


def _event_server_data(*args, **kwds):
    return DummyTable()


def _spawn_prefab(name):
    return Entity()


_the_camera = DummyTable()
_the_camera._data = {
    "GetDownVec": lambda x: Vector3(0, 0, 0),
}

G = {
    # built-ins
    "math": lua_math,
    "table": lua_table,
    "string": lua_string,
    "unpack": _table_unpack,
    "require": _require,
    "type": lua_type,
    "setmetatable": _set_metatable,
    "assert": lua_assert,
    "print": print,
    "tostring": str,
    "next": _next,
    # for dst
    "overrides": None,
    "RADIANS": 180 / 3.14,
    "PLAYER_CAMERA_SEE_DISTANCE": 40.0,
    "FRAMES": 1 / 30,
    # "TechTree": tech_tree,
    "Prefab": _prefab,
    "WORLD_TILES": world_tiles,
    "BRANCH": "staging",
    "LootTables": loot_tables,
    "SetSharedLootTable": _set_shared_loot_table,
    "Vector3": Vector3,
    "Asset": Asset,
    "IsSteamDeck": lambda: True,
    "IsConsole": lambda: True,
    "IsNotConsole": lambda: False,
    "IsLinux": lambda: False,
    "IsPS4": lambda: False,
    "PLATFORM": "WIN32_STEAM",
    "deepcopy": _deepcopy,
    "STRINGS": DummyString("STRINGS"),
    "TheWorld": _the_world,
    "TheSim": _the_sim,
    "TheNet": _the_net,
    "CreateEntity": _create_entity,
    "EnvelopeManager": DummyTable(),
    "CreateSphereEmitter": DummyTable(),
    "EmitterManager": DummyTable(),
    "LOC": _loc,
    "event_server_data": _event_server_data,
    "SpawnPrefab": _spawn_prefab,
    "ACTIONS": DummyTable(),
    "AllPlayers": LuaTable(),
    "GetGhostEnabled": lambda: True,
    "GetGameModeProperty": DummyTable(),
    "GetMaxItemSlots": lambda x: 15,
    "GetTime": time.time,
    "MakeInventoryPhysics": DummyTable(),
    "MakeCharacterPhysics": DummyTable(),
    "MakeInventoryFloatable": DummyTable(),
    "net_float": DummyTable(),
    "net_bool": DummyTable(),
    "net_tinybyte": DummyTable(),
    "net_smallbytearray": DummyTable(),
    "Profile": DummyTable(),
    "TheCamera": _the_camera,
    "AllRecipes": LuaTable(),
    "SetLunarHailBuildupAmountSmall": lambda x: None,
    "MakeCollidesWithElectricField": lambda x: None,
}
