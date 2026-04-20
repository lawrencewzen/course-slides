---
name: course-deck
description: 把 Markdown 源（课堂讲义 / 教程 / 技术分享稿 / 内部文档）转成单文件 .html 课堂 PPT。适用于 AI Spark 训练营、内部分享、课程录制等场景。**只要用户提到"把讲义/教程做成 PPT"、"上课用的幻灯片"、"分享会"、"训练营 PPT"、"course slides"，或者给了 .md 说要展示，就要触发本 skill。** 输入先按 `references/source-schema.md` 规范化，缺失字段按降级策略处理（缺备注就留空，不自动编）。严格走「采访 → 4 轮 playground → 装配」流程（第一次或换风格时），有既定风格则走快通道。视觉系统固定（白底 + AI Spark 品牌蓝点缀 + 克制 Keynote 风），不让模型自由发挥配色和动画。
---

# course-deck · 讲义到课堂 PPT

把一份 Markdown 讲义，变成一份能直接上台讲的单文件 HTML PPT。**不是"导出 PDF 那种 PPT"，是带翻页、动画、演讲者备注、时间条、键盘控制的真正可放映的 PPT。**

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

## 输入

最低输入：一份 Markdown 路径。**格式不重要，内容完整度决定模式**。

### 硬性最低要求（tutorial 模式 · 能跑的底线）

- 至少一层章节标题（`##` 或 `#` 都行，写法不拘）
- 章节内有实质内容（段落 / 要点 / 表格 / 代码）

### 加分项（有就自动升级到 lecture 模式 · 完整 PPT）

skill **逐节扫描**，**不看标题符号**（§1 / 一、/ 1. / 纯 `## 标题` 全识别），只看这节**内部是不是有下面这些信息**：

- **时长** —— `· 5min` / `（5 分钟）` / `[5 min]` / `⏱ 5` / `用 5 分钟讲完` 等任何"数字 + 时间单位"写法
- **讲师视角内容** —— 识别关键词：`讲解策略` / `跟学员说` / `对学员说` / `讲师原话` / `口语脚本` / `演讲备注` / `speaker note` 等，任意一个都算
- **承上启下句** —— 从"讲师视角内容"首句自动提取；或显式写 `> 承上启下：xxx`

### AI 智能识别原则（**硬性要求**）

- **不强制任何模板**：用户的讲义可能用 §1 / 第一节 / Chapter 1 / 零编号 —— 都吃得下
- **逐节独立判定**：同一份 md 里有的节有时长有的没有 → 有的节出时间条 pill 有的不出，**不统一降级也不统一强装**
- **拿不准就问用户**：节标题看着像时间戳（如 "14:30 开场"）时，问一句"这是时长标注还是时间表时刻"
- **不硬套 §N 格式**：哪怕源文件一个 § 都没有，只要有讲师字段，一样认定为 lecture 模式走完整装配

详细识别规则看 `references/source-schema.md` 第 2 节。

不管哪种输入，skill 第一步都走**输入规范化**，见下一节。

## 输入规范化（**装配前必跑**）

所有 Markdown 源进来，第一步**按 `references/source-schema.md` 解析成结构化 schema**，再进入 playground / 装配。

### 要做的事

1. 按 `references/source-schema.md` 第 2 节的识别规则，逐字段提取：
   - `title` / `subtitle` / `duration_total`
   - 每个 `section` 的 `heading` / `number` / `duration` / `speaker_strategy` / `speaker_speak` / `bridge` / `is_break` / `body`
   - 每个 section body 进一步拆成 `ContentBlock[]`（按 `###` 或段落语义）
2. 按字段完整度判定内容类型（**lecture** / **tutorial** / **doc**）
3. 把判定结果**简短报给用户**，例如：
   > 解析完毕 · 共 7 节 · tutorial 模式（无讲师备注、无时间条、无休息页）· 预计 22 页
4. 如果是 **doc** 类型（无章节层级） → 停下，请用户先加 `##` 章节再来
5. 如果 `title` 缺失且无法从文件名推 → 问用户一句

### 缺失字段绝不自动补

**硬性禁令**（重复 `references/source-schema.md` 第 7 节的核心三条）：

