# 安装与使用

### 前置需求
* Windows 系统
* Steam 上最新版本的《饥荒：联机版》和《饥荒》游戏
* [Python](https://www.python.org/downloads/) 3.10 及以上版本
    * 依赖的第三方库在 `requirements.txt` 文件中列出
* 在[饥荒维基](dontstarve.huijiwiki.com)上具有机器人+管理员权限

### 克隆这个仓库
在命令行中：
```bash
git clone https://github.com/HarryS561/dontstarve-huijiwiki-scripts.git
cd dontstarve-huijiwiki-scripts
```

### 创建虚拟环境（非必须）
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 安装依赖
```bash
pip install -r requirements.txt
```

### 从 `config.example.json` 复制到 `config.json`
```bash
cp config.example.json config.json
```

### 在 `config.json` 中填入：
* 《饥荒：联机版》和《饥荒》的本地文件夹
* 灰机维基的机器人用户名、密码和机器人操作所需的 header（在 QQ 群里有）
* Steam 的用户名和密码（仅在更新 Prefab History 时需要）

# 开发
出于复用代码考虑，每个脚本前将根目录加入 `sys.path`，然后导入 `main.py`
```py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import *
```

# 项目结构

文件名|注释
---|---
`config.example.json`|配置文件模板，运行前请复制到 `config.json` 并修改
`requirements.txt`|脚本所依赖的 Python 第三方库
`main.py`|通用操作封装
`dst-mod-tool.exe`|一个动画、贴图工具
`Drops/*`|实体信息框的掉落参数规范化
`DST Map/*`|联机版生物群系数据更新
`Prefab/*`|实体信息框/自动所需的实体数据更新
`Prefab History/*`|实体加入版本数据更新
`Skins/*`|皮肤数据更新
`Skins Icons/*`|皮肤图片更新
`Strings/*`|文本数据更新

# 待办事项
* 掉落
* 生物群系数据
* 地块数据
* tabx操作封装

# 特别致谢
* [Jerry457](https://github.com/Jerry457) 的命令行贴图工具
* Arough 的单机版生物群系数据更新脚本
* [Depot Downloader.exe](github.com/SteamRE/DepotDownloader)
* Frto 的[以撒维基更新脚本](github.com/frto027/isaac-huiji-scripts)