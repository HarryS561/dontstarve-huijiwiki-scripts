import zipfile
from typing import Optional, Dict, Any

import constants


def scan_chn_po(include_strings: bool = False) -> Dict[str, Dict[str, str]]:
    """
    扫描scripts/languages/chinese_s.po文件，获取以msgctxt为键名的一个字典。
    include_strings: 如果为True,则也包括strings.pot中的无翻译词条
    """
    res: Dict[str, Dict[str, str]] = {}
    po_list = ["strings.pot", "chinese_s.po"]
    if not include_strings:
        po_list = ["chinese_s.po"]
    # 一次打开 zip，依次读取所需文件，减少重复打开
    zip_path = constants.SCRIPTS_PATH
    with zipfile.ZipFile(str(zip_path)) as zip_ref:
        for po_name in po_list:
            _scan_po(zip_ref, po_name, res)
    return res


def _unquote(s: str) -> str:
    s = s.strip()
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1]
    return s


def _scan_po(
    zip_ref: zipfile.ZipFile, po_name: str, res: Dict[str, Dict[str, str]]
) -> None:
    """
    扫描单个 po 文件，支持 msgctxt/msgid/msgstr 的多行续行。
    将每个完整条目以 msgctxt 为键写入 res。
    """
    entry = {"msgctxt": None, "msgid": None, "msgstr": None}
    current = None  # 当前正在累积的字段名
    try:
        with zip_ref.open(f"scripts/languages/{po_name}") as po:
            for raw in po:
                try:
                    line = raw.decode("utf-8").rstrip("\n")
                except Exception:
                    continue
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if stripped.startswith("msgctxt"):
                    # 新条目开始
                    entry = {"msgctxt": None, "msgid": None, "msgstr": None}
                    value = stripped[len("msgctxt") :].strip()
                    entry["msgctxt"] = _unquote(value)
                    current = "msgctxt"
                elif stripped.startswith("msgid"):
                    value = stripped[len("msgid") :].strip()
                    entry["msgid"] = _unquote(value)
                    current = "msgid"
                elif stripped.startswith("msgstr"):
                    value = stripped[len("msgstr") :].strip()
                    entry["msgstr"] = _unquote(value)
                    # 完成一条记录（po 的 msgstr 一般表示该条目的结束）
                    if (
                        entry["msgctxt"] is not None
                        and entry["msgid"] is not None
                    ):
                        res[entry["msgctxt"]] = {
                            "msgctxt": entry["msgctxt"],
                            "msgid": entry["msgid"],
                            "msgstr": entry["msgstr"] or "",
                        }
                    entry = {"msgctxt": None, "msgid": None, "msgstr": None}
                    current = None
                elif stripped.startswith('"') and current:
                    # 续行，追加到当前字段
                    cont = _unquote(stripped)
                    if entry[current] is None:
                        entry[current] = cont
                    else:
                        entry[current] += cont
                else:
                    # 忽略其它行
                    continue
    except KeyError:
        print(f"zip 中未找到文件: scripts/languages/{po_name}")
    except Exception as e:
        print(f"解析 {po_name} 时出错: {e}")


def _add_into_map(
    mapping: Dict[str, Any], key: str, data: Dict[str, str]
) -> None:
    """
    将 data 插入 mapping，对于已有键将其转为 list 或追加到 list。
    """
    if key in mapping:
        existing = mapping[key]
        if isinstance(existing, list):
            existing.append(data)
        else:
            mapping[key] = [existing, data]
    else:
        mapping[key] = data


def get_names(
    prefab_only: bool = False, include_strings: bool = False
) -> Dict[str, Any]:
    """
    获取通过中、英、代码名都能查到对应STRINGS.NAMES项的字典
    prefab_only: 如果为True则只返回以prefab为键的字典
    include_strings: 是否包含 strings.pot 中未翻译项目
    """
    po_dict = scan_chn_po(include_strings)
    res: Dict[str, Any] = {}
    for msgctxt, data in po_dict.items():
        if not msgctxt.startswith("STRINGS.NAMES."):
            continue
        msgid = data.get("msgid", "")
        msgstr = data.get("msgstr", "")
        id_ = msgctxt.rsplit(".", 1)[-1].lower()
        # 始终添加 prefab 对应的伪键
        res[id_] = data
        if prefab_only:
            continue
        # 处理英文名（msgid）
        if msgid is not None and msgid != "":
            _add_into_map(res, msgid, data)
            if msgid == msgstr:
                print(f"中英文重名 id:{id_}, msgid:{msgid}, msgstr:{msgstr}")
                continue
            if msgstr == "":
                print(f"未翻译词条 id:{id_}, msgid:{msgid}")
                continue
        else:
            # 无英文名，跳过后续的中文名处理
            continue
        # 处理中文名（msgstr），与 msgid 相同的已被上面过滤掉
        _add_into_map(res, msgstr, data)
    return res


def get_crafting_station_filters_and_craftings(
    include_strings: bool = False,
) -> Dict[str, Dict[str, Dict[str, str]]]:
    """
    获取po中关于制作站分类和制作栏分类的译名的字典
    include_strings: True则包含strings.pot中的未翻译
    Return:
        形如 {
            "crafting_stations": {
                "ANCIENT": {
                    "station_en": "Ancient Pseudoscience",
                    "station_cn": "远古伪科学站"
                },
                ...
            },
            "craftings": {
                "ARMOUR": {
                    "staion_en": "Armor"
                    "station_cn": "护甲"
                },
                ...
            }
        }
    """
    res = {}
    crafts = res["crafting_stations"] = {}
    filters = res["craftings"] = {}
    po_dict = scan_chn_po(include_strings)
    for po in po_dict.values():
        msgctxt = po["msgctxt"]
        msgid = po["msgid"]
        msgstr = po["msgstr"]
        if msgctxt.startswith("STRINGS.UI.CRAFTING_STATION_FILTERS."):
            index = crafts
        elif msgctxt.startswith("STRINGS.UI.CRAFTING_FILTERS."):
            index = filters
        else:
            continue
        k = msgctxt.split(".")[-1]
        index[k] = {"station_en": msgid, "station_cn": msgstr}
    return res


def get_speech(
    character: Optional[str] = None, include_strings: bool = False
) -> Dict[str, Dict[str, str]]:
    """
    获取角色台词的字典

    Parameters:
    character: 指定角色的角色名(大小写不敏感)或None(所有角色).
    include_strings: True则包含strings.pot中的未翻译.

    Returns:
        形如 {
            "STRINGS.CHARACTERS.GENERIC.ACTIONFAIL.ACTIVATE.EMPTY_CATCOONDEN":
            {
                "msgctxt": ...,
                "msgid": ...,
                "msgstr": ...
            }
        }
        如果指定角色则返回该角色的台词，否则为所有角色的台词
    """
    start = "STRINGS.CHARACTERS"
    res = {}
    if character:
        if character.lower() == "wilson":
            character = "generic"
        start = start + "." + character.upper()
    for msgctxt, data in scan_chn_po(include_strings).items():
        if msgctxt.startswith(start):
            res[msgctxt] = data
            if data["msgid"] and data["msgstr"] == "":
                print(f"未翻译台词: {msgctxt}, msgid: {data['msgid']}")
    return res


if __name__ == "__main__":
    pass