- `speaker_speak` / `speaker_strategy` 缺失 → **留空**，不从正文推演一份"模拟讲师口吻"的备注
- `duration` 缺失 → **留空**，不按 section 数平均分配；时间条整体隐藏
- `bridge` 缺失 → **留空**，不改写正文首句当 bridge

**为什么**：瞎编的备注会误导讲师，瞎编的时长会让学员做错节奏判断。宁可缺，不能假。

### 降级装配对照

字段缺失时装配侧如何降级，见 `references/slide-templates.md` 末尾的"缺失字段降级表"。核心：

| 缺 | 装配 |
|---|---|
| 全部 `duration` | 隐藏底部时间条 + 不生成休息页 |
| 某节 `duration` | 该节 Divider 的 `⏱ N min` pill 不出 |
| `speaker_*` | 不写 `data-notes-*` attr（不是写空串）|
| `bridge` | Divider 的 `.bridge` 保留 div 但内容为空 |
| `step_points` | Steps 内容页一次全出，不走 `.stepped` |

## 快通道：按既定风格直接装配（默认就走这条）

**前提**：用户已经跑过一次完整流程，或本仓库自带的 `assets/playground-templates/` + `assets/final-deck-example.html` 就是他想要的风格。这种情况下**不要**再拉采访和 4 轮 playground——那是浪费时间，用户会不耐烦。

**触发条件**（满足任一即走快通道）：

1. 用户明说"按老样子"、"按之前那套"、"直接装"、"不用问了"、"按我的来"之类
2. 用户这次没换品牌（没提 logo / 主色 / slogan），且本 skill 自带的 `assets/final-deck-example.html` 的品牌就是他熟悉的那套（默认 AI Spark）
3. 用户的仓库/讲义同级目录下已经有一份完工的 `*-PPT.html` 或 `playground/` 目录（说明风格已定）

**做法**：

1. 直接读 `assets/final-deck-example.html` 作为骨架（或用户指向的既有 `*-PPT.html`）——CSS tokens、JS controller、slide chrome 全部复用
2. 读讲义 `.md`，按 `references/slide-templates.md` + `references/components.md` 生成每节 slide
3. 装配成 `<lecture-name>-PPT.html`，用浏览器打开交付验收
4. **只在开工前确认一句**："按你现有风格直接装配 → `xxx-PPT.html`，不走采访和 playground，可以？"——得到肯定回复就开干，否则掉头走下面的完整流程

**不要做**：快通道里**不要**再摆 3 版封面/分隔让用户挑，**不要**再问长宽比/动画/组件样式——这些都定好了。采访只在用户明确要换风格或是第一次跑时才用。

---

## 完整工作流（第一次用 or 换风格时才走）

### 阶段 1 · 采访（约 4 组结构化提问）

> 用你 agent 自带的结构化提问工具：Claude Code 是 `AskUserQuestion`，Codex 是 `ask_user_question`；都没有就用自然语言一组一组问。

目的：在动手前锁定 12 项决策，避免后期返工。**即使用户说"你定就行"，也要走完采访**——因为后面 4 轮 playground 都基于这些决策。

12 项决策、每组 3-4 个、每项 3 个选项 + Recommended，详见 `references/interview-script.md`。

第一组（基础架构 4 问）：框架 / 长宽比 / 动画基调 / 页内步进
第二组（关键组件样式 4 问）：目录树 / 流程图 / 对比叙事 / 代码块
第三组（演讲辅助 4 问）：演讲者备注 / 时间条 / 导航 / 交付形式

如果用户提供了**视觉品牌资产**（logo / 主色 / slogan），先读图分析，然后提一个"风格冲突仲裁问题"——因为高饱和品牌色和"克制 Keynote 风"通常打架，要让用户明确选边。

### 阶段 2 · 品牌锁定

如果用户没提供品牌资产，使用默认（AI Spark）：
- Logo：`assets/playground-templates/01-cover.html` 里有完整的火苗 SVG 路径，直接复用
- 主色：`#1E40FF`
- Slogan：「始于火花 · 成于实战」

如果用户提供了：
- 取主色（hex），替换 `--brand` 变量
- 取 logo（SVG 优先，PNG 也行），替换 `<symbol id="logo-flame">` 内容
- 取 slogan，替换封面/分隔页文案

