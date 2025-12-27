import math

from .lua_modules import ModuleWrapper
from .lua_functions import lua_pairs
from .lua_modules import LuaTableModule
from .lua_types import LuaTable

__all__ = ["LUA_BUILTINS", "LuaTable"]

LUA_BUILTINS = {
    # "true": True,
    # "false": False,
    "math": ModuleWrapper(math),
    "string": ModuleWrapper(str),
    "pairs": lua_pairs,
    "table": ModuleWrapper(LuaTableModule),
}
