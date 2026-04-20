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
6. 进入 **tutorial / doc** 模式（讲师字段缺）时，走下面的"结构化补问"一次问齐关键信息

### 结构化补问（tutorial / doc 模式必跑；lecture 模式跳过）

讲师字段不能瞎编，但有几项影响节奏 / 排版的信息可以直接问用户。**一次性把下面清单问完，不要逐条追问**；用户答什么就填什么，不答就按降级走。

清单（固定 3 项，可追加 1 项自定义）：

1. **课程总时长**（`duration_total` 缺时问）—— 自由输入 "45 分钟" / "一个半小时" / "不定 / 自己看"
2. **听众水平**（始终问）—— 三选一：零基础 / 有相关经验 / 进阶
3. **展示场景**（始终问）—— 三选一：线下上课 / 线上直播 / 自学翻阅
4. （可选）其他想让装配知道的事 —— 自由输入

**问法不绑具体 agent UI**：Claude Code 可以用 AskUserQuestion 一次问多题；其他 agent 没这种能力就用 markdown 编号清单单条消息问，让用户一条消息里答全。**核心是"一批问一批答"，不是"一问一答一问一答"**。

**答案怎么用**：
- `duration_total` → 填进 schema，决定要不要出时间条
- 听众水平 → 影响每页信息密度（零基础偏少、进阶可密）和要不要多给图示
- 展示场景 → 线上直播偏大字号 + 弱动画，自学翻阅可以信息密度更高、少步进 reveal

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

## 内容密度参考（hint，不是硬约束）

硬底线只有一条：**不滚动 / 不溢出**。下表是每版式每页的内容上限锚点，防止 6 类模板兜底被砍后模型塞太满。略超但页面仍清爽（字号合适、留白足）可接受；明显超、或 16:9 下逼近边缘就拆页。

| 版式 | 每页上限参考 |
|---|---|
| cover | 1 主标题 + 1 副标题 + 可选 1 行 meta（讲师 / 日期 / 时长）；首页 logo + "AI Spark" 品牌名必须有 |
| divider | eyebrow §N + 1 h1（节标题，≤18 字）+ 可选 ⏱ pill + 可选 bridge 承上启下 1-2 句 |
| body | eyebrow + 1 h1 + **2-6 段正文**（每段 ≤3 句，~60 字）+ 可选 quote ≤2 行 + **出处署名**；段数按内容自由选，5-6 段时字号会自然收小，需目测不溢出 |
| points | **3-5 条**并列要点（4 条最舒服，5 条已经偏紧，6+ 必拆）；每条 1 序号 + 短标题（2-8 字）+ 描述 1-2 行（~30 字） |
| flow | **3-5 个主节点** + 可选 1-2 个 `.future` 虚框；每节点 `.name` 2-4 字 + `.desc` ≤1 行（可 mono 路径） |
| table | **2-4 列 × 3-6 行**（含 thead）；单元格文本 ≤ 20 字；7+ 行先考虑删列 / 拆页 / 降字号 |
| break | 1 大 icon（☕ / 🚶）+ 1 句标语 + ⏱ 时长 pill；浅底 `--brand-faint` |
| 代码块（嵌在 body 内） | ≤ 10 行；单行 ≤ 60 字符；深色窗 `#1a1d24` |

拆页惯例：body 超长拆 "X（1/2）" / "X（2/2）"；points 6+ 条拆页，eyebrow + h1 原样复用，只把要点列表切成 3+3 / 3+4 / 4+4 等（每页 3-4 条最稳），标题后缀"（1/2）"；table 7+ 行先删列再拆行。

## 超量时：C 拆页（默认）vs A 定容轮播（opt-in）

内容超过单页上限时，不要靠压 padding / 压字号硬塞——会一路压到难看。有两条正经出路：

### C · 拆页（**默认**）

按上面"拆页惯例"写。eyebrow / h1 复用、h1 后缀 "（1/2）"、`data-section` 和 `data-time` 相同——面包屑 / 计时器跨两页连续。

**什么时候走 C**：
- 内容可以"前半 / 后半"独立讲（演示步骤、作业清单、参考表）
- 学员可能想回看 / 截屏（两页都留在 deck 历史里方便翻）
- 页数预算宽松

### A · 定容轮播（opt-in · 一页之内换窗口）

`skeleton.html` 的 controller 原生支持。语义："框架不动、内容换"——按 → 把当前一屏 K 条淡出上滑，下一屏 K 条在同位置淡入。

**DOM 约定**：

