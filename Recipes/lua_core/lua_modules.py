from .lua_types import LuaTable


class ModuleWrapper:
    # 将模组包裹起来，使得模组内对象可以以键的方式访问
    def __init__(self, module):
        self.module = module

    def __getitem__(self, key):
        return getattr(self.module, key)


class LuaTableModule:

    @staticmethod
    def insert(tbl: LuaTable, val, index=None):
        assert isinstance(
            tbl, LuaTable
        ), "table.insert only call on a Luatable"
        idx = index or 1
        while True:
            if idx not in tbl:
                tbl[idx] = val
                return
            idx = idx + 1

    # def _table_unpack(tbl: LuaTable, i=None, j=None):
    #     if tbl is None:
    #         return None
    #     i = i or 1
    #     res = []
    #     while True:
    #         if i in tbl._data:
    #             res.append(tbl._data[i])
    #         else:
    #             break
    #         if j:
    #             if i > j:
    #                 break
    #         i += 1
    #     return LuaUnpack(*res)

    # def _table_concat(tbl, sep="", i=0, j=None):
    #     l = []
    #     i = i + 1
    #     if j is None:
    #         j = len(tbl)
    #     while i <= j:
    #         l.append(str(tbl[i]))
    #         i = i + 1
    #     return sep.join(l)

    @staticmethod
    def contains(tbl: LuaTable, ele):
        assert isinstance(
            tbl, LuaTable
        ), "table.contains only call on a Luatable"
        # 只考虑作为数组使用的情况
        return ele in tbl.values()

    # def _table_remove(tbl: LuaTable, index=None):
    #     max_idx = tbl.max_pos()
    #     if index is None:
    #         del tbl._data[max_idx]
    #         return
    #     if max_idx:
    #         idx = index
    #         while idx < max_idx:
    #             tbl._data[idx] = tbl._data[idx+1]
    #             idx += 1
    #     else:
    #         # 表里没有数字索引
    #         raise Exception(f"no number idx in LuaTable while remove")
