# 动画参考

`assets/skeleton.html` 已经把所有通用动画实现 verbatim 包好，装配时**不要自己写动画**，用下面列的类就够。本文档只讲：

1. 3 个核心技术技巧（为什么要这么写，别"顺手优化"掉）
2. Primitive class 清单（哪个 class 干什么）
3. 合法例外（SKILL.md "克制 Keynote 风"之外允许的动画）
4. 禁止清单

## 1. 3 个核心技术技巧

### 1.1 `.active` 切换时的动画重播（双 rAF）

每页 slide 翻到时，入场动画（`.fade-up` / `.fade-in` / `.step`）要**重播一次**。靠 JS 里这段：

```js
active.classList.add('no-anim');
active.classList.remove('playing');
void active.offsetWidth;                // 强制 reflow
requestAnimationFrame(() => {
  active.classList.remove('no-anim');
  requestAnimationFrame(() => {          // 关键：要双 rAF
    active.classList.add('playing');
  });
});
```

**为什么双 rAF 不能省**：单层会被浏览器把"恢复 transition"和"加 playing"合并到同一帧，transition 没机会从"已完成"状态滑到"起始状态"，动画不播。亲测改成单层 rAF 就是静态闪现。

`.no-anim` class 会把整个 slide 的 transition 全禁掉（`transition: none !important`），让 `.fade-up` 的 opacity/transform 瞬时回到 0/14px，再去掉 `.no-anim` + 加 `playing` 触发重新过渡。

---

### 1.2 步进 reveal（`data-steps` + `.revealed`）

按键分段出现用于"三条规则""六步流程"这类场景：

HTML：
```html
<div class="slide content stepped" data-steps="3">
  <div class="step" data-step="1">规则一</div>
  <div class="step" data-step="2">规则二</div>
  <div class="step" data-step="3">规则三</div>
</div>
```

机制：
- slide 加 `.stepped` class + `data-steps="K"` 声明总步数
- 每个分步元素加 `.step` + `data-step="N"`
- 按右键时，JS 把 `dataset.stage` 加 1，给所有 `data-step <= stage` 的 `.step` 加 `.revealed`
- 左键倒序移除 `.revealed`
- `show()` 切到这页时重置 `dataset.stage = '0'` + 清空所有 `.revealed`

`.step` CSS 的过渡时长是 0.6s（不跟 `.fade-up` 的 0.85s 共用），是因为步进时希望反馈比入场快一点。

**延伸用法**：流程图节点按步亮起 —— 用 `data-lit-step="N"` attr，步进到第 N 步时 JS 给该节点加 `.lit` class。

---

### 1.3 slide 切换（单 `.deck` + absolute + opacity）

所有 slide `position: absolute; inset: 0;` 叠在同一 `.deck` 容器里，只有 `.active` 那张 `opacity: 1` 可见。翻页 = 换 `.active` class + 0.45s opacity transition。

**为什么不用 scroll-snap**：scroll-snap 是 frontend-slides 的做法，要求每页占一个 viewport，整页滚。我们的做法是 16:9 letterbox 里换 slide，deck 本身不滚，浏览器上下留黑边，更像放映。这两套机制**不通用**，不要混。

---

## 2. Primitive class 清单

所有 primitive 都在 skeleton.html CSS section 5，整段复用就行。

| class | 作用 | 初始态 | `.active.playing` 后 |
|---|---|---|---|
| `.fade-up` | 淡入 + 上移 14px 过渡（0.85s） | opacity 0, translateY(14px) | opacity 1, translateY(0) |
| `.fade-in` | 纯淡入（0.85s） | opacity 0 | opacity 1 |
| `.d1` .. `.d8` | transition-delay 0.10s .. 1.50s（步长 0.2s）| - | - |
| `.no-anim` | 禁用整个 slide 的所有 transition（配合双 rAF 用）| - | - |
| `.step` | 步进元素，要 `.revealed` 才出（0.6s） | opacity 0, translateY(14px) | 不自动出；由 JS 加 `.revealed` |

**典型用法**：

