import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import *

VER = "DST"  # 如果是单机版改成DS

itemtable = "Data:ItemTable.tabx" if VER == "DST" else "Data:DSItemTable.tabx"

if VER == "DST":
    SCRIPTS_PATH = dst_path / "data/databundles/scripts.zip"
    CHINESE_S_PATH = 'scripts/languages/chinese_s.po'
    with ZipFile(SCRIPTS_PATH, 'r') as scripts_zip:
        scripts_zip.extract(CHINESE_S_PATH, 'temp')
    CHINESE_S_PATH = "temp/" + CHINESE_S_PATH
    with open(dst_path / "version.txt") as f:
        ver = f.read().strip()
else:
    CHINESE_S_PATH = ds_path / "data/scripts/languages/chinese_s.po"
po = polib.pofile(CHINESE_S_PATH)


def process_fields(indices: list):
    fields = []
    for idx in indices:
        fields.append({
            "name": idx,
            "type": "string",
            "title": {
                "en": idx,
                "zh": ""
            }
        })
    return fields


def read_itemtable():
    pagedata = json.loads(site.pages[itemtable].text())
    for i, field in enumerate(pagedata['schema']['fields']):
        if field['name'] == 'id':
            id_idx = i
        if field['name'] == 'item_img1' or field['name'] == 'img':
            img_idx = i
    return {line[id_idx]: line[img_idx] for line in pagedata['data']}


def lua_escape(s: str) -> str:
    return (s or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")


def dump_lua_table(bucket_map: dict) -> str:
    lines = ["return {"]
    for key in sorted(bucket_map.keys()):
        v = bucket_map[key]
        if isinstance(v, dict):  # CHARACTERS
            lines.append(f'  ["{lua_escape(key)}"] = {{')
            for character in sorted(v.keys()):
                rv = v[character]
                lines.append(f'    ["{character}"] = "{lua_escape(rv)}",')
            lines.append("  },")
        else:  # 非 CHARACTERS
            lines.append(f'  ["{lua_escape(key)}"] = "{lua_escape(v)}",')
    lines.append("}")
    return "\n".join(lines)


def create_buckets(code_map):
    keys = list(code_map.keys())
    keys.sort()
    total = len(keys)
    bucket_size = (total + 99) // 100

    bucket_map = {}
    for i, key in enumerate(keys):
        bucket_index = i // bucket_size
        bucket_name = f"{bucket_index:02d}"  # 00 ~ 99
        bucket_map[key] = bucket_name

    buckets = {}
    for key, val in code_map.items():
        b = bucket_map[key]
        m = buckets.get(b)
        if m is None:
            m = {}
            buckets[b] = m
        m[key] = val

    return buckets


id_to_img = read_itemtable()
new_itemtable = []

# 去掉 STRINGS. 前缀；
# CHARACTERS.* 去掉角色段并聚合为 character->{cn,en}；
# 其它为 {cn,en}
code_map_cn = {}  # key(无STRINGS.) -> dict(character->cn) | cn
code_map_en = {}  # key(无STRINGS.) -> dict(character->en) | en

for entry in po:
    if not entry.msgctxt or entry.msgstr is None or entry.msgid is None:
        continue
    parts = entry.msgctxt.upper().split(".")
    if len(parts) < 2 or parts[0] != "STRINGS":
        continue

    cn = entry.msgstr
    en = entry.msgid

    if parts[1] == 'NAMES':
        # tabx 不允许空白符
        cn = cn.strip().replace('\n', '\\n').replace('\t', '')
        en = en.strip().replace('\n', '\\n').replace('\t', '')
        id = parts[2].lower()
        img = id_to_img[id] if id in id_to_img else f'{en}.png'
        new_itemtable.append([id, cn, en, img])

    elif parts[1] == "CHARACTERS" and len(parts) >= 4:
        character = parts[2].lower()
        if character == "generic":
            character = "wilson"
        norm_key = ".".join(["CHARACTERS"] + parts[3:])  # 去掉 STRINGS. 与 角色段
        d_cn = code_map_cn.get(norm_key)
        if not isinstance(d_cn, dict):
            d_cn = {}
            code_map_cn[norm_key] = d_cn
        d_cn[character] = cn
        d_en = code_map_en.get(norm_key)
        if not isinstance(d_en, dict):
            d_en = {}
            code_map_en[norm_key] = d_en
        d_en[character] = en
    else:
        norm_key = ".".join(parts[1:])  # 去掉 STRINGS.
        code_map_cn[norm_key] = cn
        code_map_en[norm_key] = en

# 分桶并写入：Module:{VER} Strings CN/EN <bucket>
buckets_cn = create_buckets(code_map_cn)
buckets_en = create_buckets(code_map_en)

for b in tqdm(sorted(buckets_cn.keys())):
    module_name = f"Module:{VER} Strings CN {b.lower()}"
    lua_src = dump_lua_table(buckets_cn[b])
    site.pages[module_name].save(
        lua_src, summary=f"Extract data from patch {ver}" if VER == "DST" else '')

for b in tqdm(sorted(buckets_en.keys())):
    module_name = f"Module:{VER} Strings EN {b.lower()}"
    lua_src = dump_lua_table(buckets_en[b])
    site.pages[module_name].save(
        lua_src, summary=f"Extract data from patch {ver}" if VER == "DST" else '')


pagedata = json.dumps({
    "sources": f"Extract data from patch {ver}" if VER == "DST" else '',
    'schema': {
        'fields': process_fields(['id', 'name_cn', 'name_en', 'item_img1' if VER == "DST" else 'img']),
    },
    'data': new_itemtable,
}, indent=4, ensure_ascii=False)
site.pages[itemtable].save(pagedata)

exist = {page.name for page in site.allpages()}
need = {line[0]: f"<tr><td>{line[0]}</td><td>[[{line[1]}]]</td></tr>" for line in tqdm(
    new_itemtable) if not line[1] in exist and not '{' in line[1] and not r'%s' in line[1] and not r'\n' in line[1]}
pagetext = f"""\
从 chinese_s.po 的 STRING.NAMES 中自动提取的全部缺失页面，可能含有废弃的prefab及其翻译（例如：anchor_sketch）
<table class="wikitable sortable mw-collapsible mw-collapsed">
<tr><th>prefab</th><th>页面</th></tr>
{"".join([need[id] for id in sorted(need.keys()) if "quagmire" not in id])}
</table>
"""
if VER == "DST":
    pagetext += f"""\
<table class="wikitable sortable mw-collapsible mw-collapsed">
<tr><th>暴食prefab</th><th>页面</th></tr>
{"".join([need[id] for id in sorted(need.keys()) if "quagmire" in id])}
</table>
"""
    shutil.rmtree('temp')
site.pages['Project:施工计划/缺失页面' if VER == "DST" else 'Project:施工计划/缺失页面/单机版'].save(pagetext)
