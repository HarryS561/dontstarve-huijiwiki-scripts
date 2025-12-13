from main import *
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

VER = "DST"
itemtable = "Data:ItemTable.tabx" if VER == "DST" else "Data:DSItemTable.tabx"

if VER == "DST":
    SCRIPTS_PATH = dst_path / "data/databundles/scripts.zip"
    CHINESE_S_PATH = "scripts/languages/chinese_s.po"
    with ZipFile(SCRIPTS_PATH, "r") as z:
        z.extract(CHINESE_S_PATH, "temp")
    CHINESE_S_PATH = "temp/" + CHINESE_S_PATH
    with open(dst_path / "version.txt") as f:
        ver = f.read().strip()
else:
    CHINESE_S_PATH = ds_path / "data/scripts/languages/chinese_s.po"
    ver = ""

po = polib.pofile(CHINESE_S_PATH)


def lua_escape(s):
    return (s or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")


def dump_lua_table(m):
    out = ["return {"]
    for k in sorted(m):
        v = m[k]
        if isinstance(v, dict):
            out.append(f'  ["{lua_escape(k)}"] = {{')
            for c in sorted(v):
                out.append(f'    ["{c}"] = "{lua_escape(v[c])}",')
            out.append("  },")
        else:
            out.append(f'  ["{lua_escape(k)}"] = "{lua_escape(v)}",')
    out.append("}")
    return "\n".join(out)


def create_buckets_and_index(code_map):
    keys = sorted(code_map)
    total = len(keys)
    size = (total + 99) // 100
    bucket_of = {}
    index = []
    for i, k in enumerate(keys):
        b = min(i // size, 99)
        bucket_of[k] = f"{b:02d}"
    seen = set()
    for k in keys:
        b = bucket_of[k]
        if b not in seen:
            seen.add(b)
            index.append({"key": k, "bucket": b})
    buckets = {}
    for k, v in code_map.items():
        buckets.setdefault(bucket_of[k], {})[k] = v
    return buckets, index


code_cn = {}
code_en = {}
new_itemtable = []
id_to_img = {}

if site.pages[itemtable].exists:
    pagedata = json.loads(site.pages[itemtable].text())
    id_idx = img_idx = 0
    for i, f in enumerate(pagedata["schema"]["fields"]):
        if f["name"] == "id":
            id_idx = i
        if f["name"] in ("item_img1", "img"):
            img_idx = i
    id_to_img = {l[id_idx]: l[img_idx] for l in pagedata["data"]}

for e in po:
    if not e.msgctxt or e.msgstr is None or e.msgid is None:
        continue
    p = e.msgctxt.upper().split(".")
    if p[0] != "STRINGS" or len(p) < 2:
        continue

    cn, en = e.msgstr, e.msgid

    if p[1] == "NAMES":
        cn2 = cn.strip().replace("\n", "\\n").replace("\t", "")
        en2 = en.strip().replace("\n", "\\n").replace("\t", "")
        pid = p[2].lower()
        img = id_to_img.get(pid, f"{en2}.png")
        new_itemtable.append([pid, cn2, en2, img])
        continue

    if p[1] == "CHARACTERS" and len(p) >= 4:
        ch = p[2].lower()
        if ch == "generic":
            ch = "wilson"
        key = ".".join(["CHARACTERS"] + p[3:])
        code_cn.setdefault(key, {})[ch] = cn
        code_en.setdefault(key, {})[ch] = en
    else:
        key = ".".join(p[1:])
        code_cn[key] = cn
        code_en[key] = en

buckets_cn, index = create_buckets_and_index(code_cn)
buckets_en, _ = create_buckets_and_index(code_en)

df = pd.DataFrame(index)
df = df.sort_values("key").reset_index(drop=True)
pagedata = json.dumps({
    "data": json.loads(df.to_json(orient="records", force_ascii=False))
}, ensure_ascii=False)
site.pages[f"Data:{VER} Strings Index.json"].save(
    pagedata,
    summary=f"Extract data from patch {ver}" if VER == "DST" else ""
)

for b in sorted(buckets_cn):
    site.pages[f"Module:{VER} Strings CN {b}"].save(
        dump_lua_table(buckets_cn[b]),
        summary=f"Extract data from patch {ver}" if VER == "DST" else ""
    )

for b in sorted(buckets_en):
    site.pages[f"Module:{VER} Strings EN {b}"].save(
        dump_lua_table(buckets_en[b]),
        summary=f"Extract data from patch {ver}" if VER == "DST" else ""
    )


pagedata = json.dumps({
    "sources": f"Extract data from patch {ver}" if VER == "DST" else "",
    "schema": {
        "fields": [
            {"name": "id", "type": "string", "title": {"en": "id", "zh": ""}},
            {"name": "name_cn", "type": "string",
                "title": {"en": "name_cn", "zh": ""}},
            {"name": "name_en", "type": "string",
                "title": {"en": "name_en", "zh": ""}},
            {"name": "item_img1" if VER == "DST" else "img", "type": "string",
             "title": {"en": "img", "zh": ""}}
        ]
    },
    "data": new_itemtable,
}, ensure_ascii=False, indent=2)

site.pages[itemtable].save(pagedata)

if VER == "DST":
    shutil.rmtree("temp")
