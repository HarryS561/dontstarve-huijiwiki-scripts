# Claude AI 维基编辑工作流

> AI 辅助编辑饥荒维基的工具使用指南

---

## 工作流程

```
任务开始 → 需要参考？→ 抓取页面 → 阅读资料 → 编写内容 → 检查验证 → 提交
         ↓ 否
         直接编写 ────────────────────┘
```

---

## 核心工具

### wiki_fetcher.py - 页面抓取工具
**路径：** `Agent/wiki_fetcher.py`

**基本用法：**
```bash
# 抓取默认高质量示例
python Agent/wiki_fetcher.py

# 指定页面
python Agent/wiki_fetcher.py "页面1" "页面2"

# 按模板抓取
python Agent/wiki_fetcher.py --template "模板名" --limit 5

# 按分类抓取
python Agent/wiki_fetcher.py --category "分类名" --limit 5

# 搜索/列表
python Agent/wiki_fetcher.py --search "关键词"
python Agent/wiki_fetcher.py --list
```

**输出：** `Agent/fetched_content.json` - 页面源代码 + 元数据

### STYLE.md - 编写规范
**路径：** `Agent/STYLE.md`

**关键章节：**
- 第 2 节：页面结构（代码块顺序、摘要格式）
- 第 3 节：用词术语（固定术语表、数值表示）
- 第 5 节：模板使用（信息框、常用模板）
- 第 7 节：页面模板（角色/物品/生物/建筑）
- 第 11 节：检查清单（编写完成后必查）

---

## 何时抓取资料

### ✅ 需要抓取
1. **不熟悉模板** - 不知道参数如何填写
2. **需要示例** - 参考同类页面结构
3. **不确定术语** - 查看标准表述方式
4. **学习结构** - 了解章节组织方式

### ❌ 不需要抓取
1. **基础编写** - 按 STYLE.md 常规操作
2. **数据更新** - 使用自动化脚本
3. **简单修改** - 错别字、数值、链接

---

## 完整编辑流程

### 场景：创建新角色页面

**步骤 1：抓取参考**
```bash
python Agent/wiki_fetcher.py "薇克巴顿" "温蒂" "威尔逊"
```

**步骤 2：阅读资料**
- 打开 `Agent/fetched_content.json`
- 观察：代码块顺序、摘要写法、章节组织、信息框参数

**步骤 3：参考模板编写**
- 参考 STYLE.md 第 7.1 节角色页面模板
- 结合 fetched_content.json 实际示例

**步骤 4：检查清单验证**
- 使用 STYLE.md 第 11 节检查清单
- 逐项验证：译名、格式、术语、模板、标点

**步骤 5：提交**

---

## 常见场景

### 场景 1：不确定信息框用法
```bash
python Agent/wiki_fetcher.py "拆解魔杖" "建造护符"
# 查看 {{实体信息框/自动}} 的实际用法
```

### 场景 2：不确定章节结构
```bash
python Agent/wiki_fetcher.py "寄居蟹隐士"
# 学习复杂 NPC 页面的章节组织
```

### 场景 3：不确定术语表述
```bash
python Agent/wiki_fetcher.py --search "距离单位"
# 或抓取 "帮助:编写规范"
```

### 场景 4：学习折叠模板
```bash
python Agent/wiki_fetcher.py "寄居蟹隐士"
# 查看 {{HuijiCollapsed}} 的使用方式
```

### 场景 5：展示制作材料
```bash
python Agent/wiki_fetcher.py "拆解魔杖"
# 学习 {{InventoryNew}} 模板的参数格式
```

---

## AI 编写规范要点

### 摘要格式
```mediawiki
'''中文名（{{en|英文名}}）'''是[[饥荒：联机版]]{{DST}}中的一种[[类型]]，[获取方式]。
```

### 代码块顺序
1. 醒目信息 → 2. 置顶导航 → 3. 消歧义 → 4. 信息框 → 5. 台词 → 6. 摘要 → 7. 正文 → 8. 脚注 → 9. 导航框 → 10. 分类

