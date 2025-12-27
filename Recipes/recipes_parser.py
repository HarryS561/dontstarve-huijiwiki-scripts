#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用luaparser库解析recipes.lua中Recipe2函数调用的参数
"""

import zipfile
from typing import Dict
import os
from contextlib import redirect_stdout

from luaparser import astnodes, ast

import constants
from lua_core.lua_types import LuaTable
from parser import LuaParser
from exceptions import MissionComplete


class LazyMarkUp:
    """延迟解析的标记"""

    def __init__(self, node: astnodes.Node):
        self.node = node


# dummy tables
class TUNING:
    EFFIGY_HEALTH_PENALTY = 40


class CHARACTER_INGREDIENT:
    HEALTH = "decrease_health"
    SANITY = "decrease_sanity"


class TECH_INGREDIENT:
    SCULPTING = "sculpting_material"


class SPELLTYPESCLASS:
    def __getattr__(self, attr):
        return attr.lower()


class RecipeParser(LuaParser):
    """解析recipes.lua中的Recipe2函数调用"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scope.update(
            TUNING=TUNING,
            CHARACTER_INGREDIENT=CHARACTER_INGREDIENT,
            TECH_INGREDIENT=TECH_INGREDIENT,
            SPELLTYPESCLASS=SPELLTYPESCLASS,
        )
        self.recipes = {}

    def _handle_recipe2(self, node: astnodes.Call):
        """处理Recipe2函数调用节点"""

        recipe = {}
        recipe["name"] = self.visit(node.args[0])
        recipe["ingredients"] = ingres = []
        ingre_table: astnodes.Table = node.args[1]
        for field in ingre_table.fields:
            ingre_prefab = self.visit(field.value.args[0])
            ingre_amount = self.visit(field.value.args[1])
            ingres.append({"prefab": ingre_prefab, "amount": ingre_amount})
        tech_node: astnodes.Index = node.args[2]
        recipe["TECH"] = f"{tech_node.value.id}.{tech_node.idx.id}"
        if len(node.args) > 3:
            config_node: astnodes.Table | None = node.args[3]
            recipe["config"] = {}
            for field in config_node.fields:
                field_name = field.key.id
                field_value = self.visit(field.value)
                if isinstance(field_value, LazyMarkUp):
                    if field_name == "override_numtogive_fn":
                        field_value = True
                    else:
                        field_value = False
                elif isinstance(field_value, LuaTable):
                    field_value = "unjsonable luatable"
                elif isinstance(field_value, astnodes.AnonymousFunction):
                    if field_name == "override_numtogive_fn":
                        field_value = True
                    else:
                        field_value = False
                recipe["config"][field_name] = field_value
        return recipe

    def visit_Call(self, node: astnodes.Call):
        """处理函数调用节点"""
        if isinstance(node.func, astnodes.Name) and node.func.id == "Recipe2":
            recipe = self._handle_recipe2(node)
            if recipe:
                self.recipes[recipe["name"]] = recipe
            else:
                print(f"Recipe2 函数调用参数解析失败: {node}")
        else:
            # 目前为止 没有别的函数需要处理
            return LazyMarkUp(node)

    def visit_Index(self, node):
        """处理索引节点"""
        value = self.visit(node.value)
        if not isinstance(value, LuaTable):
            # dummy tables返回类属性
            return getattr(value, node.idx.id)
        else:
            return super().visit_Index(node)

    def visit_LocalFunction(self, node: astnodes.LocalFunction):
        """处理局部函数定义节点"""
        # 局部函数在Recipe2中不会被调用, 所以不处理
        self.scope[node.name.id] = LazyMarkUp(node)

    def visit_Assign(self, node: astnodes.Assign):
        """处理赋值节点"""
        # 赋值语句中, 左侧是变量名, 右侧是表达式
        # 我们只需要处理右侧的表达式, 左侧的变量名会在后续的访问中处理
        target = node.targets[0]
        if (
            isinstance(target, astnodes.Name)
            and target.id == "PROTOTYPER_DEFS"
        ):
            # 文件头部的定义，不需要理会
            return
        elif (
            isinstance(target, astnodes.Index)
            and target.value.id == "PROTOTYPER_DEFS"
        ):
            # 文件头部的定义，不需要理会
            return
        elif (
            isinstance(target, astnodes.Name)
            and target.id == "CONSTRUCTION_PLANS"
        ):
            # 到这说明Recipe2已经处理完了
            raise MissionComplete
        else:
            # 其他情况, 正常处理
            return super().visit_Assign(node)


def scan_recipes() -> Dict[str, Dict]:
    """
    将 recipes.lua 中的以 "Recipe2(" 开头的配方定义转化为字典

    Returns:
        配方名称为键，值为配方的具体定义
    """
    parser = RecipeParser()

    try:
        with zipfile.ZipFile(constants.SCRIPTS_PATH) as zip_ref:
            with zip_ref.open("scripts/recipes.lua") as fp:
                content = fp.read().decode("utf-8")
                with open(os.devnull, "w") as f:
                    with redirect_stdout(f):
                        chunk = ast.parse(content)
                try:
                    parser.visit(chunk)
                except MissionComplete:
                    pass

        print(f"成功解析 {len(parser.recipes)} 个配方")
        return parser.recipes
    except Exception as e:
        print(f"读取配方文件失败: {e}")
        raise
        return {}


if __name__ == "__main__":
    print(scan_recipes())
