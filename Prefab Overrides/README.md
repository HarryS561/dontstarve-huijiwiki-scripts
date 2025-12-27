# Prefab Overrides
本模块用于解析`scripts/prefabs/`中的所有`SetPrefabNameOverride`定义的映射关系，然后上传到维基`模块:ItemTable/PrefabOverrides`。

## 使用

1. 按照根目录下的README.md中的步骤配置好环境、账号信息和游戏目录。
2. 切换工作目录到`Prefab Overrides`目录下，
3. 执行run.py文件

正常情况下会运行若干分钟，输出的一部分会类似于:

```
...
visiting moon_altar.lua
visiting wagdrone_flying.lua
skipping quagmire_altar_statue.lua
visiting palmconetree.lua
visiting furtuft.lua
visiting daywalker_pillar.lua
visiting winch.lua
skipping balloonparty.lua
visiting reticulearc.lua
visiting yotr_food.lua
```

当运行结束无报错，即已经上传更新。

## 反馈
使用过程中遇到问题或有建议，你可以:
1. 在[GitHub仓库](https://github.com/HarryS561/dontstarve-huijiwiki-scripts/issues)的Issues中反馈。
2. 维基编辑QQ群里联系2199。

## TODO
* 运行时根据文件数显示进度
* 结束时输出与源文件的比较，显示新增、删除和修改的映射关系。
* 在输出比较的前提下，询问用户是否确认更新。
