from typing import Optional, Any, Dict
from operator import (
    add,
    sub,
    mul,
    truediv,
    floordiv,
    mod,
    pow,
    neg,
    lt,
    gt,
    le,
    ge,
    eq,
    ne,
)

from luaparser import astnodes

from exceptions import ReturnValue, IdentifierNotFound
from lua_core import LuaTable


def register_visit(name: str):
    """Decorator to register a visit handler under an explicit display_name.

    Usage (future-proof):
        @register_visit('MyNode')
        def visit_MyNode(self, node):
            ...
    """

    def _decorator(func):
        setattr(func, "_visit_name", name)
        return func

    return _decorator


class LuaParser:
    def __init__(self, builtins: Optional[Dict[str, Any]] = None):
        # avoid mutable default
        if builtins is None:
            builtins = {}
        self.scope = Scope(self)
        self.scope.update(builtins)
        # scope_stack 用于处理闭包, 仅在函数调用前入新栈, 函数调用后出栈
        self.scope_stack = []
        # 一个lua模块的全局变量
        self.globals: None | Scope = None
        # 用于函数返回值传递
        self.return_value = None
        # cache for visit dispatch methods
        self._visit_cache = {}
        # preload existing visit_* methods into cache for faster dispatch
        for attr in dir(self):
            if attr.startswith("visit_") and attr != "visit":
                method = getattr(self, attr)
                display = attr[len("visit_") :]
                # if the underlying function was decorated with register_visit,
                # prefer its explicit name
                func = getattr(method, "__func__", method)
                explicit = getattr(func, "_visit_name", None)
                key = explicit or display
                self._visit_cache[key] = method

    def get_value(self, name: str):
        return self.scope.get_value(name)

    def get_logical_value(self, node: astnodes.Expression):
        return not (self.visit(node) in (False, None))

    def visit(self, node: astnodes.Node) -> Any:
        """Dispatch to visit_<NodeDisplayName> with caching.

        Raises a clear error when node type or handler is unexpected.
        """
        if not isinstance(node, astnodes.Node):
            if isinstance(node, int):
                return node
            else:
                raise TypeError(
                    "Expected astnodes.Node, got %r: %r" % (type(node), node)
                )

        name = node.display_name
        method = self._visit_cache.get(name)
        if method is None:
            method = getattr(self, f"visit_{name}", None)
            if method is None:
                # fallback to generic handler that raises a clear exception
                method = self.generic_visit
            self._visit_cache[name] = method

        return method(node)

    def generic_visit(self, node: astnodes.Node) -> Any:
        """Fallback when a specific visit_ handler is not implemented."""
        name = getattr(node, "display_name", repr(type(node)))
        raise NotImplementedError("No visit handler for node type: " + name)

    # helper for binary ops to reduce duplication in visit_* methods
    def _binary_op(self, node: astnodes.BinaryOp, op):
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(left, str) and isinstance(right, int):
            # "abc" .. 123 -> "abc123"
            right = str(right)
        return op(left, right)

    def _unary_op(self, node: astnodes.UnaryOp, op):
        """Helper for unary ops like unary minus."""
        val = self.visit(node.operand)
        return op(val)

    def visit_Chunk(self, node: astnodes.Chunk):
        block = node.body  # always a Block
        return self.visit(block)

    def visit_Block(self, node: astnodes.Block):
        with Scope(self, self.scope):
            for stmt in node.body:
                self.visit(stmt)

    def visit_LocalAssign(self, node: astnodes.LocalAssign):
        # 未考虑左值和右值中"..."的情况
        targets = node.targets  # always Name?
        values = node.values
        # evaluate all RHS first to support multi-return expansion
        evaluated = [self.visit(v) for v in values]
        # if last value is a tuple (multi-return), expand it
        if evaluated and isinstance(evaluated[-1], tuple):
            last = list(evaluated[-1])
            evaluated = evaluated[:-1] + last
        for idx, target in enumerate(targets):
            name = target.id
            val = evaluated[idx] if idx < len(evaluated) else None
            self.scope[name] = val

    def visit_Assign(self, node: astnodes.Assign):
        targets = node.targets
        values = node.values
        # evaluate all RHS first to support multi-return expansion
        evaluated = [self.visit(v) for v in values]
        if evaluated and isinstance(evaluated[-1], tuple):
            evaluated = evaluated[:-1] + list(evaluated[-1])

        for idx, target in enumerate(targets):
            value = evaluated[idx] if idx < len(evaluated) else None
            if isinstance(target, astnodes.Index):
                # lua table元素的赋值
                if target.notation == astnodes.IndexNotation.DOT:
                    # dot方式访问必定是Name 直接访问id
                    self.visit(target.value)[target.idx.id] = value
                elif target.notation == astnodes.IndexNotation.SQUARE:
                    self.visit(target.value)[self.visit(target.idx)] = value
            elif isinstance(target, astnodes.Name):
                name = target.id
                try:
                    scope = self.scope.get_scope_by_name(name)
                    # 修改变量值
                    scope[name] = value
                except IdentifierNotFound:
                    # 定义新变量
                    self.scope.top_scope[name] = value
            else:
                raise Exception("Unexpected target type: {}", type(target))

    def visit_Table(self, node: astnodes.Table):
        # list or dict 先尝试总是dict
        table = LuaTable()
        for field in node.fields:
            if isinstance(field.key, astnodes.Number):
                k = self.visit(field.key)
            elif isinstance(field.key, astnodes.Name):
                k = field.key.id
            else:
                raise Exception(
                    "Unexpected field key type {}", type(field.key)
                )
            v = self.visit(field.value)
            table[k] = v
        return table

    def visit_Number(self, node: astnodes.Number):
        return node.n

    def visit_String(self, node: astnodes.String):
        # delimiter是否影响解析?
        return node.s

    def visit_AddOp(self, node: astnodes.AddOp):
        return self._binary_op(node, add)

    def visit_SubOp(self, node: astnodes.SubOp):
        return self._binary_op(node, sub)

    def visit_MultOp(self, node: astnodes.MultOp):
        return self._binary_op(node, mul)

    def visit_FloatDivOp(self, node: astnodes.FloatDivOp):
        return self._binary_op(node, truediv)

    def visit_FloorDivOp(self, node: astnodes.FloorDivOp):
        return self._binary_op(node, floordiv)

    def visit_ModOp(self, node: astnodes.ModOp):
        return self._binary_op(node, mod)

    def visit_ExpoOp(self, node: astnodes.ExpoOp):
        return self._binary_op(node, pow)

    def visit_RLtOp(self, node: astnodes.LessThanOp):
        return self._binary_op(node, lt)

    def visit_RGtOp(self, node: astnodes.GreaterThanOp):
        return self._binary_op(node, gt)

    def visit_RLtEqOp(self, node: astnodes.LessOrEqThanOp):
        return self._binary_op(node, le)

    def visit_RGtEqOp(self, node: astnodes.GreaterOrEqThanOp):
        return self._binary_op(node, ge)

    def visit_REqOp(self, node: astnodes.EqToOp):
        # Lua 有没有NaN的情况?
        return self._binary_op(node, eq)

    def visit_RNotEqOp(self, node: astnodes.NotEqToOp):
        return self._binary_op(node, ne)

    def visit_LAndOp(self, node: astnodes.AndLoOp):
        return (
            False
            if not self.get_logical_value(node.left)
            else self.visit(node.right)
        )

    def visit_LOrOp(self, node: astnodes.OrLoOp):
        return (
            self.visit(node.left)
            if self.get_logical_value(node.left)
            else self.visit(node.right)
        )

    def visit_Concat(self, node: astnodes.Concat):
        return self._binary_op(node, add)

    def visit_UMinusOp(self, node: astnodes.UMinusOp):
        return self._unary_op(node, neg)

    def visit_ULNotOp(self, node: astnodes.ULNotOp):
        # Lua's logical not: true when operand is falsey
        # (False or None)
        return self._unary_op(node, lambda v: v in (False, None))

    def visit_Call(self, node: astnodes.Call):
        callable_ = self.visit(node.func)
        # 未考虑参数收集和参数展开

        if isinstance(callable_, astnodes.LocalFunction) or isinstance(
            callable_, astnodes.Function
        ):
            return self.lua_call(callable_, node)
        else:
            return self.python_call(callable_, node)

    def lua_call(self, func_node, node):
        parameters = func_node.args
        with Scope(self, func_node.scope, enclosure=True):
            for idx, arg in enumerate(node.args):
                param = parameters[idx].id
                self.scope[param] = self.visit(arg)
            self.visit(func_node.body)
        result = self.return_value
        self.return_value = None
        return result

    def python_call(self, callable_, node):
        args = tuple(map(self.visit, node.args))
        return callable_(*args)

    def function_def(self, node):
        # 保留当前scope栈,以处理闭包的情况
        node.scope = self.scope
        return node

    def visit_LocalFunction(self, node: astnodes.LocalFunction):
        fn_name = node.name.id
        # 保留完整函数定义 到调用时才能传递参数展开计算函数内语句
        self.scope[fn_name] = self.function_def(node)

    def visit_Function(self, node: astnodes.Function):
        fn_name = node.name.id
        # 保留完整函数定义 到调用时才能传递参数展开计算函数内语句
        self.scope.top_scope[fn_name] = self.function_def(node)

    def visit_AnonymousFunction(self, node: astnodes.AnonymousFunction):
        # 保留完整函数定义 到调用时才能传递参数展开计算函数内语句
        return self.function_def(node)

    def visit_Index(self, node: astnodes.Index):
        value = self.visit(node.value)
        if node.notation == astnodes.IndexNotation.DOT:
            # dot方式访问必定是Name 直接访问id
            # 用visit访问反而尝试将字段作为变量名解析
            return value[node.idx.id]
        elif node.notation == astnodes.IndexNotation.SQUARE:
            return value[self.visit(node.idx)]
        else:
            raise Exception(
                "not a expected Notation Type: {}", type(node.notation)
            )

    def visit_Name(self, node: astnodes.Name):
        id_ = node.id
        return self.get_value(id_)

    def visit_Invoke(self, node: astnodes.Invoke):
        source = self.visit(node.source)
        func = getattr(source, node.func.id)
        args = tuple(map(self.visit, node.args))
        return func(source, *args)

    def visit_If(self, node: astnodes.If):
        if self.get_logical_value(node.test):
            self.visit(node.body)
        else:
            if node.orelse:
                self.visit(node.orelse)

    def visit_ElseIf(self, node: astnodes.ElseIf):
        if self.get_logical_value(node.test):
            self.visit(node.body)
        else:
            if node.orelse:
                self.visit(node.orelse)

    def visit_Forin(self, node: astnodes.Forin):
        if len(node.iter) == 1:
            iterable = self.visit(node.iter[0])
        else:
            raise Exception("Unexpected iter length: {}", len(node.iter))
        with Scope(self, self.scope):
            for items in iterable:
                for idx, item in enumerate(items):
                    target = node.targets[idx]
                    self.scope[target.id] = item
                self.visit(node.body)

    def visit_Fornum(self, node: astnodes.Fornum):
        # numeric for: for var = start, stop, step do ... end
        id_ = node.target.id
        # initialize iteration variable in current scope
        self.scope[id_] = self.visit(node.start)
        stop = self.visit(node.stop)
        # step may be optional; default to 1
        step = self.visit(node.step) if getattr(node, "step", None) else 1
        # choose comparison based on sign of step
        if step >= 0:

            def cond(v):
                return v <= stop

        else:

            def cond(v):
                return v >= stop

        while cond(self.scope[id_]):
            with Scope(self, self.scope):
                self.visit(node.body)
            self.scope[id_] = self.scope[id_] + step

    def visit_Return(self, node: astnodes.Return):
        # 支持多返回值：如果返回多个表达式，将其包装为 tuple
        if not node.values:
            self.return_value = None
        elif len(node.values) == 1:
            self.return_value = self.visit(node.values[0])
        else:
            self.return_value = tuple(self.visit(v) for v in node.values)
        raise ReturnValue

    def visit_Nil(self, node: astnodes.Nil):
        return None

    def visit_True(self, node: astnodes.TrueExpr):
        return True

    def visit_False(self, node: astnodes.FalseExpr):
        return False

    def visit_SemiColon(self, node: astnodes.SemiColon):
        pass


