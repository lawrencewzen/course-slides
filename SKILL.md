---
name: course-slides
description: 把 Markdown 源（课堂讲义 / 教程 / 技术分享稿 / 内部文档）转成带 AI Spark 品牌身份的单文件 .html 课堂 PPT。适用于 AI Spark 训练营、内部分享、课程录制等场景。**只要用户提到"把讲义/教程做成 PPT"、"上课用的幻灯片"、"分享会"、"训练营 PPT"、"course slides"，或者给了 .md 说要展示，就要触发本 skill。** 输入按 `references/source-schema.md` 规范化，缺失字段按降级策略处理（缺备注就留空，不自动编）。装配时从 `assets/skeleton.html` 整段拷技术骨架 + 品牌 tokens（CSS / JS controller / deck chrome / 演讲者备注 / 时间条 / 键盘控制），每页 slide 版式由模型按内容自由决定，视觉参考 `assets/layouts/` 单版式 gallery，受 4 条视觉底线约束（白底 + 品牌蓝 #1E40FF 点缀 + 克制 Keynote 风 + 系统字体栈）。
---

# course-slides · 讲义到课堂 PPT

把一份 md 变成一份能直接上台讲的单文件 HTML PPT。不是"导出 PDF 那种 PPT"，是带翻页、动画、演讲者备注、时间条、键盘控制的真正可放映的 PPT。

## 何时触发

强触发：
- 用户提供了 .md 源（讲义 / 教程 / 技术分享稿 / 长篇博客），说要做成 PPT / 幻灯片 / 上台讲
- 用户说"做一个上课用的 PPT"、"训练营要用的幻灯片"、"分享会的 deck"
- 用户问"怎么把这份讲义/教程展示出来"
- 用户提到 "AI Spark"、"全链路 AI 创作工作流" 这类课程时
- 讲义是**完整形态**（带 §N / 时长 / 讲解策略） → lecture 模式
- 输入是**教程 / 技术文档**（只有 `##` 章节 + 正文，无讲师字段） → tutorial 模式，按降级策略装（无备注 / 无时间条 / 无休息页）

弱触发但仍然适用：
- "做一个 HTML 幻灯片"、"网页版 PPT"、"演示文稿"
- 用户已经看过本 skill 的产出（火苗 logo、品牌蓝、克制风），想再做一份

不适用：
- 单页落地页 / 营销页（不是分节、不是用来上台讲的）
- 数据 dashboard、内部报告
- 无章节层级的纯散文 / 纯代码仓库 README（`references/source-schema.md` 里列为 `doc` 类型，**拒绝**，让用户先加 `##` 章节）

**语义前提**：输入必须是**用来给人讲 / 看 / 分享的内容**（讲义、教程、博客、会议纪要、项目宣讲、产品需求等皆可），而非数据 dump / DB schema / changelog / 日志导出 —— 后者即便有 `##` 结构，装成 PPT 也没意义。判断不确定时问用户一句："这份 md 是要拿来上台讲 / 给人看的吧？"

## 输入识别（lecture vs tutorial vs doc）

skill **逐节扫描**，**不看标题符号**（§1 / 一、/ 1. / 纯 `## 标题` 全识别），只看这节内部是不是有下面这些信息：

- **时长** —— `· 5min` / `（5 分钟）` / `[5 min]` / `⏱ 5` / `用 5 分钟讲完` 等任何"数字 + 时间单位"写法
- **讲师视角内容** —— 识别关键词：`讲解策略` / `跟学员说` / `对学员说` / `讲师原话` / `口语脚本` / `演讲备注` / `speaker note` 等，任意一个都算
- **承上启下句** —— 从"讲师视角内容"首句自动提取；或显式写 `> 承上启下：xxx`

**逐节独立判定**：同一份 md 里有的节有时长有的没有 → 有的节出时间条 pill 有的不出，**不统一降级也不统一强装**。

**拿不准就问用户**：节标题看着像时间戳（如 "14:30 开场"）时，问一句"这是时长标注还是时间表时刻"。

详细识别规则看 `references/source-schema.md` 第 2 节。

## 输入规范化（装配前必跑）

所有 Markdown 源进来，第一步按 `references/source-schema.md` 解析成结构化 schema，再进入装配。

### 要做的事

1. 按 `references/source-schema.md` 第 2 节的识别规则，逐字段提取：
   - `title` / `subtitle` / `duration_total`
   - 每个 `section` 的 `heading` / `number` / `duration` / `speaker_strategy` / `speaker_speak` / `bridge` / `is_break` / `body`
   - 每个 section body 进一步拆成 `ContentBlock[]`（按 `###` 或段落语义）
2. 按字段完整度判定内容类型（**lecture** / **tutorial** / **doc**）
3. 把判定结果简短报给用户，例如：
   > 解析完毕 · 共 7 节 · tutorial 模式（无讲师备注、无时间条、无休息页）· 预计 22 页
4. 如果是 **doc** 类型（无章节层级） → 停下，请用户先加 `##` 章节再来
5. 如果 `title` 缺失且无法从文件名推 → 问用户一句

### 缺失字段绝不自动补

- `speaker_speak` / `speaker_strategy` 缺失 → 留空，不从正文推演一份"模拟讲师口吻"的备注
- `duration` 缺失 → 留空，不按 section 数平均分配；时间条整体隐藏
- `bridge` 缺失 → 留空，不改写正文首句当 bridge

**为什么**：瞎编的备注会误导讲师，瞎编的时长会让学员做错节奏判断。宁可缺，不能假。

### 缺失字段降级对照

