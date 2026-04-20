# 设计系统

## 1. 品牌资产（不能变）

- **主色** `--brand: #1E40FF`；配套 `--brand-soft`、`--brand-faint` 浅底
- **火苗 logo** `<symbol id="logo-flame">`
- **品牌名** AI Spark
- **Slogan** 始于火花 · 成于实战

## 2. 关键技术技巧（3 个）

以下 3 个技巧的完整 CSS / JS 实现都在 `assets/final-deck-example.html` 里，装配时照搬即可，不要自己重写。

1. **重播动画 reset**：必须用 `no-anim` class + 双 `requestAnimationFrame`，单层 reflow 不够
2. **步进 reveal**：`data-steps` + `data-stage` + `data-step` 配合 JS 的 `.revealed` class
3. **slide 切换**：单 `.deck` 容器 + 多 `.slide` absolute 定位 + opacity 切换；`.active` 切换时复用重播 reset 触发动画

## 3. Gotchas（反直觉陷阱，不要"顺手优化"掉）

- **双 `requestAnimationFrame` 不能省**：单层会被浏览器把"恢复 transition"和"加 playing"合并到同一帧，动画不播
- **`.logo-mini` 必须有 `aspect-ratio: 100/110` + `height: auto`**：否则 SVG 高度 fallback 成 150px 默认值（HTML replaced element 规范），撑爆 flex 父级
- **SVG 路径上的 `paint-order: stroke fill`**：让白描边画在填充下面得到"贴纸"效果；去掉视觉会变
- **允许的"非克制"动画例外**（SKILL.md 视觉底线第 2 条之外的合法例外）：
  - 流程图箭头亮起后的"流光"（`@keyframes flow-light`，1.4s linear infinite，作 UI 反馈）
  - 标题局部背景的"荧光笔"扫过（淡淡 `--brand-soft` 底，不闪不动）
- **Chrome 可见性**：`.deck-top.visible` 切换；封面 / 休息 / 结束页加 `data-no-chrome`，JS 切换时不显示 chrome
