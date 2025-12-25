import copy
import math
from contextlib import contextmanager
from typing import Optional

from luaparser import ast

from exceptions import LuaNameError, LuaReturn, LuaBreak
from lua_types import LuaTable, LuaVarArgs, LuaUnpack
from lua_globals import Vector3


class Scope:
    id = 1

    def __init__(self, parent=None, interp=None):
        self.parent: None | Scope = parent
        self.interp: Optional[Interpreter] = interp or (
            parent.interp if parent else None
        )
        self.variables = {}
        self.id = self.new_id()

    @classmethod
    def new_id(cls):
        res = cls.id
        cls.id += 1
        return res

    def define(self, name: str, value):
        # 用于LocalAssign
        self.variables[name] = value

    def assign(self, name, value):
        # 用于Assign
        scope = self
        while scope.parent:
            if name in scope.variables:
                scope.define(name, value)
                break
            scope = scope.parent
        else:
            scope.define(name, value)

    @property
    def level(self) -> int:
        level = 1
        scope = self
        while scope.parent:
            scope = scope.parent
            level += 1
        return level

    def lookup(self, name: str):
        """从最内层scope找name，若没有逐层向外找，直到找到返回值或是抛出异常"""
        if name in self.variables:
            return self.variables[name]
        elif self.parent is not None:
            return self.parent.lookup(name)
        else:
            raise LuaNameError(f"name '{name}' is not defined")

    @contextmanager
    def create_child_scope(self, interp=None):
        # interp和self.scope在多个interp之间共享过程中可能不是同一个
        # 这在处理函数闭包时需要额外注意
        if self.interp is None:
            raise ValueError("Scope must have an interpreter")
        try:
            scope = Scope(parent=self, interp=interp or self.interp)
            if interp:
                interp.scope = scope
            else:
                self.interp.scope = scope
            yield scope
        finally:
            self.interp.scope = self

    @property
    def top_scope(self):
        scope = self
        while scope.parent:
            scope = scope.parent
        return scope

    def content(self):
        s = ""
        for k, v in self.variables.items():
            s += f"K: {k} V: {v}\n"
        return s

    def __deepcopy__(self, memo):
        scope = Scope(parent=self.parent, interp=self.interp)
        scope.variables = copy.deepcopy(scope.variables)
        memo[id(self)] = scope
        return scope

    def __str__(self):
        return f"scope{self.id}: in level: {self.level}"