class Scope(dict):
    def __init__(
        self,
        parser: LuaParser,
        parent: Optional["Scope"] = None,
        enclosure: bool = False,
    ):
        self.parser = parser
        self.parent = parent
        # 函数调用时前作用域链入栈
        self.enclosure = enclosure

    def __enter__(self):
        if self.enclosure:
            self.parser.scope_stack.append(self.parser.scope)
        self.parser.scope = self
        # 顶层scope 再上面是builtins 将该scope设置为globals
        # 实际上只是当前lua模块的本地顶级, 在这之上还有一个lua的全局
        if not self.parser.scope_stack and (
            self.parent is None or getattr(self.parent, "parent", None) is None
        ):
            self.parser.globals = self
        # print(f"Enter! level {self.depth} now")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # print(f"Exit! level {self.parent.depth} now")
        if self.enclosure:
            self.parser.scope = self.parser.scope_stack.pop()
        else:
            self.parser.scope = self.parent
        if exc_type == ReturnValue:
            return True
        return False

    def get_value(self, name: str):
        scope = self
        while scope is not None:
            # print(f"Search {name} in {scope}")
            if name in scope:
                return scope[name]
            scope = scope.parent
            # print(f"Jump to {scope}")
        else:
            self.recursive_print()
            raise IdentifierNotFound(f"Not Found identifier: {name}")

    def get_scope_by_name(self, name: str):
        scope = self
        while scope is not None:
            if name in scope:
                return scope
            scope = scope.parent
        else:
            raise IdentifierNotFound(f"Not Found identifier: {name}")

    def recursive_print(self):
        if self.parent:
            self.parent.recursive_print()

    def __repr__(self) -> str:
        try:
            keys = list(self.keys())
        except Exception:
            keys = []
        return f"<Scope depth={self.depth} keys={keys}>"

    @property
    def top_scope(self):
        scope = self
        while scope.parent is not None:
            scope = scope.parent
        return scope

    @property
    def depth(self):
        scope = self
        depth = 0
        while scope.parent is not None:
            scope = scope.parent
            depth += 1
        return depth
