import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import *

SCRIPTS_PATH = dst_path / "data/databundles/scripts.zip"
paths = [
    "scripts/skin_strings.lua",
    "scripts/languages/chinese_s.po",
    "scripts/prefabs/skinprefabs.lua",
    "scripts/clothing.lua",
    "scripts/beefalo_clothing.lua",
    "scripts/emote_items.lua",
    "scripts/misc_items.lua",
    "scripts/item_blacklist.lua"
]
with ZipFile(SCRIPTS_PATH, 'r') as scripts_zip:
    for path in paths:
        scripts_zip.extract(path, 'temp')
SKIN_STRINGS_PATH, CHINESE_S_PATH, SKIN_PREFABS_PATH, CLOTHING_PATH, \
    BEEFALO_CLOTHING_PATH, EMOTE_ITEMS_PATH, MISC_ITEMS_PATH, ITEM_BLACKLIST_PATH = \
    [f"temp/{path}" for path in paths]


# id_to_name 皮肤代码名：皮肤名字（英文）
id_to_name = {}
with open(SKIN_STRINGS_PATH, "r", encoding="utf-8") as file:
    lines = file.readlines()
    start = False
    for line in lines:
        if "SKIN_NAMES" in line:
            start = True
        elif "}" in line:
            start = False
        elif start and "=" in line:
            idx = line.find("=")
            id = line[1:idx - 1].strip()
            name = line[idx + 3:-3].strip()
            id_to_name[id] = name

# id_to_name_cn 皮肤代码名：皮肤名字（中文）
id_to_name_cn = {}
with open(CHINESE_S_PATH, "r", encoding="utf-8") as file:
    lines = file.readlines()
    id = None
    for line in lines:
        if "#. STRINGS.SKIN_NAMES." in line:
            id = line.replace("#. STRINGS.SKIN_NAMES.", "").strip()
        elif id and 'msgstr "' in line:
            name_cn = line.replace('msgstr "', "").strip()[:-1].strip()
            id_to_name_cn[id] = name_cn
            id = None

# id_to_desc_cn 皮肤代码名：描述（中文）
id_to_desc_cn = {}
with open(CHINESE_S_PATH, "r", encoding="utf-8") as file:
    lines = file.readlines()
    id = None
    for line in lines:
        if "#. STRINGS.SKIN_DESCRIPTIONS." in line:
            id = line.replace("#. STRINGS.SKIN_DESCRIPTIONS.", "").strip()
        elif id and 'msgstr "' in line:
            desc_cn = line.replace('msgstr "', "").strip()[:-1].strip()
            id_to_desc_cn[id] = desc_cn
            id = None

# rarity_translation 品质代码名：品质名字（中文），以及品质前缀代码名：品质前缀名字（中文）
rarity_translation = {}
with open(CHINESE_S_PATH, "r", encoding="utf-8") as file:
    lines = file.readlines()
    rarity_en = None
    for line in lines:
        if "#. STRINGS.UI.RARITY." in line:
            rarity_en = line.replace("#. STRINGS.UI.RARITY.", "").strip()
        elif rarity_en and 'msgstr "' in line:
            rarity_ch = line.replace('msgstr "', "").strip()[:-1]
            rarity_translation[rarity_en] = rarity_ch
            rarity_en = None

# collection_translation 系列代码名：系列名字（中文）
collection_translation = {}
with open(CHINESE_S_PATH, "r", encoding="utf-8") as file:
    lines = file.readlines()
    tag = None
    for line in lines:
        if "#. STRINGS.SKIN_TAG_CATEGORIES.COLLECTION." in line:
            tag = line.replace(
                "#. STRINGS.SKIN_TAG_CATEGORIES.COLLECTION.", "").strip()
        elif tag and 'msgstr "' in line:
            tag_name_cn = line.replace('msgstr "', "").strip()[:-1]
            collection_translation[tag] = tag_name_cn
            tag = None