| 缺 | 装配 |
|---|---|
| 全部 `duration` | 隐藏底部时间条 + 不生成休息页 |
| 某节 `duration` | 该节 Divider 的 `⏱ N min` pill 不出 |
| `speaker_*` | 不写 `data-notes-*` attr（不是写空串）|
| `bridge` | Divider 的 `.bridge` 保留 div 但内容为空 |
| `step_points` | 内容页一次全出，不走步进 reveal |

## 装配

1. 读 `assets/skeleton.html`，**整段 verbatim 拷入**最终 deck：
   - `<style>` 里所有内容（CSS tokens / deck shell / chrome / slide base / animation primitives / **section 6 global slogan + watermark** / notes / hotkey help / timer）—— 除了末尾 `SKELETON-ONLY · 占位 slide 样式` 那段，整段删掉
   - `<body>` 里 `<symbol id="logo-flame">` + `.deck` 外壳 + `.deck-progress` + `.deck-top` + `.deck-timer` + `.deck-bottom`（底部 slogan 条）
   - `<body>` 末尾 `.notes` 浮层 + `.hotkey-help` 浮层
   - `<script>` 里整段 DECK CONTROLLER（含 cover 页自动隐藏 `.deck-bottom` 逻辑）
   - 把 skeleton 里那张 `SKELETON-ONLY` 占位 slide 删掉
2. 按 schema 生成每页 slide 插入 `.deck`：
   - 每节至少一页 Divider + 若干内容页
   - 布局 / 信息密度 / 是否分步 / 用不用表格流程图 —— 按这节的内容决定，不受预设模板约束
   - 动画**不要重写**，复用骨架里 `.fade-up` / `.fade-in` / `.d1-.d8` / `.step` 这些 primitive class 就够；用法见 `references/animation-reference.md`
   - 必须遵守下面 4 条视觉底线
   - 视觉上吃不准某类页怎么排时，翻 `assets/layouts/` 对应版式的 preview + 顶部注释"数据形状 / 典型场景 / 关键机制 / 装配期注意"定位；layouts/ 只是视觉参考不是装配模板，每页版式仍按内容自由设计
   - **纯正文页规则**：如果一页是 eyebrow + h1 + 多段 body（可选 quote），slide class 要写 `content body`。`.body` 触发"quote 底部锚定"：quote 用 `margin-top: auto` 推到页面底部，段落顺着 fade-up 链从顶部展开。body 段数按内容自由选 2-6 段，**不要限制在 2 段**，内容充足时段落会自然撑满整页
3. 首页必须有 logo + "AI Spark" 品牌名 + 讲义标题；末页必须有 End / Q&A
4. 写入 `<source>-PPT.html`，浏览器打开验收

## 视觉底线（4 条，硬性）

1. 白底 + 品牌色 `#1E40FF` 点缀 ≤10%；例外：休息页用 `--brand-faint` 浅底、代码块用 `#1a1d24` 深色窗
2. 动画克制 Apple Keynote 风：淡入 + 轻微上移，0.85s ease；禁弹跳 / 旋转 / 大位移
3. 尺寸用 `cqw`，字体用系统栈（PingFang SC / Hiragino Sans GB / Microsoft YaHei）；不引外部字体；不用 reveal.js / Slidev / Tailwind CDN
4. 首页有 logo + "AI Spark"，末页有 End / Q&A

品牌资产细节见 `references/design-system.md`；动画写法见 `references/animation-reference.md`。

## 后续改动走 tweak 对照

装配后要改某页，不直接动 `<source>-PPT.html`：

1. 在同目录 `tweaks/` 下新建 `tweak-<描述>.html`，把要改的 slide 拎出来做新旧两版
2. 浏览器打开给用户看 before / after
3. 用户点头后再把通过的版本落回正式 deck

**Why**：正式 deck 里 slide 共享 CSS tokens / JS controller / 动画时序，直接改易污染其他页；对照视图也让用户一眼看出差别，省得口头描述拉扯。

## 不要做的事

- 不要自由设计配色（必须用品牌 tokens）
- 不要用第三方框架（reveal.js / Slidev / Tailwind CDN）
- 不要在内容页用整页深色底（只有代码块组件用 `#1a1d24`）
- 不要加装饰 emoji（除休息页 ☕ 🚶 和状态 icon ⚠️ 📄 这种功能性）
- 不要重写 deck chrome / JS controller / 动画 primitive —— 直接复用 `skeleton.html` 里的，那是验证过能用的
- 不要在每页 slide 里手写底部 slogan 条或背景水印 —— skeleton 的 `.deck-bottom`（品牌蓝 "AI Spark · 始于火花 成于实战"）和 `.slide::before`（flame + AI Spark 黑剪影水印，opacity 0.015）是 deck 级全局 chrome / bg，cover 页由 controller 自动隐藏 slogan 条（cover 自己 footer 有 slogan 位）

## 参考文件

- `assets/skeleton.html` — 技术骨架（verbatim 拷入最终 deck）
- `assets/layouts/index.html` — Layouts Gallery 入口，7 张 layout 缩略一览 + 锚点导航
- `assets/layouts/<body|points|flow|table|cover|divider|break>.html` — 单版式 preview，可视化预览 + 顶部注释的数据形状 / 典型场景 / 关键机制 / 装配期注意（非装配模板，仅视觉参考）
- `references/source-schema.md` — 输入字段 schema + 识别规则 + 降级策略
- `references/design-system.md` — 品牌资产清单
- `references/animation-reference.md` — 动画 primitive class 清单 + 核心技术技巧 + 合法例外 + 禁止清单
