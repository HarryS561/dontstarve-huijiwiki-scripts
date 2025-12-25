# 继承dict会导致json序列化时无法调用to_json方法，因此需要自定义LuaTable类
class LuaTable:

    def __init__(self, *args, **kwargs):
        self.table = dict()
        self.table.update(dict(*args, **kwargs))

    def __getitem__(self, key):
        # 未定义的key返回None
        # 其余同dict的行为
        return self.table.get(key, None)

    def __setitem__(self, key, value):
        self.table[key] = value

    def __delitem__(self, key):
        del self.table[key]

    def __len__(self):
        return len(self.table)

    def __iter__(self):
        return iter(self.table)

    def __repr__(self):
        return repr(self.table)

    def __str__(self):
        return str(self.table)

    # 访问属性时如果属性不存在则访问__getitem__
    def __getattr__(self, key):
        return self.table.get(key, None)

    def __setattr__(self, key, value):
        if key in ("table",):
            super().__setattr__(key, value)
        else:
            self.table[key] = value

    def __contains__(self, key):
        return key in self.table

    def keys(self):
        return self.table.keys()

    def values(self):
        return self.table.values()

    def items(self):
        return self.table.items()

    def to_json(self):
        # 如果表中键是数字序列，则转换为数组
        # print(f"check to json for table {self}")
        if all(isinstance(k, int) for k in self.keys()):
            # print("regard table as array")
            res = [self[k] for k in sorted(self.keys())]
            # print(res)
            return res
        # print("regard table as dict")
        return self.table
