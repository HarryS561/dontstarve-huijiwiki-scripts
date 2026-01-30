# Agent - AI 辅助编辑工具集

本目录包含用于辅助 Claude AI 编辑饥荒维基的工具和资源。

## 📁 文件说明

### `wiki_fetcher.py` - 维基页面抓取工具 ⭐

**功能：** 从饥荒维基抓取页面的 wikitext 源代码，供 AI 参考学习。

**使用场景：**
- 不熟悉某个模板的用法
- 需要参考高质量页面的结构
- 不确定术语或概念的维基表述方式
- 需要查看特定类型页面的编写规范

**快速开始：**
```bash
# 抓取默认的高质量示例页面
python Agent/wiki_fetcher.py

# 抓取指定页面
python Agent/wiki_fetcher.py "薇克巴顿" "拆解魔杖"

# 按模板抓取页面示例
python Agent/wiki_fetcher.py --template "角色信息框" --limit 5

# 查看帮助
python Agent/wiki_fetcher.py --help
```

详细使用说明请参考 [CLAUDE.md](../CLAUDE.md)。

### `STYLE.md` - 编写风格指南 📖

**功能：** 系统化的维基编写规范，为 AI 提供可执行的标准。

**内容包括：**
- 核心原则（内容基准、语言要求、准确性原则）
- 页面结构规范（代码块顺序、摘要格式、章节组织）
- 用词与术语规范（固定术语表、数值表示、空格使用）
- 格式规范（标点符号、数字格式）
- 模板使用规范（信息框、常用模板、数据展示）
- 不同类型页面模板（角色、物品、生物、建筑）
- AI 执行检查清单
- 高质量页面特征总结

**使用方式：**
AI 在编辑维基时应该：
1. 参考 `STYLE.md` 了解规范要求
2. 使用 `wiki_fetcher.py` 抓取实际示例
3. 结合两者进行编写
4. 用检查清单（第 11 节）验证

### `fetched_content.json` - 抓取的页面内容 💾

**说明：** 由 `wiki_fetcher.py` 生成的页面内容存储文件。

**格式：**
```json
{
  "页面名": {
    "content": "页面的 wikitext 源代码...",
    "length": 12345,
    "fetched_at": "2026-01-29T18:30:00",
    "url": "https://dontstarve.huijiwiki.com/wiki/页面名"
  }
}
```

**使用方式：**
- AI 可以直接读取此文件，查看抓取的页面内容
- 包含页面元数据（长度、抓取时间、URL）
- 可以作为编写新页面时的参考

### `fetch_style_content.py` - 旧版抓取脚本 ⚠️ 已弃用

**状态：** 已被 `wiki_fetcher.py` 取代，保留用于兼容性。

**建议：** 使用新的 `wiki_fetcher.py`，功能更强大且易用。

---

## 🚀 快速上手

### 首次使用

1. 确保已安装依赖并配置 `config.json`（见主目录 `README.md`）

2. 抓取默认的高质量示例页面：
   ```bash
   python Agent/wiki_fetcher.py
   ```

3. 查看抓取的内容：
   - 打开 `Agent/fetched_content.json`
   - 或使用 `--list` 查看列表：
     ```bash
     python Agent/wiki_fetcher.py --list
     ```

4. 开始编辑维基时，参考 `STYLE.md` 和 `fetched_content.json`

### 常见使用场景

#### 场景 1: 编写新的角色页面

```bash
# 1. 抓取角色页面示例
python Agent/wiki_fetcher.py "薇克巴顿" "温蒂" "威尔逊"

# 2. 参考 STYLE.md 第 7.1 节的角色页面模板

# 3. 查看 fetched_content.json 中的实际示例

# 4. 结合两者编写新页面

# 5. 使用 STYLE.md 第 11 节的检查清单验证
```

#### 场景 2: 学习模板用法

```bash
# 抓取使用该模板的页面
python Agent/wiki_fetcher.py --template "实体信息框/自动" --limit 5

# 查看 fetched_content.json 学习参数填写方式
```

#### 场景 3: 查找术语表述

```bash
# 在已抓取内容中搜索
python Agent/wiki_fetcher.py --search "距离单位"

# 或抓取帮助页面
python Agent/wiki_fetcher.py "帮助:编写规范" "帮助:译名表"
```

---

## 📚 完整工作流

详细的 AI 编辑工作流程请参考主目录的 [CLAUDE.md](../CLAUDE.md)。

**核心流程：**

```
任务开始
  ↓
是否需要参考？
  ↓ 是
使用 wiki_fetcher.py 抓取
  ↓
阅读 fetched_content.json + STYLE.md
  ↓
编写/修改页面
  ↓
使用检查清单验证
  ↓
提交到维基
```

---

## 🛠️ 工具对比

### `wiki_fetcher.py` vs `fetch_style_content.py`

| 特性 | wiki_fetcher.py (新) | fetch_style_content.py (旧) |
|------|---------------------|----------------------------|
| 命令行参数 | ✅ 支持多种参数 | ❌ 无参数 |
| 按模板抓取 | ✅ `--template` | ❌ |
| 按分类抓取 | ✅ `--category` | ❌ |
| 搜索功能 | ✅ `--search` | ❌ |
| 列出已抓取 | ✅ `--list` | ❌ |
| 元数据 | ✅ 包含时间戳、URL | ❌ |
| 错误处理 | ✅ 详细的错误信息 | ⚠️ 简单 |
| 文档说明 | ✅ 详细的 docstring | ⚠️ 简单 |

**建议：** 使用新的 `wiki_fetcher.py`。

---

## 📝 维护说明

### 更新 STYLE.md

当维基编写规范更新时：
1. 参考最新的 `帮助:编写规范` 页面
2. 分析新的高质量页面
3. 更新 `STYLE.md` 相应章节
4. 更新文档版本号和日期

### 清理 fetched_content.json

定期清理不再需要的旧内容：
```bash
# 删除旧文件
rm Agent/fetched_content.json

# 重新抓取需要的页面
python Agent/wiki_fetcher.py
```

### 添加新的默认页面

如果发现新的高质量示例页面，可以添加到 `wiki_fetcher.py` 的 `DEFAULT_PAGES` 列表中。

---

## 🤝 贡献

如有改进建议或发现问题，请：
- 在 QQ 群中讨论
- 提交 GitHub Issue
- 创建 Pull Request

---

**最后更新：** 2026-01-29
**维护者：** Claude AI 辅助生成