锁定后，**所有后续 playground 和最终 deck 都用这套品牌**，不再变。

### 阶段 3 · 4 轮 playground

**关键原则**：每轮做一个独立 .html 文件，并排展示候选方案，每个方案都有「重播动画」+「全屏预览」按钮。**用户看完才进下一轮，不要批量出**。

存放位置：跟讲义同目录的 `playground/` 文件夹下。

| 轮次 | 文件 | 内容 |
|---|---|---|
| 01 | `playground/01-cover.html` | 封面页 × 3 版本（A 极简 Swiss / B 中轴 Keynote / C 不对称双栏） |
| 02 | `playground/02-section-divider.html` | 章节分隔页 × 3 版本（大节号 / 时间轴 / 节奏卡片） |
| 02b | `playground/02b-divider-bridge.html` | 分隔页是否加"承上启下原句"对比版（A 简版 vs A+ 增强版） |
| 03 | `playground/03-content-pages.html` | 内容页 3 模板（概念解释 / 步进要点 / 对照表）—— **3 个模板都要用，不是 3 选 1** |
| 04 | `playground/04-components.html` | 4 个关键组件（目录树 / 流程图 / 对比叙事 / 代码块） |

**直接复制 `assets/playground-templates/` 下的对应文件作为起点**，然后：
1. 替换品牌（如果用户用了自定义品牌）
2. 替换示例内容为本讲义里的真实内容（用 §X 节、真实文件名、真实流程）
3. 用浏览器打开（macOS 可用 `open <path>`；没有桌面环境就把路径给用户让其自行打开）

**每轮等用户反馈再继续**：
- 通过 → 进下一轮
- 想改某处 → 修改后再开一次
- 看不出差别 → 推荐 A 版

### 阶段 4 · 最终装配

**输出**：`<source-name>-PPT.html`，跟源文件同目录。

**做法**：
1. 读 `assets/final-deck-example.html` 作为骨架——它包含完整的 deck shell、chrome、CSS tokens、JS controller（翻页/步进/演讲者备注/时间条/键盘）
2. **用"输入规范化"阶段已经解析好的 schema**（见 `references/source-schema.md`），不要再重新解析 md
3. 按 `references/slide-templates.md` 里的对应模板生成每页 HTML；**按缺失字段降级表处理空字段**
4. 按 `references/components.md` 里的对应组件生成目录树 / 流程图 / 对比 / 代码块 slide
5. 把所有 slide 装进 deck，**保留 example 里的 deck-chrome、speaker-notes、hotkey-help、JS 不变**
6. 用浏览器打开供用户验收

**slide 顺序约定**（典型 lecture 9 节 + 2 休息）：
1. Cover
2. §1 Divider → §1 内容页
3. §2 Divider → §2 内容页
4. ...每节都是 Divider → 内容页（数量按节大小定）
5. 休息节（`is_break = true`）用 `.slide.break`
6. 末尾 End / Q&A 页

**页数预期**：
- lecture 模式 9 节 ≈ 30-40 页
- tutorial 模式 ≈ 1.5-2 × 章节数（无休息页、章节通常更短）
- 不论哪种模式，Cover + End 各 1 张是固定的

## 设计系统（**严格遵守**）

详见 `references/design-system.md`，关键约束：

| 维度 | 约束 |
|---|---|
| 配色 | 白底 + 品牌主色 ≤10% 点缀；不能整页底色用品牌色 |
| 例外 | 休息页可用 `--brand-faint` 浅蓝底；代码块组件用 `#1a1d24` 深色窗口 |
| 风格 | 克制 Apple Keynote 风：淡入 + 轻微上移，0.85s ease。**禁止戏剧动画**（弹跳、旋转、大位移） |
| 字体 | 系统栈（PingFang SC / Hiragino Sans GB / Microsoft YaHei），**禁止引入外部字体** |
| 单位 | 所有 slide 内尺寸用 `cqw`（容器查询单位），让文字随 slide 缩放 |
| Logo | 用 `<symbol id="logo-flame">` 模式定义一次，多处 `<use href="#logo-flame">` |
| 框架 | **不用 reveal.js / Slidev / Tailwind CDN**——纯 HTML+CSS+JS 单文件 |

