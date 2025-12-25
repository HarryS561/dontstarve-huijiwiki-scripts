from typing import Any, Dict, Iterable, Iterator, Tuple


def is_hashable(value):
    try:
        hash(value)
        return True
    except TypeError:
        return False


# Lua -> Python的数据结构
class LuaTable:
    """A light-weight emulation of Lua's table semantics.

    - Keys may be ints/strings/tuples/etc. Missing keys return None.
    - Assigning None deletes the key (Lua: setting to nil removes it).
    - insert(value, pos) shifts numeric keys >= pos upwards.
    - Iteration yields (k, v) pairs (used by Interpreter.pairs).
    """

    def __init__(self, *args) -> None:
        self._data: Dict[Any, Any] = {}
        for arg in args:
            self.insert(arg)

    def insert(self, value, pos: int | None = None):
        """Insert value into array part.

        If pos is None, append at the first free positive integer index.
        If pos is provided and occupied, shift integer keys >= pos upward.
        """
        if pos is None:
            pos = 1
            while pos in self._data:
                pos += 1
        else:
            # shift numeric keys >= pos up by 1 (descending order)
            numeric_keys = [
                k for k in self._data.keys() if isinstance(k, int) and k >= pos
            ]
            for k in sorted(numeric_keys, reverse=True):
                self._data[k + 1] = self._data[k]
                # delete old key after moving to avoid duplicates
                del self._data[k]
        self._data[pos] = value

    def max_pos(self) -> int:
        """Return the maximum contiguous positive integer index from 1."""
        pos = 1
        while pos in self._data:
            pos += 1
        return pos - 1

    def __getitem__(self, index):
        """支持索引访问；不可哈希索引返回 None（Lua 的 nil）。"""
        try:
            return self._data.get(index, None)
        except TypeError:
            return None

    def __setitem__(self, index, value):
        """支持索引赋值；将 None 视为删除该键（Lua 的赋 nil）。"""
        if value is None:
            # delete if exists
            try:
                del self._data[index]
            except Exception:
                pass
        else:
            self._data[index] = value

    def keys(self) -> Iterable[Any]:
        return list(self._data.keys())

    def values(self) -> Iterable[Any]:
        return list(self._data.values())

    def items(self) -> Iterable[Tuple[Any, Any]]:
        return list(self._data.items())

    def to_dict(self) -> Dict[Any, Any]:
        """Shallow copy to a plain dict."""
        return dict(self._data)

    def __repr__(self) -> str:
        return f"LuaTable({self._data!r})"

    def __str__(self) -> str:
        # Safe shallow repr to avoid infinite recursion.
        parts = []
        for k, v in self._data.items():
            # avoid calling __str__ on nested LuaTable to prevent recursion
            if isinstance(k, LuaTable):
                k_s = f"<LuaTable id={id(k)}>"
            else:
                k_s = repr(k)
            if isinstance(v, LuaTable):
                v_s = f"<LuaTable id={id(v)}>"
            else:
                v_s = repr(v)
            parts.append(f"{k_s}:{v_s}")
        return "{" + ", ".join(parts) + "}"

    def __contains__(self, item):
        return item in self._data

    def __len__(self):
        return len(self._data)

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        # Return the value under "_ctor" if present.
        return self._data.get("_ctor", None)

    def __iter__(self) -> Iterator[Tuple[Any, Any]]:
        # yield (k, v) pairs to match Interpreter.pairs behavior
        for k, v in self._data.items():
            yield k, v


class LuaVarArgs(list):
    pass


class LuaUnpack:
    def __init__(self, *args, **kwds) -> None:
        self.args = args


class DummyTable(LuaTable):
    # 当作函数调用时不解析参数
    ignore_args = True

    # 一个总是可以访问键且可以调用的lua表
    def __init__(self):
        super().__init__()

    def __getitem__(self, index):
        """不存在的键值设为 DummyTable 并返回它（链式访问友好）。"""
        res = super().__getitem__(index)
        if res is None:
            res = DummyTable()
            # store dummy only for hashable keys
            try:
                self._data[index] = res
            except TypeError:
                # unhashable key: just return dummy without storing
                pass
        return res

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        # 有 run 方法则运行 run，否则返回 DummyTable（允许链式调用）
        fn = getattr(self, "run", False)
        if fn:
            res = self.run(*args, **kwds)
            return res
        return DummyTable()

    # arithmetic / comparison fallbacks to be permissive in scripts parsing
    def __add__(self, other):
        return other

    def __mul__(self, other):
        return other

    def __rmul__(self, other):
        return other

    def __eq__(self, value: object) -> bool:
        return True

    def __gt__(self, value):
        return True

    def __lt__(self, value):
        return True

    def __le__(self, value):
        return True

    def __ne__(self, value):
        return True

    def __ge__(self, value):
        return True

    def __sub__(self, value):
        return 0

    def __rsub__(self, value):
        return value

    def __truediv__(self, value):
        return value

    def __hash__(self) -> int:
        return hash("DummyTable")

    def __neg__(self):
        return 0


class Entity(DummyTable):
    # 在 DummyTable 的基础上补充一些 entity 默认有的属性和方法
    def __init__(self) -> None:
        super().__init__()
        self.tags = set()
        self["components"] = DummyTable()
        self["entity"] = DummyTable()
        self["AnimState"] = DummyTable()
        anim = self["AnimState"]
        anim["GetCurrentAnimationNumFrames"] = _animstate_getanimnumframes
        self["AddTag"] = _add_tag
        self["SetPrefabNameOverride"] = _set_prefab_name_override
        self["AddComponent"] = _add_component
        self.prefab_name_override = None


def _set_prefab_name_override(self, override):
    self.prefab_name_override = override


def _add_tag(self, tag, *args, **kwds):
    self.tags.add(tag)


def _add_component(self, comp_name, *args, **kwds):
    res = self["components"][comp_name] = DummyTable()
    return res


def _animstate_getanimnumframes(self):
    return 30
