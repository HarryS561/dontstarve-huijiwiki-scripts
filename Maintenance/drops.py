import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import *

results = []
for page in tqdm(get_pages(category='联机版', template='实体信息框')):
    text = page.text()
    code = parse(text)
    templates = code.filter_templates()
    for i, tpl in enumerate(templates):
        if "实体信息框" in tpl.name.strip():
            if tpl.has("掉落"):
                original = tpl.get("掉落").value.strip()
                
                if "实体信息框/自动" in tpl.name.strip():
                    if tpl.has("2"):
                        code = tpl.get("2").value.strip()
                    else:
                        code = tpl.get("代码").value.strip()

                results.append({
                    "page": page.name,
                    "infobox_index": i,
                    "drop_param_original": original,
                    "drop_param_current": original
                })
with open("Maintenance/drops.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=4)
print(f"共收集到 {len(results)} 条掉落信息，已写入 drops.json")

# with_zh = set()
# with_code = set()
# with_none = set()
# for page in tqdm(get_pages(category='联机版', template='实体信息框/自动')):
#     text = page.text()
#     code = parse(text)
#     templates = code.filter_templates()
#     for i, tpl in enumerate(templates):
#         if "实体信息框/自动" in tpl.name.strip():
#             if tpl.has("2"):
#                 continue
#             if tpl.has("代码"):
#                 with_code.add(page.name)
#             elif tpl.has("中文名"):
#                 with_zh.add(page.name)
#             else:
#                 with_none.add(page.name)
# print('with_zh: ' + ' '.join(with_zh))
# print('with_code: ' + ' '.join(with_code))
# print('with_none: ' + ' '.join(with_none))