# id_to_type 皮肤代码名：类型，类型包括"item"（财物皮肤）、"base"（人物皮肤）、nil（都不是）
# id_to_base 皮肤代码名：物品代码名
# id_to_override 皮肤代码名：覆写皮肤代码名
# id_to_rarity 皮肤代码名：品质（中文）
# id_to_rarity_modifier 皮肤代码名：品质前缀（中文），包括"织造-"或nil
# id_to_collection 皮肤代码名：系列名字（中文）
# id_to_marketable 皮肤代码名：是否可交易（中文）
id_to_type = {}
id_to_base = {}
id_to_override = {}
id_to_rarity = {}
id_to_rarity_modifier = {}
id_to_collection = {}
id_to_marketable = {}

with open(SKIN_PREFABS_PATH, "r", encoding="utf-8") as file:
    lines = file.readlines()
    id = None
    for line in lines:
        if 'CreatePrefabSkin' in line:
            idx = line.find('CreatePrefabSkin')
            id = line[idx + 18:-3].strip()
        elif '\tbase_prefab = "' in line:
            base = line.replace('\tbase_prefab = "', "").strip()[:-2]
            id_to_base[id] = base
        elif '\ttype = "' in line:
            tp = line.replace('\ttype = "', "").strip()[:-2]
            id_to_type[id] = tp
        elif '\tbuild_name_override = "' in line:
            override = line.replace(
                '\tbuild_name_override = "', "").strip()[:-2]
            id_to_override[id] = override
        elif '\trarity = "' in line:
            rarity = line.replace('\trarity = "', "").strip()[:-2]
            id_to_rarity[id] = rarity_translation.get(rarity, "n/a")
        elif '\trarity_modifier = "' in line:
            rarity_modifier = line.replace(
                '\trarity_modifier = "', "").strip()[:-2]
            id_to_rarity_modifier[id] = rarity_translation.get(
                rarity_modifier, "n/a")
        elif '\tskin_tags = { ' in line:
            for tag in re.findall(r'"\w+"', line):
                tag = tag[1:-1]
                if collection_translation.get(tag):
                    id_to_collection[id] = collection_translation[tag]
        elif 'marketable = true,' in line:
            id_to_marketable[id] = "可交易"

# 如果皮肤B是皮肤A的granted_items，那么B不会有skin_tags，少数情况下还不会有desc_cn，这里修复了这个bug
with open(SKIN_PREFABS_PATH, "r", encoding="utf-8") as file:
    lines = file.readlines()
    id = None
    for line in lines:
        if 'CreatePrefabSkin' in line:
            idx = line.find('CreatePrefabSkin')
            id = line[idx + 18:-3].strip()
        elif '\tgranted_items = { ' in line:
            for granting in re.findall(r'"\w+"', line):
                granting = granting[1:-1]
                if id_to_collection.get(id) and not id_to_collection.get(granting):
                    id_to_collection[granting] = id_to_collection[id]
                if id_to_desc_cn.get(id) and id_to_desc_cn.get(granting) == "n/a":
                    id_to_desc_cn[granting] = id_to_desc_cn[id]

path_starts = [
    {'path': CLOTHING_PATH, 'start': "CLOTHING"},
    {'path': BEEFALO_CLOTHING_PATH, 'start': "BEEFALO_CLOTHING"},
    {'path': EMOTE_ITEMS_PATH, 'start': "EMOTE_ITEMS"},
    {'path': MISC_ITEMS_PATH, 'start': "MISC_ITEMS"},
]
for path_start in path_starts:
    with open(path_start['path'], "r", encoding="utf-8") as file:
        lines = file.readlines()
        start = False
        id = None
        for line in lines:
            if (path_start['start'] + " =") in line:
                start = True
            elif (path_start['start'] + "_SYMBOLS") in line:
                start = False
            elif start:
                temp = re.match(r'^(\w+) =$', line.strip())
                if temp and temp.group(1) != 'data':
                    id = temp.group(1)
                elif '\t\ttype = "' in line:
                    tp = line.replace('\t\ttype = "', "").strip()[:-2]
                    id_to_type[id] = tp
                elif '\t\tbuild_name_override = "' in line:
                    override = line.replace(
                        '\t\tbuild_name_override = "', "").strip()[:-2]
                    id_to_override[id] = override
                elif '\t\trarity = "' in line:
                    rarity = line.replace('\t\trarity = "', "").strip()[:-2]
                    id_to_rarity[id] = rarity_translation.get(rarity, "n/a")
                elif '\t\trarity_modifier = "' in line:
                    rarity_modifier = line.replace(
                        '\t\trarity_modifier = "', "").strip()[:-2]
                    id_to_rarity_modifier[id] = rarity_translation.get(
                        rarity_modifier, "n/a")
                elif '\t\tskin_tags = { ' in line:
                    for tag in re.findall(r'"\w+"', line):
                        tag = tag[1:-1]
                        if collection_translation.get(tag):
                            id_to_collection[id] = collection_translation[tag]
                elif 'marketable = true,' in line:
                    id_to_marketable[id] = "可交易"