### 关键术语
| 正确 ✅ | 错误 ❌ |
|---------|---------|
| 制作 | 制造、合成 |
| 生成 | 产生、出现 |
| 掉落 | 生成（lootdropper） |
| 概率 | 几率 |
| 死亡 | 被击败 |
| 击杀 | （指凶手） |
| 玩家/角色 | 你 |
| {{解释\|距离单位}} | 地皮、地皮长度 |

### 数值格式
```mediawiki
✅ 需要 1 个石头和 1 个树枝
✅ 造成 20 点物理伤害
✅ 回复 30 {{生命值}}（属性模板前无"点"）
✅ 持续 1.5 天
✅ 距离 3 {{解释|距离单位}}
❌ 需要石头和树枝（缺数量）
❌ 造成 20 物理伤害（缺"点"）
❌ 回复 30 点{{生命值}}（多了"点"）
```

### 标点符号
- 使用全角：，。、；：？！
- 句尾句号（专有名词除外）
- 人名间隔：· 不用 •
- 游戏名不用书名号：饥荒：联机版 ✅
- 版本名用双引号："她卖贝壳" ✅
- 区间用半角波浪号：3.6 ~ 4.8 ✅

### 常用模板
```mediawiki
{{实体信息框/自动|dst|code}}
{{角色信息框|参数...}}
{{Pic|32|image.png}}
{{en|English Name}}
{{DST}}
{{解释|距离单位}}
{{tooltip|显示|提示}}
{{待补充}}
{{InventoryNew|item1,item2|count=1,2|size=48}}
{{HuijiCollapsed|title=标题|ID=id|text=内容}}
```

---

## 检查清单（编写后必查）

### 内容
- [ ] 使用官方中文译名
- [ ] 摘要格式：粗体中文名 + {{en}} + 类型 + 获取方式
- [ ] 每章节首次出现的词条加链接
- [ ] 描述"具有"而非"不具有"（除特例）

### 格式
- [ ] 数值格式正确：`X 个物品`、`X 点伤害`、`X {{属性}}`
- [ ] 标点全角、句尾句号、数字与中文有空格
- [ ] 时间格式：`X 天/分钟/秒`（不用"半天"）
- [ ] 术语正确：制作/生成/掉落/概率/玩家/角色

### 模板
- [ ] 信息框参数完整
- [ ] 图片使用 {{Pic|32|...}}
- [ ] 英文名使用 {{en|...}}
- [ ] 章节使用 =={{标题|...}}==

### 结构
- [ ] 代码块顺序正确
- [ ] 添加脚注章节（如有引用）
- [ ] 添加导航框
- [ ] 添加分类标签

---

## 推荐抓取页面

### 首次使用（抓取默认集）
```bash
python Agent/wiki_fetcher.py
```

**包含：**
- 规范：帮助:编写规范、帮助:译名表
- 角色：薇克巴顿、温蒂
- 物品：拆解魔杖、建造护符
- NPC：寄居蟹隐士、蜘蛛战士
- 模板：实体信息框/自动、角色信息框、Pic

### 按需抓取
```bash
# 角色页面
python Agent/wiki_fetcher.py --category "角色" --limit 3

# 物品页面
python Agent/wiki_fetcher.py "拆解魔杖" "冰魔杖" "建造护符"

# 模板示例
python Agent/wiki_fetcher.py --template "角色信息框" --limit 5
```

---

## 快速命令

```bash
# 抓取
python Agent/wiki_fetcher.py                              # 默认页面
python Agent/wiki_fetcher.py "页面1" "页面2"              # 指定页面
python Agent/wiki_fetcher.py --template "模板" --limit 5  # 按模板
python Agent/wiki_fetcher.py --category "分类" --limit 5  # 按分类

# 查询
python Agent/wiki_fetcher.py --list                       # 列表
python Agent/wiki_fetcher.py --search "关键词"            # 搜索
```

---

## 故障排除

| 问题 | 解决方案 |
|------|----------|
| 页面不存在 | 检查拼写、在维基搜索确认 |
| 认证失败 | 检查 config.json 认证信息 |
| 文件过大 | 删除旧内容重新抓取 |
| 搜索无结果 | 抓取更多页面、尝试不同关键词 |
| 模板不明 | 抓取模板说明页或更多示例对比 |

---

**版本：** v2.0 (Compact)
**更新：** 2026-01-29
