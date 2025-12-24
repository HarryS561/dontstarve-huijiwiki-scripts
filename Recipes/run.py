import os
import sys
import json
import importlib

from recipes_parser import scan_recipes
from read_po import scan_chn_po
from tabx import DSTRecipes

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
Client = importlib.import_module("main").site


def get_previous_tabx():
    raw_text = Client.pages["Data:DSTRecipes.tabx"].text()
    tabx = json.loads(raw_text)
    return tabx


def pop_tabx_from_scripts() -> dict:
    recipes = scan_recipes()
    po = scan_chn_po()
    fields = set(DSTRecipes.fields.keys())
    for name, d in recipes.items():
        item = {}
        item["recipe_name"] = name
        for idx, ingre in enumerate(d["ingredients"], 1):
            item["ingredient" + str(idx)] = ingre["prefab"]
            item["amount" + str(idx)] = ingre["amount"]
        item["tech"] = d["TECH"]
        desc_str = (
            d.get("config", {}).get("description")
            or d.get("config", {}).get("product")
            or name
        )
        desc_msgid = "STRINGS.RECIPE_DESC." + desc_str.upper()
        po_row = po.get(desc_msgid)
        if po_row:
            description = po_row["msgstr"]
        else:
            description = ""
        recipe = DSTRecipes(
            **item,
            **{k: v for k, v in d.get("config", {}).items() if k in fields},
            desc=description,
        )
        recipe.save()
    return DSTRecipes.export()


if __name__ == "__main__":
    new = pop_tabx_from_scripts()
    old = get_previous_tabx()
    old_data = old["data"]
    diffs = DSTRecipes.differ(old_data)
    print(f"新添加了{len(diffs['add'])}个配方")
    print(f"删除了{len(diffs['del'])}个配方")
    print(f"修改了{len(diffs['change'])}个配方")
    i = input("是否确认更新? (y/n)").strip()
    if i == "y":
        datas = json.dumps(new, indent=2, ensure_ascii=False)
        Client.pages["Data:DSTRecipes.tabx"].edit(datas)