```html
<div class="items windowed" data-window="4">
  <div class="step" data-step="1">…</div>
  …
  <div class="step" data-step="6">…</div>
</div>
```

- `.windowed` 标记容器；`data-window="K"` 每屏显示 K 条
- N 个 `.step`（1-indexed `data-step`）→ 自动算 `⌈N/K⌉` 屏
- 进入 slide 时第一屏自动显示（stage=1），不用按一下
- controller 自动在容器底部生成 pager（"1–4 / 6"）
- 容器高度锁到首屏实际高度，末屏稀疏时不塌陷
- `.stepped`（累积揭示，如"三条规则"）和 `.windowed`（定容轮播）互斥，按需二选一

**什么时候走 A**：
- 语义上不可拆（如"三条规则"要并排对比；节奏上要"一页讲完"）
- 条数临时超量但整组是同一抽象层级
- 页数预算吃紧，不想再加页

**什么时候不走 A**：
- 学员需要**对照着做**（§8 六步流程这种手把手清单）——全可见 > 节奏好
- 参考表 / 目录结构（学员要截屏）——拆页比轮播友好

### 装配后必跑：静态 lint（闭环）

**装配完不算完**。跑一遍 linter，收敛到 0 告警才算交付：

```bash
python3 assets/lint.py <source>-PPT.html
```

linter 按结构阈值扫所有 slide，抓 `.points / .demo-steps / tbody / .body / .flow-row` 的超量，每条告警给出"slide N · §N · 容器 · 实际/阈值 · 建议"。`data-window` 已开的容器自动跳过（不误报 A 用户）。

**工作流**：

```
assemble  →  lint
           ├─ 0 告警 → 交付
           └─ 有告警 → 就地改（C 拆 or A 开 data-window）→ lint → …
```

**豁免**（per-slide opt-out）：某页确实放得下（如 compact padding / 字号特调），在该 `.slide` 上加 `data-lint-skip="<kind>[,<kind>]"`，值从下面这列拿：`points_single` / `points_two` / `points_cmp` / `demo_steps` / `table_rows` / `body_paras` / `flow_nodes`。

**别滥用豁免**。豁免 = "我肉眼验过了真的放得下"。新加内容（多了一行 / 长了一句）要重新验证。

### 运行时二道关：controller 溢出 warning

linter 只抓结构超量，抓不到像素级（标题换行撑破版 / 长 cell 撑宽）。controller 进入每页时补一道检测：`.body / .items / .demo-steps / .flow / table / .ascii-box / .quote` 跨过 slogan 安全线（deck 底 - 3.5cqw）就往浏览器 console 打：

```
⚠ slide 12 溢出 slogan 安全线 · 超出 1.8cqw · 最差元素: div.demo-steps · 建议走 C 拆页或 A 轮播
```

lint 干净后再开浏览器过一遍 console，双保险。

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
- 不要在每页 slide 里手写底部 slogan 条或背景水印 —— skeleton 的 `.deck-bottom`（品牌蓝 "AI Spark · 始于火花 成于实战"）和 `.slide::before`（flame + AI Spark 黑剪影水印，opacity 0.015）是 deck 级全局 chrome / bg，cover + end 页由 controller 自动隐藏底部 slogan 条（cover footer 自带 slogan 位；end 页自带收尾 slogan，避免与全局条重复）。**首页 slide class 必须带 `cover`，末页必须带 `end`**，controller 靠这两个 class 判断

## 参考文件

- `assets/lint.py` — 装配后跑的静态密度 linter（无依赖，Python 3 stdlib）
- `assets/skeleton.html` — 技术骨架（verbatim 拷入最终 deck）
- `assets/layouts/index.html` — Layouts Gallery 入口，7 张 layout 缩略一览 + 锚点导航
- `assets/layouts/<body|points|flow|table|cover|divider|break>.html` — 单版式 preview，可视化预览 + 顶部注释的数据形状 / 典型场景 / 关键机制 / 装配期注意（非装配模板，仅视觉参考）
- `assets/examples/example-<text|flow|table>-heavy.html` — 3 份通用示例 deck，各 8 页完整串法。文字密 / 图形重 / 结构化三种定位，演示多版式组合 + 转场节奏 + controller 真跑；装配新 deck 吃不准"整份怎么串"时翻这里。**内容纯占位，别拿来当业务参考**
- `references/source-schema.md` — 输入字段 schema + 识别规则 + 降级策略
- `references/design-system.md` — 品牌资产清单
- `references/animation-reference.md` — 动画 primitive class 清单 + 核心技术技巧 + 合法例外 + 禁止清单
