import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import *

VER = "DST"

itemtable = "Data:ItemTable.tabx" if VER == "DST" else "Data:DSItemTable.tabx"

if VER == "DST":
    SCRIPTS_PATH = dst_path / "data/databundles/scripts.zip"
    CHINESE_S_PATH = "scripts/languages/chinese_s.po"
    with ZipFile(SCRIPTS_PATH, "r") as scripts_zip:
        scripts_zip.extract(CHINESE_S_PATH, "temp")
    CHINESE_S_PATH = "temp/" + CHINESE_S_PATH
    with open(dst_path / "version.txt") as f:
        ver = f.read().strip()
else:
    CHINESE_S_PATH = ds_path / "data/scripts/languages/chinese_s.po"
    ver = ""
po = polib.pofile(CHINESE_S_PATH)


def process_fields(indices: list):
    return [{
        "name": idx,
        "type": "string",
        "title": {"en": idx, "zh": ""}
    } for idx in indices]


def read_itemtable():
    pagedata = json.loads(site.pages[itemtable].text())
    id_idx = 0
    img_idx = 0
    for i, field in enumerate(pagedata["schema"]["fields"]):
        if field["name"] == "id":
            id_idx = i
        if field["name"] == "item_img1" or field["name"] == "img":
            img_idx = i
    return {line[id_idx]: line[img_idx] for line in pagedata["data"]}


def lua_escape(s: str) -> str:
    return (s or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")


def dump_lua_table(bucket_map: dict) -> str:
    lines = ["return {"]
    for key in sorted(bucket_map.keys()):
        v = bucket_map[key]
        if isinstance(v, dict) and ("cn" in v or "en" in v):
            lines.append(f'  ["{lua_escape(key)}"] = {{ cn = "{lua_escape(v.get("cn",""))}", en = "{lua_escape(v.get("en",""))}" }},')
        elif isinstance(v, dict):
            lines.append(f'  ["{lua_escape(key)}"] = {{')
            for character in sorted(v.keys()):
                pair = v[character] or {}
                lines.append(f'    ["{lua_escape(character)}"] = {{ cn = "{lua_escape(pair.get("cn",""))}", en = "{lua_escape(pair.get("en",""))}" }},')
            lines.append("  },")
        else:
            lines.append(f'  ["{lua_escape(key)}"] = "{lua_escape(v)}",')
    lines.append("}")
    return "\n".join(lines)


def make_bucket_map_and_index(keys: list):
    keys = sorted(keys)
    total = len(keys)
    if total == 0:
        return {}, []
    bucket_size = (total + 99) // 100
    if bucket_size <= 0:
        bucket_size = 1

    bucket_map = {}
    index = []
    for i, key in enumerate(keys):
        bucket_index = i // bucket_size
        if bucket_index > 99:
            bucket_index = 99
        bucket = f"{bucket_index:02d}"
        bucket_map[key] = bucket

    seen = set()
    for key in keys:
        b = bucket_map[key]
        if b not in seen:
            seen.add(b)
            index.append({"key": key, "bucket": b})

    return bucket_map, index


def build_buckets(code_map: dict, bucket_map: dict):
    buckets = {}
    for key, val in code_map.items():
        b = bucket_map.get(key)
        if b is None:
            continue
        m = buckets.get(b)
        if m is None:
            m = {}
            buckets[b] = m
        m[key] = val
    return buckets


id_to_img = read_itemtable()
new_itemtable = []
code_map = {}

for entry in po:
    if not entry.msgctxt or entry.msgstr is None or entry.msgid is None:
        continue
    parts = entry.msgctxt.upper().split(".")
    if len(parts) < 2 or parts[0] != "STRINGS":
        continue

    cn = entry.msgstr
    en = entry.msgid

    if parts[1] == "NAMES":
        cn = cn.strip().replace("\n", "\\n").replace("\t", "")
        en = en.strip().replace("\n", "\\n").replace("\t", "")
        id_ = parts[2].lower()
        img = id_to_img[id_] if id_ in id_to_img else f"{en}.png"
        new_itemtable.append([id_, cn, en, img])

    elif parts[1] == "CHARACTERS" and len(parts) >= 4:
        character = parts[2].lower()
        if character == "generic":
            character = "wilson"
        norm_key = ".".join(["CHARACTERS"] + parts[3:])
        d = code_map.get(norm_key)
        if not isinstance(d, dict) or ("cn" in d or "en" in d):
            d = {}
            code_map[norm_key] = d
        d[character] = {"cn": cn, "en": en}

    else:
        norm_key = ".".join(parts[1:])
        code_map[norm_key] = {"cn": cn, "en": en}

bucket_map, index = make_bucket_map_and_index(list(code_map.keys()))
buckets = build_buckets(code_map, bucket_map)

for b in tqdm(sorted(buckets.keys())):
    module_name = f"Module:{VER} Strings {b}"
    lua_src = dump_lua_table(buckets[b])
    site.pages[module_name].save(lua_src, summary=f"Extract data from patch {ver}" if VER == "DST" else "")

index_json = json.dumps(index, ensure_ascii=False, indent=2)
site.pages[f"Data:{VER}_Strings_Index.json"].save(
    index_json, summary=f"Extract data from patch {ver}" if VER == "DST" else ""
)

pagedata = json.dumps({
    "sources": f"Extract data from patch {ver}" if VER == "DST" else "",
    "schema": {
        "fields": process_fields(["id", "name_cn", "name_en", "item_img1" if VER == "DST" else "img"]),
    },
    "data": new_itemtable,
}, indent=4, ensure_ascii=False)
site.pages[itemtable].save(pagedata)

exist = {page.name for page in site.allpages()}
need = {
    line[0]: f"<tr><td>{line[0]}</td><td>[[{line[1]}]]</td></tr>"
    for line in tqdm(new_itemtable)
    if line[1] not in exist and "{" not in line[1] and r"%s" not in line[1] and r"\n" not in line[1]
}
pagetext = f"""\
从 chinese_s.po 的 STRING.NAMES 中自动提取的全部缺失页面，可能含有废弃的prefab及其翻译（例如：anchor_sketch）
<table class="wikitable sortable mw-collapsible mw-collapsed">
<tr><th>prefab</th><th>页面</th></tr>
{"".join([need[id_] for id_ in sorted(need.keys()) if "quagmire" not in id_])}
</table>
"""
if VER == "DST":
    pagetext += f"""\
<table class="wikitable sortable mw-collapsible mw-collapsed">
<tr><th>暴食prefab</th><th>页面</th></tr>
{"".join([need[id_] for id_ in sorted(need.keys()) if "quagmire" in id_])}
</table>
"""
    shutil.rmtree("temp")
site.pages["Project:施工计划/缺失页面" if VER == "DST" else "Project:施工计划/缺失页面/单机版"].save(pagetext)