class Interpreter:
    IGNORE_NAMES = set()
    IGNORE_FUNCS = set()
    # Cache operator mappings to avoid recreating dicts on every visit
    REL_OPS = {
        "RLtOp": lambda x, y: x < y,
        "RGtOp": lambda x, y: x > y,
        "RLtEqOp": lambda x, y: x <= y,
        "RGtEqOp": lambda x, y: x >= y,
        "REqOp": lambda x, y: x == y,
        "RNotEqOp": lambda x, y: x != y,
    }

    ARI_OPS = {
        "AddOp": lambda x, y: x + y,
        "SubOp": lambda x, y: x - y,
        "MultOp": lambda x, y: x * y,
        "FloatDivOp": lambda x, y: x / y,
        "FloorDivOp": lambda x, y: x // y,
        "ModOp": lambda x, y: x % y,
        "ExpoOp": lambda x, y: math.pow(x, y),
    }

    UNARY_OPS = {
        "UMinusOp": lambda x: -x,
        "UBNotOp": lambda x: ~x,
        "ULNotOp": lambda x: not x,
        "ULengthOp": lambda x: len(x),
    }

    def __init__(self):
        self.scope = Scope(interp=self)
        self.scope_stack = []
        self.first_block_scope = None  # 最外层Block的scope 用于调试打印
        for fn_name in self.IGNORE_FUNCS:
            self.scope.variables[fn_name] = _dummy_fn

    def visit(self, node: ast.Node):
        method_name = "visit_" + type(node).__name__
        # logger.debug(f"Visiting {method_name}")
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ast.Node):
        if isinstance(node, ast.RelOp):
            return self.visit_RelOp(node)
        elif isinstance(node, ast.AriOp):
            return self.visit_AriOp(node)
        elif isinstance(node, ast.UnaryOp):
            return self.visit_UnaryOp(node)
        elif isinstance(node, ast.LoOp):
            return self.visit_LoOp(node)
        elif isinstance(node, (ast.Nil, ast.TrueExpr, ast.FalseExpr)):
            if isinstance(node, ast.Nil):
                return None
            elif isinstance(node, ast.TrueExpr):
                return True
            else:
                return False
        elif isinstance(node, ast.Dots):
            return self.visit_Dots(node)
        elif isinstance(
            node,
            (
                int,
                float,
                str,
                bool,
                list,
                type(None),
                LuaTable,
                Vector3,
                type(_dummy_fn),
            ),
        ):
            return node
        elif isinstance(node, ast.Break):
            raise LuaBreak
        else:
            raise Exception(f"No visit_{type(node).__name__} method")

    def visit_Return(self, node: ast.Return):
        values = []
        if node.values:
            # 空return句的node.values=False
            for value in node.values:
                values.append(self.visit(value))
            if values:
                if len(values) > 1:
                    res = tuple(values)
                else:
                    res = values[0]
            else:
                res = None
        else:
            res = None
        raise LuaReturn("Lua返回值", res)

    def visit_LocalFunction(self, node: ast.LocalFunction):
        node.scope = self.scope
        self.scope.define(node.name.id, node)
        # 返回值用于该函数对象被返回然后赋值给变量时
        return node

    def visit_Function(self, node: ast.Function):
        node.scope = self.scope
        self._assign(node.name, node, True)
        # 返回值用于该函数对象被返回然后赋值给变量时
        return node

    def visit_Method(self, node: ast.Method):
        node.scope = self.scope
        cls_name = node.source.id
        cls: LuaTable = self.scope.lookup(cls_name)
        cls._data[node.name.id] = node
        node.args.insert(0, ast.Name("self"))
        # 返回值用于该函数对象被返回然后赋值给变量时
        return node

    def visit_AnonymousFunction(self, node: ast.AnonymousFunction):
        node.scope = self.scope
        return node

    def visit_Call(self, node: ast.Call):
        fn = self.visit(node.func)
        args = []
        if not getattr(fn, "ignore_args", False):
            # IGNORE_FUNCS无视参数解析
            for arg in node.args:
                parsed_arg = self.visit(arg)
                if isinstance(parsed_arg, LuaUnpack):
                    args = tuple(map(self.visit, parsed_arg.args))
                    break
                args.append(parsed_arg)
        if callable(fn):
            if getattr(fn, "need_interp", False):
                args.insert(0, self)
            if isinstance(node.func, LuaTable):
                # DST Class Implement in Lua
                ctor = node.func()
                self._execute_call(ctor, (node.func,))
                # 类初始化函数返回的是对象，即该表
                res = node.func
            else:
                res = fn(*args)
        else:
            res = self._execute_call(fn, args)
        return res

    def visit_Invoke(self, node: ast.Invoke):
        source = self.visit(node.source)
        if not isinstance(source, (LuaTable, Vector3)):
            source_class = {
                str: self.scope.lookup("string"),
            }[type(source)]
        else:
            source_class = source
        func_node = source_class[node.func.id]
        if getattr(func_node, "ignore_args", False):
            args = tuple()
        else:
            # avoid deepcopy of AST nodes; build arg list without mutating node
            # first arg is the source (table/self)
            args = tuple([source] + [self.visit(a) for a in node.args])
        if callable(func_node):
            res = func_node(*args)
        else:
            res = self._execute_call(func_node, args)
        return res

    def visit_Dots(self, node: ast.Dots):
        return self.scope.lookup("...")

    def _execute_call(self, func_node, args):
        self.scope_stack.append(self.scope)
        self.scope: Scope = func_node.scope
        with self.scope.create_child_scope(interp=self):
            for idx, param in enumerate(func_node.args):
                if idx < len(args):
                    if isinstance(param, ast.Varargs):
                        self.scope.define("...", LuaVarArgs(args[idx:]))
                        break
                    else:
                        self.scope.define(param.id, args[idx])
                else:
                    self.scope.define(param.id, None)
            try:
                self.visit(func_node.body)
            except LuaReturn as e:
                res = e.value
            else:
                res = None
        self.scope = self.scope_stack.pop()
        return res

    def visit_Index(self, node: ast.Index):
        idx = node.idx
        if isinstance(idx, ast.Name):
            k = (
                idx.id
                if node.notation == ast.IndexNotation.DOT
                else self.visit(idx)
            )
        else:
            k = self.visit(idx)
        source = self.visit(node.value)
        if source is None:
            return None
        return source[k]

    def visit_RelOp(self, node: ast.RelOp):
        fn = self.REL_OPS[node._name]
        return fn(self.visit(node.left), self.visit(node.right))

    def visit_AriOp(self, node: ast.AriOp):
        fn = self.ARI_OPS[node._name]
        try:
            res = fn(self.visit(node.left), self.visit(node.right))
        except ZeroDivisionError:
            res = float("inf")
        return res

    def visit_Concat(self, node: ast.Concat):
        left = self.visit(node.left)
        right = self.visit(node.right)
        return left + str(right)

    def visit_UnaryOp(self, node):
        fn = self.UNARY_OPS[node._name]
        return fn(self.visit(node.operand))

    def _is_lua_true(self, value):
        return not (value in (False, None))

    def visit_LoOp(self, node: ast.LoOp):
        if node._name == "LAndOp":
            if self._is_lua_true(self.visit(node.left)):
                return self.visit(node.right)
            else:
                return False
        elif node._name == "LOrOp":
            left = self.visit(node.left)
            if not self._is_lua_true(left):
                return self.visit(node.right)
            else:
                return left
        else:
            raise Exception(f"未知的逻辑符号 {node}")

    def visit_If(self, node: ast.If):
        if self._is_lua_true(self.visit(node.test)):
            self.visit(node.body)
        else:
            if node.orelse:
                self.visit(node.orelse)

    def visit_ElseIf(self, node: ast.ElseIf):
        if self._is_lua_true(self.visit(node.test)):
            self.visit(node.body)
        else:
            if node.orelse:
                self.visit(node.orelse)

    def visit_Chunk(self, node: ast.Chunk):
        try:
            self.visit(node.body)
        except LuaReturn as e:
            return e.value

    def _get_index_list(self, node: ast.Index):
        """解析一个Index结点，按调用顺序逆序返回标识符"""
        res = []
        if node.notation == ast.IndexNotation.DOT:
            res.append(node.idx.id)
        elif node.notation == ast.IndexNotation.SQUARE:
            res.append(self.visit(node.idx))
        else:
            raise Exception(
                "unknown IndexNotation type: " f"{type(node.notation)}"
            )
        if isinstance(node.value, ast.Name):
            res.append(node.value.id)
            return res
        elif isinstance(node.value, ast.Index):
            res.extend(self._get_index_list(node.value))
            return res
        elif isinstance(node.value, ast.Call):
            res.append(self.visit(node.value))
            return res
        else:
            raise Exception(
                "value of Index node neither Name nor Index: "
                f"{type(node.value)}"
            )

    def visit_Assign(self, node: ast.Assign):
        targets = node.targets
        values = node.values
        for idx, target in enumerate(targets):
            value_node = values[idx]
            if isinstance(target, ast.Name):
                name = target.id
                if name in self.IGNORE_NAMES:
                    try:
                        self.scope.lookup(name)
                    except LuaNameError:
                        # 仅在未定义时给忽略变量赋值
                        self._assign(target, None, True)
                    continue
            self._assign(target, value_node)

    def _assign(self, target, value_node, no_visit=False):
        if no_visit:
            # value_node不解析，用于函数定义的整体保存
            value = value_node
        else:
            value = self.visit(value_node)
        if isinstance(target, ast.Name):
            self.scope.assign(target.id, value)
        elif isinstance(target, ast.Index):
            index_list = self._get_index_list(target)
            root_name = index_list.pop()
            if not isinstance(root_name, str):
                # Index类型的前面可能是一个函数调用，此时是个返回结果(一定是表吗)
                v = root_name
            else:
                if root_name in self.IGNORE_NAMES:
                    return
                try:
                    v = self.scope.lookup(root_name)
                except LuaNameError:
                    top_scope = self.scope.top_scope
                    v = top_scope.variables[root_name] = LuaTable()
            while len(index_list) > 1:
                index = index_list.pop()
                # 这里有可能访问了未定义的属性 属于Lua代码本身的错误
                v = v[index]
            last_index = index_list.pop()
            v[last_index] = value
        else:
            raise Exception(f"unknown assign left value type: {type(target)}")

    def visit_LocalAssign(self, node: ast.LocalAssign):
        targets = node.targets
        values = node.values
        if values and (len(targets) > len(values)):
            # unpack 之类的返回多个值的函数调用
            _value = self.visit(values[0])
            if isinstance(_value, LuaUnpack):
                values = _value.args
            else:
                values = _value
        for idx, target in enumerate(targets):
            name = target.id
            if name in self.IGNORE_NAMES:
                if name not in self.scope.variables:
                    self.scope.define(name, None)
                continue
            if values and len(values) > idx:
                value = self.visit(values[idx])
            else:
                value = None
            self.scope.define(name, value)

    def visit_LuaTable(self, node: LuaTable):
        # 有时会懒得分辨是不是解析过的表
        return node

    def visit_Name(self, node: ast.Name):
        try:
            return self.scope.lookup(node.id)
        except LuaNameError:
            return None

    def visit_Number(self, node: ast.Number):
        return node.n

    def visit_Table(self, node: ast.Table):
        tbl = LuaTable()
        for field in node.fields:
            if isinstance(field.value, ast.Varargs):
                for value in self.scope.lookup("..."):
                    if value is not None:
                        # lua语法在value为None时认为该键不存在
                        tbl.insert(value)
                continue
            if isinstance(field.key, ast.Name):
                if field.between_brackets:
                    # between_brackets不一定存在
                    tbl[self.visit(field.key)] = self.visit(field.value)
                else:
                    tbl[field.key.id] = self.visit(field.value)
            else:
                k = self.visit(field.key)
                v = self.visit(field.value)
                if v is not None:
                    # lua语法在value为None时认为该键不存在
                    tbl[k] = v
        return tbl

    def visit_String(self, node: ast.String):
        return node.s

    def visit_Forin(self, node: ast.Forin):
        iter_fn = node.iter[0]
        assert isinstance(iter_fn, ast.Call), "iterator not a function"
        iter_fn_name: str = iter_fn.func.id
        iter_val = self.visit(iter_fn.args[0])
        if len(node.targets) == 2:
            k_name, v_name = node.targets[0].id, node.targets[1].id
        else:
            # 有的会只用一个参数接受对象
            k_name = node.targets[0].id
            v_name = None
        if iter_fn_name == "pairs":
            iter_ = iter(iter_val)
            for k, v in iter_:
                with self.scope.create_child_scope():
                    if v_name:
                        self.scope.variables.update({k_name: k, v_name: v})
                    else:
                        self.scope.variables.update({k_name: k})
                    try:
                        self.visit(node.body)
                    except LuaBreak:
                        break
        elif iter_fn_name == "ipairs":
            idx = 1
            while idx in iter_val:
                v = iter_val[idx]
                self.scope.variables.update({k_name: idx, v_name: v})
                try:
                    self.visit(node.body)
                except LuaBreak:
                    break
                idx += 1

    def visit_Fornum(self, node: ast.Fornum):
        var = self.scope.variables
        id_ = node.target.id
        var[id_] = self.visit(node.start)
        stop = self.visit(node.stop)
        step = self.visit(node.step)
        while stop >= var[id_]:
            with self.scope.create_child_scope():
                self.visit(node.body)
            var[id_] += step

    def visit_Block(self, node: ast.Block):
        with self.scope.create_child_scope():
            if self.first_block_scope is None:
                # 保存Chunk内的scope，方便打印调试
                self.first_block_scope = self.scope
            for stmt in node.body:
                self.visit(stmt)

    def visit_SemiColon(self, node):
        return

    def _get_qualname(self, node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Index):
            res = ".".join(map(str, reversed(self._get_index_list(node))))
            return res
        elif callable(node):
            res = node.__qualname__
            return res