## 关键技术技巧（**模型必须知道**）

详见 `references/design-system.md`，最关键 3 个：

1. **重播动画的 reset 模式**——必须用 `no-anim` class + 双 `requestAnimationFrame`，单层 reflow 不够
2. **步进 reveal 模式**——`data-steps` + `data-stage` + `data-step` 配合 JS 的 `.revealed` class
3. **slide 切换**——单 `.deck` 容器 + 多 `.slide` absolute 定位 + opacity 切换；`.active` 切换时复用重播 reset 触发动画

## 后续样式改动也走 playground

装配完成后，任何 slide 样式调整（配色、布局、组件、动画）都**不允许直接改 `<lecture-name>-PPT.html`**：

1. 在 `playground/` 下新建一个对照 html（命名如 `05-tweak-<描述>.html`），把要改的 slide 单独拎出来做新旧两版
2. 用浏览器打开，截图给用户看 before/after
3. 用户点头后，再把通过的版本落到正式 deck

**Why**：正式 deck 里 slide 共享 CSS tokens、JS controller、动画时序，直接改容易污染其他页或打断翻页；playground 的对照视图也让用户一眼看出差别，省得口头描述拉扯。

## 不要做的事

- 不要让模型自由设计配色（必须用 brand color + 白底）
- 不要让模型用第三方框架（reveal.js / Slidev / Tailwind CDN）
- 不要在内容页面用整页深色底（只有代码块组件用 `#1a1d24`）
- 不要加 emoji 装饰（除了休息页的 ☕ 🚶 这种功能性 icon、和组件 3 散乱状态里的 ⚠️📄）
- 不要在"第一次跑 + 新品牌"的情况下省略采访（这是 skill 的核心价值之一）；但如果命中上面的「快通道」触发条件，**必须**走快通道，别倒回来重新走 4 轮 playground
- 不要把每轮 playground 一次性全部生成，要一轮一轮来
- 不要在装配时把 deck-chrome / JS controller 重写——直接复用 `final-deck-example.html` 里的，那是验证过能用的

## 参考文件

- `references/source-schema.md` — **输入源字段 schema + 识别规则 + 降级策略**（装配前必读）
- `references/design-system.md` — 配色 / 动画 / 单位 / 关键技巧
- `references/interview-script.md` — 12 项决策的完整问句和推荐项
- `references/slide-templates.md` — 6 类 slide（cover/divider/break/concept/steps/table）的 HTML 骨架
- `references/components.md` — 4 个组件（tree/flow/compare/code）的 HTML 骨架
- `assets/playground-templates/0X-*.html` — 4 轮 playground 的可直接复用模板
- `assets/final-deck-example.html` — 完整可放映的 PPT 范本（AI Spark 04 课）

## 一个完整流程的样子

```
用户：把 course/xxx/讲义.md 做成 PPT

你：好，开始采访。先问 4 个基础问题。
   [结构化提问: 框架/比例/动画/步进]

用户：[全推荐]

你：第二组，关键组件样式。
   [结构化提问: 目录树/流程图/对比/代码块]

用户：[全推荐]

你：第三组，演讲辅助。
   [结构化提问: 备注/时间条/导航/交付]

用户：[全推荐]

你：[如果用户没传品牌图]
   品牌资产：你想用默认 AI Spark，还是有自己的 logo 和主色？

用户：默认就行

你：好，开始 Playground 01 封面页。
   [复制 assets/playground-templates/01-cover.html → playground/01-cover.html]
   [替换示例文案为本讲义内容]
   [用浏览器打开]
   3 版封面已开。选哪一版？

用户：A

你：进 Playground 02 章节分隔页。
   [同上]
   ...

[4 轮 playground 都过完]

你：开始装配最终 PPT。
   [读 final-deck-example.html 作为骨架]
   [按讲义 9 节生成 ~36 页 slide]
   [写入 <lecture-name>-PPT.html]
   [用浏览器打开]
   PPT 已开，按 → / 空格翻页，N 看演讲者备注。

用户：[验收]
```

整个流程通常需要 4-6 轮交互，约 30 分钟出成品。**不要心急一次出完**——节奏感是 skill 的价值之一。
