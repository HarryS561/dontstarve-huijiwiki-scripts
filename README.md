# 使用
在 `config.json` 中填入：
* 《饥荒：联机版》和《饥荒》的本地文件夹
* 灰机维基的机器人用户名、密码和机器人操作所需的 header（在 QQ 群里有）
* Steam 的用户名和密码（仅在更新 Prefab History 时需要）

# 开发
出于复用代码考虑，每个脚本前将根目录加入 `sys.path`，然后导入 `main.py`
`
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import *
`

# 项目结构

文件名|注释
---|---
`config.json`|配置文件，运行前请修改
`main.py`|通用操作封装
`dst-mod-tool.exe`|一个动画、贴图工具
`drops/*`|实体信息框的掉落参数规范化
`DST Prefab/*`|实体信息框/自动所需的实体数据更新
`dst生物群系/*`|生物群系数据更新
`Prefab History/*`|生物群系数据更新
`Skins/*`|皮肤tabx数据更新
`Skins Icons/*`|皮肤图片更新
`Strings/*`|文本数据更新

# 待办事项
* 掉落
* tabx操作封装

# 特别致谢
* Jerry 的命令行贴图工具
* Arough 的单机版生物群系数据更新脚本
* Depot Downloader.exe (github.com/SteamRE/DepotDownloader)