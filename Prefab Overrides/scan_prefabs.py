import zipfile
import json
import os
from contextlib import redirect_stdout

from luaparser import ast

from constants import SCRIPTS_PATH, CHARACTERS
from lua_globals import G, LUA_MODULES, SCANNED_PREFABS
from interpreter import (
    Scope,
    Interpreter,
    PrefabInterpreter,
    ConstantsInterpreter,
)


def interpret_file(path, Interp=Interpreter, scopes=None):
    with zipfile.ZipFile(SCRIPTS_PATH) as zip_ref:
        p = zipfile.Path(zip_ref, f"scripts/{path}.lua")
        lua_code = p.read_text()
    with open(os.devnull, "w") as f:
        with redirect_stdout(f):
            tree = ast.parse(lua_code)
            i = Interp()
            i.scope.variables.update(G)
            if scopes:
                for scope in scopes:
                    i.scope.variables.update(scope.variables)
            res = i.visit(tree)
    LUA_MODULES[path] = res
    return i


def scan_prefabs_in_zip(zip_path, should_ignore=None, scope=None):
    """
    扫描压缩包内 scripts/prefabs/ 下所有 Lua 文件，解析并执行 PrefabInterpreter。
    支持忽略列表和前缀过滤。
    """
    import zipfile
    from luaparser import ast

    i = PrefabInterpreter()
    if scope is None:
        scope = Scope()
    i.scope.variables.update(scope.variables)
    with zipfile.ZipFile(zip_path) as zip_ref:
        prefabs = zipfile.Path(zip_ref, "scripts/prefabs/")
        for path in prefabs.iterdir():
            if should_ignore and should_ignore(path.name):
                print(f"skipping {path.name}")
                continue
            print(f"visiting {path.name}")
            try:
                lua_code = path.read_text()
                with open(os.devnull, "w") as f:
                    with redirect_stdout(f):
                        tree = ast.parse(lua_code)
                        i.visit(tree)
            except Exception as e:
                print(f"Failed to parse {path.name}: {e}")
    return i


def dump_prefab_overrides():
    overrides = {}
    for name, inst in sorted(SCANNED_PREFABS.items(), key=lambda x: x[0]):
        override = getattr(inst, "prefab_name_override", False)
        if override:
            overrides[name] = override
    output_path = "prefab_name_overrides.json"
    with open(output_path, "w") as fp:
        json.dump(overrides, fp, indent=4, ensure_ascii=False)
    print(f"Dumped prefab overrides to {output_path}")


def get_prefab_name_override():
    """
    预处理基础模块后，扫描所有 prefabs 并保存 prefab_name_override。
    """
    scope = Scope()
    # 预处理基础模块
    scope.variables.update(G)
    for mod, interp_cls in [
        ("class", Interpreter),
        ("constants", ConstantsInterpreter),
        ("simutil", Interpreter),
        ("vecutil", Interpreter),
        ("prefabutil", Interpreter),
        ("tuning", ConstantsInterpreter),
    ]:
        i = interpret_file(mod, interp_cls, scopes=(scope,))
        scope.variables.update(i.scope.variables)
    # 解析所有 prefabs
    IGNORE_PREFABS = {
        "skinprefabs",
        "cave",
        "world",
        "forest",
        "frontend",
        "balloonparty",
        "meteorwarning",
        "minimap",
        "carnival_food",
        "waxed_plants",
        "snowman",
        "treasurechest",
        "nightmarecreature",
        "shadowcreature",
        "container_classified",
        "walter",
        "tentacle_pillar",
        "nightmarerock",
        "woby_rack",
        "ugc_swap_fx",
    }
    IGNORE_PREFABS = IGNORE_PREFABS.union(CHARACTERS)
    SKIP_PREFIXES = ("quagmire",)

    # lava 但不 lavae
    def skip_prefab(name: str) -> bool:
        prefab = name.rsplit(".", maxsplit=1)[0]
        return (
            (not name.endswith(".lua"))
            or prefab in IGNORE_PREFABS
            or name.startswith(SKIP_PREFIXES)
            or (name.startswith("lava") and not name.startswith("lavae"))
        )

    scan_prefabs_in_zip(
        SCRIPTS_PATH,
        should_ignore=skip_prefab,
        scope=scope,
    )
