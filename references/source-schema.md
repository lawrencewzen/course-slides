# 输入源 Schema · 讲义 / 教程 / 技术文档 / 分享稿

本 skill 的装配完全基于下面这份 schema。任何 Markdown 输入（不管作者是不是按"讲义"写的）都要**先规范化成这份结构**，再进入 playground / 装配。

**核心原则**：必需字段缺失 → 让用户补；可选字段缺失 → 按"降级策略"装配，**绝不模型补**。

---

## 1. 字段定义

### Deck（顶层）

| 字段 | 必需 | 说明 | 缺失策略 |
|---|---|---|---|
| `title` | ✅ | 课程/教程标题，用作 Cover `<h1>` | 没有 → 从文件名推，例 `xxx-guide.md` → "xxx guide"；再没有 → 问用户 |
| `subtitle` | ❌ | Cover 副标题一行 | 留空，Cover 只显示主标题 |
| `date` | ❌ | 课程日期，用作 Cover 右上角 meta | 不显示这一行 |
| `duration_total` | ❌ | 总时长（分钟），用作 Cover footer "2.5h" 行 | footer 只写"单人讲完"，不报时长 |
| `sections` | ✅ | 节列表，有序；至少 1 节 | 0 节 → 让用户确认是不是给错文件了 |

### Section（每节）

| 字段 | 必需 | 说明 | 缺失策略 |
|---|---|---|---|
| `heading` | ✅ | 节标题，用作 Divider `<h1>` 和内容页面 eyebrow | 必须有 |
| `number` | ❌ | 节号（整数，从 1 起） | 按 sections 顺序自动编号 |
| `body` | ✅ | 节内正文（Markdown 原文片段），后续拆成内容页 | 必须有；全空 → 本节只出 Divider |
| `duration` | ❌ | 本节时长（分钟），用作 Divider `.pill` "⏱ N min" | **整份缺失** → 隐藏时间条 + 不生成 Break；**部分缺失** → 有的节显示时间条，没有的节省略 pill |
| `speaker_strategy` | ❌ | 讲解策略，用作 `data-notes-strategy` | **留空，不自动编** |
| `speaker_speak` | ❌ | 跟学员说（口语脚本），用作 `data-notes-speak` | **留空，不自动编** |
| `bridge` | ❌ | 承上启下原句，用作 Divider 的 `.bridge` 引号句 | Divider 的 `.bridge` div 留空 |
| `is_break` | ❌ | 本节是休息（如"中场休息""走一走"） | 按 `heading` 关键词自动识别：含"休息"/"break"/"中场"/"走动" → `true`；否则 `false` |

### ContentBlock（节内正文拆页用）

正文按内容特征拆成若干 ContentBlock（每个对应一个内容页 slide）：

| 字段 | 说明 | 映射到 slide |
|---|---|---|
| `heading` | 小节标题 | `<h1>` |
| `eyebrow` | 上位定位词 | `.eyebrow` |
| `type` | `concept` / `steps` / `table` / `flow` / `compare` / `code` | 决定套哪个模板 |
| `body` | 正文段落 / 要点数组 / 表格行 | 塞进对应模板的坑位 |
| `step_points` | 若类型是 steps，是否逐步显示 | 有 → `.stepped` + `data-step`；无 → 一次全出 |

`type` 的判定规则：
- 含 `| xxx | xxx |` Markdown 表格 → `table`
- 含 `1. xxx` / `- xxx` 三条以上且每条都短 → `steps`
- 含 `xxx → yyy → zzz` 单行流程 → `flow`
- 含 ```代码块``` → `code`
- 含 "vs" / "对比" / 两列对照 → `compare`
- 其余 → `concept`

---

## 2. Markdown 源 → Schema 的识别规则

**核心原则**：识别靠**语义**不靠**固定标记**。用户可能用 §N / 第一节 / Chapter 1 / 零编号 / 一、二、三 —— 都要吃得下。下面给的模式只是**非穷举举例**，AI 遇到变体要按常识推广，不确定就问用户。

### `section.heading` + `section.number`

标题识别不限符号，以下写法都认：
- `## §N、xxx` / `## §N xxx` / `§N xxx`
- `## N、xxx` / `## N. xxx` / `## N xxx`
- `# 一、xxx` / `## 第一节 xxx` / `第一章 xxx`（中文数字自动转阿拉伯）
- `## Chapter N: xxx` / `## Section N xxx`
- `## xxx` 纯标题无编号 → 按出现顺序自动 `number`

`number` 缺失时**永远按 md 里 `##` 的出现顺序编**，不依赖文本里写没写编号。

### `section.duration`

任何"数字 + 时间单位"的写法都识别：
- `· 5min` / `· 5 min` / `· 5 分钟`
- `(5 分钟)` / `（5min）` / `[5 min]`
- `⏱ 5` / `⏰ 5min` / `🕐 5 分钟`
- `用 5 分钟讲完` / `5 分钟` / `预计 5min`
- 标题同行 / 紧跟下一行 / section 开头第一个 blockquote 里，都要扫

单位转分钟：`sec / s / 秒` → `/ 60`；`h / hr / 小时` → `× 60`。

整份找不到任何时长标记 → 不写 `duration_total`，所有 section `duration` 留空，时间条整体隐藏。

### `section.speaker_strategy` / `section.speaker_speak`

