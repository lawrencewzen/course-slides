# 设计系统

本文件只讲**品牌身份**。技术骨架（CSS tokens / JS controller / 动画 primitives）全部封装在 `assets/skeleton.html` 里，装配时 verbatim 复用即可。

## 1. 品牌资产（锁死，不能变）

- **主色** `--brand: #1E40FF`；配套浅底 `--brand-soft: #EEF1FF` / `--brand-faint: #F5F7FF`
- **辅色**（火苗渐变，只在 `<symbol id="logo-flame">` 内用）`--flame-1: #FFA92E` / `--flame-2: #EF4D2A` / `--flame-3: #C42138`
- **火苗 logo** `<symbol id="logo-flame">`（skeleton.html 里已完整定义）
- **品牌名** AI Spark
- **Slogan** 始于火花 · 成于实战
- **字体栈** `-apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif` —— 不引外部字体（Fontshare / Google Fonts / 自建 CDN 全禁，课堂离线考虑）

## 2. 非动画类 gotchas

动画相关的坑 → `references/animation-reference.md`。下面是跟排版 / 资源相关的坑：

- **`.logo-mini` 必须有 `aspect-ratio: 100/110` + `height: auto`**：否则 SVG 高度 fallback 成 150px 默认值（HTML replaced element 规范），撑爆 flex 父级
- **SVG 路径上的 `paint-order: stroke fill`**：让白描边画在填充下面得到"贴纸"效果；去掉视觉会变
- **封面 / 休息 / 结束页加 `data-no-chrome="true"`**：JS 切换时不显示顶部面包屑 / 页码，避免"§0 / " 之类穿帮
- **品牌色点缀 ≤10% 是硬底线**：除代码块 `#1a1d24` 和休息页 `--brand-faint` 浅底外，主内容区不要整片刷蓝；蓝色要留给 `eyebrow` / `.accent` / `key` / `strong` 下划线这类强调