id_to_blacklist = {}
# id_to_blacklist 皮肤代码名：是否为附加财物

with open(ITEM_BLACKLIST_PATH, "r", encoding="utf-8") as file:
    lines = file.readlines()
    for line in lines:
        temp = re.match(r'^(\w+) = true,$', line.strip())
        if temp:
            id_to_blacklist[temp.group(1)] = "附加财物"


def id_to_icon(id): return f"File:{id}_icon.png"  # id_to_icon 皮肤代码名：维基图片链接


# 所有的nil转为"n/a"，按id_to_override覆写缺失项
# 排序，先按物品代码名的字母表顺序，相同时按皮肤代码名的字母表顺序
skins = []
for k, v in id_to_type.items():
    s = {
        'main_category': "skin",
        'type': id_to_type.get(k, "n/a"),
        'base': id_to_base.get(k, "n/a"),
        'id': k,
        'name': id_to_name.get(k, "n/a"),
        'name_cn': id_to_name_cn.get(k, "n/a"),
        'desc_cn': id_to_desc_cn.get(k, "n/a"),
        'rarity_modifier': id_to_rarity_modifier.get(k, "n/a"),
        'rarity': id_to_rarity.get(k, "普通"),
        'collection': id_to_collection.get(k, "n/a"),
        'marketable': id_to_marketable.get(k, "n/a"),
        'blacklist': id_to_blacklist.get(k, "n/a"),
        'huijiwiki_icon': id_to_icon(k)
    }
    skins.append(s)

for s in skins:
    if id_to_override.get(s['id']):
        override_id = id_to_override[s['id']]
        if s['base'] == id_to_base.get(override_id, "n/a") or s['rarity'] == '角色':
            s['huijiwiki_icon'] = id_to_icon(override_id)
        if s['name'] == "n/a" and id_to_name.get(override_id):
            s['name'] = id_to_name[override_id]
        if s['name_cn'] == "n/a" and id_to_name_cn.get(override_id):
            s['name_cn'] = id_to_name_cn[override_id]
        if s['desc_cn'] == "n/a" and id_to_desc_cn.get(override_id):
            s['desc_cn'] = id_to_desc_cn[override_id]
        if s['collection'] == "n/a" and id_to_collection.get(override_id):
            s['collection'] = id_to_collection[override_id]

skins.sort(key=lambda s: (s['type'], s['base'], s['id']))

fields_index = ["main_category", "type", "base", "id", "name", "name_cn",
                "desc_cn", "rarity_modifier", "rarity", "collection", "marketable", "blacklist", "huijiwiki_icon"]
fields = []
for idx in fields_index:
    fields.append({
        "name": idx,
        "type": "string",
        "title": {
            "en": idx,
            "zh": ""
        }
    })
address_types = {
    'Item': ['item'],
    'Player': ["base", "body", "feet", "hand", "legs"],
    'Other': ["beard", "beef_body", "beef_feet", "beef_head", "beef_horn",
              "beef_tail", "emote", "emoji", "playerportrait", "profileflair", "loading"]
}
for address, types in tqdm(address_types.items()):
    data = []
    for s in skins:
        if s['type'] in types:
            data.append([s[i] for i in fields_index])
    pagedata = json.dumps({
        'schema': {
            'fields': fields,
        },
        'data': data,
    }, indent=4, ensure_ascii=False)
    site.pages[f"Data:DST Skins {address}.tabx"].save(pagedata)

shutil.rmtree('temp')

# 下面这段代码用于更新GSearch，可以输出全部系列
a = []
for s in skins:
    if s['collection'] not in a:
        a.append(s['collection'])
a = sorted(a, key=lambda x: lazy_pinyin(x))
for i in a:
    if i != "n/a":
        print(f"{i}-{i},", end="")
