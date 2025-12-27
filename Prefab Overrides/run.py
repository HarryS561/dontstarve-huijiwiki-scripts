import os
import importlib
import json
import sys

from scan_prefabs import get_prefab_name_override, SCANNED_PREFABS


sys.path.append(os.path.dirname(os.path.dirname(__file__)))
Client = importlib.import_module("main").site


if __name__ == "__main__":
    get_prefab_name_override()
    overrides = {}
    for name, inst in sorted(SCANNED_PREFABS.items(), key=lambda x: x[0]):
        override = getattr(inst, "prefab_name_override", False)
        if override:
            overrides[name] = override
    datas = json.dumps(overrides, indent=4, ensure_ascii=False)
    content = Client.pages["模块:ItemTable/PrefabOverrides"].text()
    new_content = ""
    found_start = False
    wait_for_end = False
    for line in content.splitlines():
        if found_start is False:
            new_content += line + "\n"
            if "[[" in line:
                found_start = True
                new_content += datas + "\n"
        elif found_start is True and wait_for_end is False:
            if "]]" in line:
                wait_for_end = True
                new_content += line + "\n"
        elif wait_for_end is True:
            new_content += line + "\n"
    Client.pages["模块:ItemTable/PrefabOverrides"].save(new_content)