**关键词识别**（不限位置：blockquote / 标题块 / 行内加粗都认）：
- strategy 关键词：`讲解策略` / `策略` / `讲师视角` / `怎么讲` / `备注` / `speaker strategy`
- speak 关键词：`跟学员说` / `对学员说` / `讲师原话` / `口语脚本` / `台词` / `speaker speak`

命中关键词 → 提该块全文作为对应字段。若一段话既可能是 strategy 又可能是 speak，按关键词优先级判；都没关键词但明显是讲师口吻的 blockquote，**不要猜**，留空。

### `section.bridge`

- 优先：显式 `> 承上启下：xxx`
- 次选：`speaker_speak` 的**第一句**（第一个句号前）
- 都没有 → 留空，**不从正文首句改写**

### `section.is_break`

- `heading` 匹配 `/休息|break|中场|走一走|走动|喝水|暂停/i` → `true`
- 或 section body 只有一两行"休息一下"类文本，且 duration < 15 min → `true`

### 模糊识别的处置

- **写法不在上面列举里但语义明显** → 按常识识别，不要死咬字面模式
- **看着像但不确定**（比如 `14:30 开场` 可能是时刻表不是时长） → **问用户一句**，别强解
- **同一份 md 有的节有加分项有的没有** → 逐节独立判定，**不统一降级也不统一强装**

### `section.body` → `ContentBlock[]` 拆分
- 按 `###` 小节标题拆
- 没有 `###` 的整节 → 整段作为 1 个 `concept` block
- 一节 body 过长（>800 字）→ 按段落语义再拆 2-3 个 block

---

## 3. 缺失字段的装配降级表

**用户明示 / 解析器提取到 → 用；否则按下表降级。不要让模型脑补。**

| 字段 | 有 → | 没有 → 装配时 |
|---|---|---|
| `duration_total` | Cover footer 显示 "2.5h · 单人讲完" | Footer 只显示"单人讲完" |
| `section.duration` | Divider `.pill ⏱ N min` + 时间条跑 | 隐藏 `.pill`；整份都没 → `<footer>` 底部时间条整体隐藏 |
| `section.speaker_strategy` | `data-notes-strategy="..."` | **不写这个 attr**（不是写空串） |
| `section.speaker_speak` | `data-notes-speak="..."` | **不写这个 attr** |
| 两者都没 | N 键备注栏显示"本页无备注" | JS 层已处理，模板侧不用特殊写 |
| `section.bridge` | Divider 显示 `.bridge` 带引号句 | Divider 留空 `.bridge` div（保留高度，让布局不跳） |
| `section.is_break` | 生成 `.slide.break` | 不生成休息页 |
| `ContentBlock.step_points` | `.stepped` + 按空格逐步显示 | 一次全出（`.compact`） |

---

## 4. 内容类型识别（lecture / tutorial / doc）

按解析完的字段完整度，自动分类 → 影响后续流程：

| 类型 | 判定 | 装配表现 |
|---|---|---|
| **lecture**（讲义） | 有 `duration` + (`speaker_strategy` 或 `speaker_speak`) | 完整备注 + 时间条 + 可能带休息页 |
| **tutorial**（教程） | 有章节和正文，但无讲师字段 | 无备注 + 无时间条 + 无休息页，但有 Divider / 内容页 / 对照表正常出 |
| **doc**（技术文档） | 无章节层级（只有连续正文）→ **拒绝**，让用户先加 `##` 章节 | — |

**分类只影响提示给用户的"本次装配会/不会有什么"**，不影响 schema 本身。

---

## 5. 规范化产物（可选落盘）

如果讲义复杂 / 用户想复用，skill 可以把解析结果落盘到讲义同目录 `xxx-source.normalized.json`，内容就是上面 schema 的 JSON 形态。**默认不落盘**，只在用户问"你解析出啥"或需要人工校对时才写。

---

## 6. 一个最小合格输入的例子

```markdown
# 怎么用 Claude Code 做日报自动化

## §1 开场 · 5min

今天要讲的事：每周花 2 小时写日报，用 Claude Code 15 分钟搞定。

> 讲解策略：先让学员说自己写日报多久，再展示我的效果，差距越大注意力越高。

> 跟学员说：你们现在每周花多久写日报？举手示意一下。

## §2 看效果 · 8min

现场演示 → 输入 git log → 输出 markdown 日报 → 复制粘贴。

## §3 中场 · 5min

休息一下，喝水。
```

解析后：
- `title`: "怎么用 Claude Code 做日报自动化"（取自 `#`）
- 3 个 sections，number 1/2/3，duration 5/8/5
- §1 有 `speaker_strategy` + `speaker_speak` → lecture 类型
- §3 `heading` 含"中场" → `is_break = true`
- bridge for §1: "你们现在每周花多久写日报"（`speaker_speak` 首句）

---

## 7. 不做的事（**硬性禁令**）

- ❌ `speaker_speak` / `speaker_strategy` 缺失时，**不要**从 `body` 推演出一份"模拟讲师口吻"的备注 —— 瞎编风险远大于价值
- ❌ `duration` 缺失时，**不要**按 section 数平均分配 —— 学员看到假时间会做错判断
- ❌ `bridge` 缺失时，**不要**改写 `body` 第一句当 bridge —— 原句和承上启下句调性不同
- ❌ 整份 md 没 section 层级时，**不要**按字数切片硬分 —— 让用户先加标题
