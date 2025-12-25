class LuaNameError(Exception):
    def __init__(self, message="变量名在定义前被访问"):
        self.message = message
        super().__init__(self.message)


class LuaReturn(Exception):
    def __init__(self, message="Lua返回值", value=None):
        self.message = message
        self.value = value
        super().__init__(self.message)


class LuaBreak(Exception):
    def __init__(self, message="Lua跳出循环"):
        self.message = message
        super().__init__(self.message)