```html
<div class="slide content" data-section="1" data-section-name="开场">
  <div class="eyebrow fade-up d1">一句话</div>
  <h1 class="fade-up d2">下课后你会拥有一台属于自己的写作流水线</h1>
  <div class="body">
    <p class="fade-up d3">从想法到成品...</p>
    <p class="fade-up d4">前半段你看我演示...</p>
  </div>
</div>
```

delay 建议按"视线落点顺序"递增，不要每条都 d1 齐刷（齐刷 = 没节奏）。d1/d2/d3/d4 四条线是最常用组合，d5-d8 备用。

---

## 3. 合法例外（"克制 Keynote 风"之外允许的）

SKILL.md 视觉底线第 2 条禁弹跳 / 旋转 / 大位移。以下是**功能性动画**的合法例外，不当装饰：

### 3.1 流程图箭头"流光"

`.flow-arrow.lit::before` 跑 `@keyframes flow-light`，一条白色半透明竖条从左往右刷过亮起的箭头（1.4s linear infinite）：

```css
.flow-arrow.lit::before {
  content: ''; position: absolute;
  top: 0; left: 0; height: 100%; width: 30%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.85), transparent);
  animation: flow-light 1.4s linear infinite;
}
@keyframes flow-light {
  0% { left: -30%; }
  100% { left: 100%; }
}
```

作 UI 反馈用（标识当前所处环节），不要挪作他用。

### 3.2 标题"荧光笔"扫过

`h1 .accent` 用 `linear-gradient(transparent 70%, var(--brand-soft) 70%)` 做底色强调，**不闪不动**（伪动画）：

```css
.slide.content h1 .accent {
  background: linear-gradient(transparent 70%, var(--brand-soft) 70%);
  padding: 0 0.05em;
}
```

静态效果，算"克制的视觉强调"，不属违规动画。

### 3.3 火苗 logo 的"贴纸感"

`<symbol id="logo-flame">` 里的 path 用 `style="paint-order: stroke fill"` 让白描边画在填充下面，视觉上像"贴纸"。这是 **SVG 样式技巧不是动画**，但属于"不要顺手优化掉"的关键细节 —— 去掉描边顺序，贴纸感消失。

### 3.4 chrome 浮层的 0.4s opacity 过渡

`.deck-top` / `.deck-timer` / `.notes` / `.hotkey-help` 开关都走 opacity transition，时长 0.3–0.4s ease。算 UI 交互反馈，不属于"动画装饰"。

---

## 4. 禁止清单

以下动画**不要加**，即便看着"更有设计感"：

- **弹跳**（`cubic-bezier` 带反弹 / `@keyframes` 有 overshoot）—— 不符合 Keynote 风
- **旋转**（`transform: rotate(...)` 作为入场）—— 太抢戏，学员视线被拽走
- **大位移**（translateY/X > 20px 的入场）—— 显得慌乱；统一用 14px
- **spring / 物理动画**（react-spring / framer-motion 那套感觉）—— 不克制
- **持续循环动画**（除 `flow-light` 外）—— 课堂 PPT 不是网页 hero section
- **hover 动画**（课堂是放映场景，没有 hover）—— 除非是讲师演示 demo 页

如果内容真的需要某个"超出克制范围"的动画（比如一个关于"震荡"的概念需要摇晃），在 tweak 对照里跟用户确认过再落回正式 deck。

---

## 5. 常见坑（gotchas，别顺手优化）

- **双 `requestAnimationFrame` 不能省** —— 见 §1.1
- **`.logo-mini` 必须有 `aspect-ratio: 100/110` + `height: auto`** —— 否则 SVG 按 HTML replaced element 规范高度 fallback 成 150px，撑爆 flex 父级
- **SVG path 上的 `paint-order: stroke fill`** —— 见 §3.3，去掉贴纸感就没了
- **封面 / 结束 / 休息页要标 `data-no-chrome="true"`** —— 不然顶部面包屑会穿帮显出 "§0 / "
- **步进 slide 记得同时加 `.stepped` class + `data-steps="K"`** —— 两个缺一不可，JS 里 `classList.contains('stepped')` 是 gate