def _dummy_fn(*args, **kwds):
    return None


_dummy_fn.ignore_args = True


class ConstantsInterpreter(Interpreter):
    IGNORE_FUNCS = ("rawget",)
    IGNORE_NAMES = ("FE_MUSIC",)


class TuningInterpreter(Interpreter):
    def __init__(self):
        super().__init__()
        # 只关心TUNING的定义，忽略上下文
        self.ignore = True

    def visit(self, node):
        node_name = type(node).__name__
        if self.ignore and node_name not in ("Chunk", "Block"):
            if node_name == "Assign" and (
                node.targets and node.targets[0].id == "TUNING"
            ):
                self.ignore = False
                return super().visit(node)
        else:
            return super().visit(node)

    def visit_Assign(self, node):
        super().visit_Assign(node)
        if node.targets and node.targets[0].id == "TUNING":
            self.ignore = True


class PrefabInterpreter(Interpreter):
    IGNORE_FUNCS = {
        "AddDefaultRippleSymbols",
        "bit",
        "CreateBoxEmitter",
        "CreateDiscEmitter",
        "CreateCircleEmitter",
        "GetIdealUnsignedNetVarForCount",
        "IsRestrictedCharacter",
        "MakeSmallBurnable",
        "MakeMediumBurnable",
        "MakePlacer",
        # "MakeInventoryFloatable",
        "MakeSmallPropagator",
        "MakeMediumPropagator",
        "MakeSnowCovered",
        "MakeObstaclePhysics",
        "MakeWaterObstaclePhysics",
        "MakeSmallObstaclePhysics",
        "MakeHeavyObstaclePhysics",
        "MakeGhostPhysics",
        "MakeProjectilePhysics",
        "MakeTinyFlyingCharacterPhysics",
        "MakeFlyingCharacterPhysics",
        "MakeGiantCharacterPhysics",
        "MakeFlyingGiantCharacterPhysics",
        "MakeTinyGhostPhysics",
        "MakePondPhysics",
        "MakeSmallHeavyObstaclePhysics",
        "MakeSnowCoveredPristine",
        "MakeSmallPerishableCreaturePristine",
        "MakeFeedableSmallLivestockPristine",
        "MakeDeployableFertilizerPristine",
        "net_smallbyte",
        "net_event",
        # "net_tinybyte",
        # "net_bool",
        # "net_float",
        "net_entity",
        "net_byte",
        "net_shortint",
        "net_string",
        "net_hash",
        "net_ushortint",
        "net_uint",
        "RemovePhysicsColliders",
        "rawget",
        "setmetatable",
        "SeasonalSpawningChanges",
        "SetDesiredMaxTakeCountFunction",
        "TintByOceanTile",
    }
    IGNORE_NAMES = {
        "brain",
        "LanguageTranslator",
        "deepcopy",
        "RiftConfirmScreen",
        "STRINGS",
    }
