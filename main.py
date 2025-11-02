from mwclient import *
from mwparserfromhell import parse
from tqdm import tqdm
import json
from pathlib import Path
from zipfile import ZipFile
import pandas as pd
from bs4 import BeautifulSoup
import polib
import shutil
from pypinyin import lazy_pinyin
import re
from hashlib import md5

with open('config.json','r') as f:
    config = json.load(f)

site = Site('dontstarve.huijiwiki.com', custom_headers={
            'X-authkey': config["huijiwiki"]["X-authkey"]})  # 编辑QQ群内有Authkey
site.login(
    username = config["huijiwiki"]["username"],  # 引号内填灰机用户名
    password = config["huijiwiki"]["password"],  # 引号内填灰机用户密码
)

dst_path = Path(config["dontstarve"]["dst_path"])
ds_path = Path(config["dontstarve"]["ds_path"])

steam_username = config["steam"]["username"]
steam_password = config["steam"]["password"]

def touch_all():
    for item in tqdm(list(site.search('创建缩略图出错'))):
        site.pages[item['title']].touch()

def get_pages(template=None, category=None):
    if template and category:
        pages_using_template = {
            p.name for p in site.pages['Template:' + template].embeddedin()}
        res = list(p for p in site.categories[category] if p.name in pages_using_template)
        return res
    elif template:
        return list(site.pages['Template:' + template].embeddedin())
    elif category:
        return list(site.categories[category])
    return []

def get_param(template, index, default=''):
    try:
        return str(template.get(index).value).strip()
    except ValueError:
        return default

def repl():
    replacements = {
        '大漩涡': '巨型漩涡',
        '遗物复制品 碗': '仿制遗物碗',
        '遗物复制品 椅子': '仿制遗物椅子',
        '遗物复制品 盘子': '仿制遗物盘子',
        '遗物复制品 碟子': '仿制遗物碟子',
        '遗物复制品 桌子': '仿制遗物桌子',
        '遗物复制品': '仿制遗物花瓶',
        '损毁的废墟': '破损遗物'
    }
    for page in tqdm(get_pages(category="联机版")):
        text = page.text()
        newtext = text
        for old, new in replacements.items():
            newtext = newtext.replace(old, new)
        if newtext != text:  # 只保存有改动的
            page.save(newtext, summary='批量替换文本')
