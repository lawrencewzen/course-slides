#!/usr/bin/env python3
"""
course-slides 视觉自检 · headless 浏览器抓像素级溢出

静态 lint.py 只看结构数量；本脚本补上 lint 抓不到的：
- 长标题换行撑破版
- 长 cell 撑宽 / 溢出右边
- 字号 padding 样式叠加后越过 slogan 安全线
- 用户肉眼能看见但结构阈值判不出的"最后一两条显示不到"

用法:
  python3 visual_check.py <deck.html>
  python3 visual_check.py <deck.html> --screenshots          # 写每页截图到 <deck>-check/
  python3 visual_check.py <deck.html> --viewport 1440x900    # 自定视口，默认 1280x720

依赖: playwright
  pip install playwright
  python3 -m playwright install chromium

退出码: 0 干净 / 1 有告警 / 2 运行错误
"""

import argparse
import json
import platform
import re
import subprocess
import sys
from pathlib import Path


def detect_screen_size():
    """返回 (width, height) logical pixels；无法检测返回 None。"""
    system = platform.system()
    if system == "Darwin":
        try:
            out = subprocess.check_output(
                [
                    "osascript",
                    "-e",
                    'tell application "Finder" to get bounds of window of desktop',
                ],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=3,
            ).strip()
            parts = [p.strip() for p in out.split(",")]
            if len(parts) == 4:
                return int(parts[2]), int(parts[3])
        except Exception:
            pass
    try:
        import tkinter as tk

        r = tk.Tk()
        r.withdraw()
        w, h = r.winfo_screenwidth(), r.winfo_screenheight()
        r.destroy()
        return w, h
    except Exception:
        return None


# 控制台捕获的格式化告警 regex（匹配 skeleton.html 里 checkOverflow 输出）
WARN_RE = re.compile(
    r"⚠ slide (?P<idx>\d+) 溢出 slogan 安全线 · 超出 (?P<over>[\d.]+)cqw · 最差元素: (?P<tag>[^·]+)"
)


DEEP_PROBE_JS = r"""
() => {
  // 外部逐页强制激活 + 最大可见态测量，补 controller 的自然态检测
  // 对 .stepped 把所有 .step 打 revealed（模拟讲完最后一步）；
  // 对 .windowed 每一屏 winStage 都量一次，取最糟。
  const slides = [...document.querySelectorAll('.deck .slide')];
  const deck = document.querySelector('.deck');
  if (!deck || !slides.length) return {error: 'no deck'};

  // 结构敏感版式的必备嵌套 selector 清单
  // —— 装配时若漏写嵌套结构，CSS 不命中 → h1 回退 default 字号撑破版 / flex 布局丢失变居中 / 动画不跑
  // 检查方式：只看必备嵌套是否存在（存在 = CSS 有命中机会）
  const STRUCTURE_REQUIRED = {
    cover:   ['.top', '.center', '.center .eyebrow', '.center h1', '.footer'],
    end:     ['.top', '.center', '.center h1', '.footer'],
    divider: ['.center', '.center .num', '.center .label', '.center h1',
              '.center .bridge', '.center .meta-row', '.center .meta-row .pill',
              '.progress', '.progress .ticks'],
    break:   ['.icon', '.label', 'h1', '.duration', '.hint'],
    // flow 页：外层必须 .flow 包 .flow-row（少一层 flex 就会塌），节点要 data-lit-step 才有 autoLightFlow 动画
    'flow-layout': ['.flow', '.flow .flow-row', '.flow-row .flow-node',
                    '.flow-row .flow-node[data-lit-step]'],
  };
  // 用 dataset 标记 flow-layout slide（有 .flow-row 的就是，不靠 class 名判）
  function checkStructure(slide) {
    const missing = [];
    for (const [key, sels] of Object.entries(STRUCTURE_REQUIRED)) {
      const applies = key === 'flow-layout'
        ? !!slide.querySelector('.flow-row, .flow-node')
        : slide.classList.contains(key);
      if (!applies) continue;
      for (const sel of sels) {
        if (!slide.querySelector(sel)) missing.push(`${key} 缺 ${sel}`);
      }
    }
    return missing;
  }

  const origActive = slides.findIndex(s => s.classList.contains('active'));
  const origStages = slides.map(s => ({
    stage: s.dataset.stage,
    winStage: s.dataset.winStage,
    revealed: [...s.querySelectorAll('.step.revealed')].map(x => x),
  }));

  function measure(slide) {
    const dr = deck.getBoundingClientRect();
    const cqw = dr.width / 100;
    const safeBottom = dr.bottom - 3.5 * cqw;
    const safeRight  = dr.right;
    const sel = '.body, .items, .demo-steps, .flow, table, .ascii-box, .quote, ' +
                '.item, .demo-step, .flow-node, h1, .eyebrow, p, thead, tbody, td, th';
    const els = slide.querySelectorAll(sel);
    let bottom = {over: 0, tag: null};
    let right  = {over: 0, tag: null};
    els.forEach(el => {
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) return;
      const ob = r.bottom - safeBottom;
      const orr = r.right - safeRight;
      if (ob > bottom.over) {
        bottom = {over: ob, tag: el.tagName.toLowerCase() + (el.className ? '.' + [...el.classList].join('.') : '')};
      }
      if (orr > right.over) {
        right  = {over: orr, tag: el.tagName.toLowerCase() + (el.className ? '.' + [...el.classList].join('.') : '')};
      }
    });
    return {bottomOverCqw: +(bottom.over / cqw).toFixed(2), bottomTag: bottom.tag,
            rightOverCqw:  +(right.over  / cqw).toFixed(2), rightTag:  right.tag};
  }

  // 稀疏检测：内容外接矩形 vs slide 区 + 字号相对落差
  // 只对有实际内容的版式量（cover / divider / break / end 合理稀疏，跳过）
  const SPARSE_SKIP = ['cover', 'divider', 'break', 'end'];
  function measureFill(slide) {
    if (SPARSE_SKIP.some(c => slide.classList.contains(c))) return null;
    const sr = slide.getBoundingClientRect();
    if (sr.width === 0) return null;
    // 拿 "实质内容" 元素：正文容器 + 要点卡 + 流程节点 + 表格 + 引用 + 标题 + 代码块
    // 排除纯装饰或 chrome：.eyebrow 给算到 top 基准；底部 slogan / 水印在 deck 级不在 slide 内
    const contents = [...slide.querySelectorAll(
      '.body, .items, .demo-steps, .flow, table, .ascii-box, .quote, h1, p, .item, .demo-step, .flow-node, pre, .code'
    )].filter(el => {
      const r = el.getBoundingClientRect();
      return r.width > 0 && r.height > 0;
    });
    if (!contents.length) return null;

    let minL = sr.right, minT = sr.bottom, maxR = sr.left, maxB = sr.top;
    contents.forEach(el => {
      const r = el.getBoundingClientRect();
      if (r.left   < minL) minL = r.left;
      if (r.top    < minT) minT = r.top;
      if (r.right  > maxR) maxR = r.right;
      if (r.bottom > maxB) maxB = r.bottom;
    });
    const contentH = Math.max(0, maxB - minT);
    const contentW = Math.max(0, maxR - minL);
    const verticalFill   = contentH / sr.height;           // 内容高度占 slide 高度
    const horizontalFill = contentW / sr.width;            // 内容宽度占 slide 宽度
    const bottomGapRatio = (sr.bottom - maxB) / sr.height; // 内容底到 slide 底的距离比

    // 字号落差：max h1 vs min p（用 computed font-size，px）
    // 注意：pMin 只看 body 正文 p，不含 .item .desc（item 是卡片结构，字号小是正常的）
    const h1s = [...slide.querySelectorAll('h1')];
    const bodyPs = [...slide.querySelectorAll('.body p, .slide > p')];
    let h1Max = 0, pMin = Infinity;
    h1s.forEach(el => { const fs = parseFloat(getComputedStyle(el).fontSize); if (fs > h1Max) h1Max = fs; });
    bodyPs.forEach(el => {
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) return;
      const fs = parseFloat(getComputedStyle(el).fontSize);
      if (fs > 0 && fs < pMin) pMin = fs;
    });
    const fsRatio = (h1Max > 0 && pMin < Infinity) ? (pMin / h1Max) : null;

    // 检测当前 slide 是否已经用了非 body 版式（points / flow / table / code）
    const hasPointsGrid = !!slide.querySelector('.items, .demo-steps');
    const hasFlow       = !!slide.querySelector('.flow, .flow-row');
    const hasTable      = !!slide.querySelector('table');
    const hasCode       = !!slide.querySelector('pre, .code');

    // "短段落" 只数 body 正文 p —— .item .desc / .flow-node .desc 是卡片结构，不该算
    const shortParas = bodyPs
      .map(el => (el.textContent || '').trim())
      .filter(t => t && t.length <= 40).length;

    // 推荐换版式的 hint：当前是纯 body（没 points/flow/table/code）+ ≥3 条短 p
    let hint = null;
    if (!hasPointsGrid && !hasFlow && !hasTable && !hasCode && shortParas >= 3) {
      hint = `${shortParas} 条短段落（≤40 字）建议换 points 卡片版（.items.two-col 或 compact）`;
    }

    return {
      verticalFill:   +verticalFill.toFixed(2),
      horizontalFill: +horizontalFill.toFixed(2),
      bottomGapRatio: +bottomGapRatio.toFixed(2),
      fsRatio:        fsRatio === null ? null : +fsRatio.toFixed(2),
      shortParas,
      hasPointsGrid,
      hasFlow,
      hasTable,
      hasCode,
      hint,
    };
  }

  const results = [];
  slides.forEach((s, i) => {
    // 强制只此页 active playing；加 no-anim 关掉 transition，让元素直接落到终态再量
    slides.forEach((x, j) => {
      x.classList.toggle('active', j === i);
      if (j === i) { x.classList.add('playing'); x.classList.add('no-anim'); }
      else { x.classList.remove('playing'); x.classList.remove('no-anim'); }
    });

    // 让 stepped 全部展开
    if (s.classList.contains('stepped')) {
      s.querySelectorAll('.step').forEach(st => st.classList.add('revealed'));
    }

    // windowed: 每屏量一次取最糟
    const windows = [...s.querySelectorAll('.windowed')];
    const stagesPerWin = windows.map(c => {
      const K = +(c.dataset.window || '0');
      const N = c.querySelectorAll('.step').length;
      return K > 0 ? Math.ceil(N / K) : 1;
    });
    const maxStages = stagesPerWin.length ? Math.max(...stagesPerWin) : 1;

    let worst = measure(s);
    let worstStage = 1;
    for (let stage = 1; stage <= maxStages; stage++) {
      windows.forEach((c, wi) => {
        const K = +(c.dataset.window || '0');
        const steps = [...c.querySelectorAll('.step')];
        steps.forEach((st, idx) => {
          const sn = idx + 1;
          const inStage = sn > (stage - 1) * K && sn <= stage * K;
          st.classList.toggle('revealed', inStage);
          st.classList.toggle('past', sn <= (stage - 1) * K);
        });
      });
      const m = measure(s);
      const pick = Math.max(m.bottomOverCqw, m.rightOverCqw);
      const curPick = Math.max(worst.bottomOverCqw, worst.rightOverCqw);
      if (pick > curPick) { worst = m; worstStage = stage; }
    }

    const fill = measureFill(s);
    const missingStructure = checkStructure(s);

    results.push({
      idx: i + 1,
      section: s.dataset.section || '',
      name: s.dataset.sectionName || '',
      classes: [...s.classList].filter(c => c !== 'active' && c !== 'playing' && c !== 'no-anim').join(' '),
      worstStage,
      ...worst,
      fill,
      missingStructure,
    });
  });

  // 粗略恢复原状态（不完美，但脚本只用于自检）
  slides.forEach((s, j) => s.classList.toggle('active', j === origActive));
  return {results};
}
"""


def _sparse_fix_options(fill):
    """根据 fill 指标给出机器可读的修法建议，供 skill 自动循环选。"""
    opts = []
    if fill.get("shortParas", 0) >= 3:
        opts.append(
            "switch_to_points_grid"
        )  # body+短 bullet → points.items.two-col / compact
    if fill.get("fsRatio") is not None and fill["fsRatio"] < 0.18:
        opts.append("balance_typography")  # 正文字号调大 / h1 调小
    if fill["verticalFill"] < 0.30 and fill["bottomGapRatio"] > 0.50:
        opts.append("add_content_or_center")  # 加内容 / 压 padding 居中做"一句话 slide"
    if not opts:
        opts.append("manual_review")
    return opts


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("html")
    ap.add_argument(
        "--screenshots", action="store_true", help="写每页截图到 <deck>-check/"
    )
    ap.add_argument(
        "--viewport",
        default="auto",
        help=(
            "视口大小。auto = 跟当前屏幕（推荐，匹配实际播放环境）"
            " / WxH 自定（如 1920x1080）/ 16:9 / 16:10 等比例别名（用当前屏宽对等换）；默认 auto"
        ),
    )
    ap.add_argument(
        "--threshold",
        type=float,
        default=0.3,
        help="溢出告警的最小越界量（cqw），低于此值忽略，默认 0.3",
    )
    ap.add_argument(
        "--sparse-vfill",
        type=float,
        default=0.45,
        help="稀疏告警阈值：内容高度占 slide 高度比 <此值 时告警，默认 0.45",
    )
    ap.add_argument(
        "--sparse-gap",
        type=float,
        default=0.35,
        help="稀疏告警阈值：内容底到 slide 底空白比 >此值 时告警，默认 0.35",
    )
    ap.add_argument(
        "--sparse-fs",
        type=float,
        default=0.18,
        help="稀疏告警阈值：p / h1 字号比 <此值 时告警（默认 0.18，h1 5cqw / p 0.9cqw 即 0.18）",
    )
    ap.add_argument(
        "--no-sparse",
        action="store_true",
        help="关闭稀疏检测，只保留溢出检测",
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="输出 JSON 报告到 stdout（供 skill 循环自改用）",
    )
    args = ap.parse_args()
    if args.no_sparse:
        args.sparse_vfill = -1
        args.sparse_fs = -1

    vp_arg = args.viewport.strip().lower()
    # 预设别名：常见投影 / 线上会议播放端
    PRESETS = {
        "projector": (1920, 1080),  # 1080p 投影仪 / 大屏，线下上课默认
        "zoom": (1280, 720),  # Zoom / Tencent Meeting 共享窗口
        "macbook": (1440, 900),  # MacBook Air M1 默认 "Looks Like"
        "fhd": (1920, 1080),
        "qhd": (2560, 1440),
        "4k": (3840, 2160),
    }
    vp_source = None  # 用于在输出里解释 viewport 来源
    if vp_arg == "auto":
        detected = detect_screen_size()
        if not detected:
            print(
                "⚠ 无法检测当前屏幕 CSS 像素，fallback 到 1440x900",
                file=sys.stderr,
            )
            detected = (1440, 900)
            vp_source = "auto fallback"
        else:
            vp_source = "auto · 当前屏幕 CSS 像素（macOS 扣掉菜单栏）"
        viewport = {"width": detected[0], "height": detected[1]}
    elif vp_arg in PRESETS:
        w, h = PRESETS[vp_arg]
        viewport = {"width": w, "height": h}
        vp_source = f"preset {vp_arg}"
    elif vp_arg in ("16:9", "16:10", "4:3", "21:9"):
        detected = detect_screen_size() or (1440, 900)
        num, den = map(int, vp_arg.split(":"))
        w = detected[0]
        h = int(round(w * den / num))
        viewport = {"width": w, "height": h}
        vp_source = f"按当前屏宽按 {vp_arg} 比例换算"
    else:
        m = re.fullmatch(r"(\d+)x(\d+)", vp_arg)
        if not m:
            print(
                "viewport 格式: auto / WxH / 预设别名（projector / zoom / macbook / fhd / qhd / 4k）/ 比例（16:9 / 16:10 / 4:3 / 21:9）",
                file=sys.stderr,
            )
            return 2
        viewport = {"width": int(m.group(1)), "height": int(m.group(2))}
        vp_source = "自定"

    path = Path(args.html)
    if not path.is_file():
        print(f"❌ 找不到文件: {path}", file=sys.stderr)
        return 2

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "❌ 缺少 playwright。先跑：\n   pip install playwright\n   python3 -m playwright install chromium",
            file=sys.stderr,
        )
        return 2

    console_warns = []  # list of dict {idx, over, tag}

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as e:
            print(
                f"❌ 启动 chromium 失败（可能没装浏览器）:\n   {e}\n"
                f"   跑一下: python3 -m playwright install chromium",
                file=sys.stderr,
            )
            return 2
        context = browser.new_context(viewport=viewport, device_scale_factor=2)
        page = context.new_page()

        def on_console(msg):
            if msg.type != "warning":
                return
            mm = WARN_RE.search(msg.text)
            if mm:
                console_warns.append(
                    {
                        "idx": int(mm.group("idx")),
                        "over": float(mm.group("over")),
                        "tag": mm.group("tag").strip(),
                    }
                )

        page.on("console", on_console)
        page.goto(path.resolve().as_uri())
        page.wait_for_selector(".deck .slide", state="attached")
        page.wait_for_timeout(400)  # 等 controller 初始化

        total = page.evaluate("document.querySelectorAll('.deck .slide').length")
        if not total:
            print("❌ 没找到 .slide", file=sys.stderr)
            browser.close()
            return 2

        # === Pass 1: 自然翻页，让 controller 自己跑 checkOverflow ===
        # 从 slide 1 走到结尾；mash ArrowRight，最多每页 15 次（覆盖最长 .stepped/.windowed）
        for _ in range(total * 15):
            idx = page.evaluate(
                "[...document.querySelectorAll('.deck .slide')].findIndex(s => s.classList.contains('active'))"
            )
            if idx < 0:
                break
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(120)
            new_idx = page.evaluate(
                "[...document.querySelectorAll('.deck .slide')].findIndex(s => s.classList.contains('active'))"
            )
            if new_idx == total - 1:
                # 末页再按几次用完末页 step/window，然后跳出
                for _ in range(10):
                    page.keyboard.press("ArrowRight")
                    page.wait_for_timeout(100)
                break

        # 等所有 RAF 结束
        page.wait_for_timeout(400)

        # === Pass 2: 直接操纵 DOM 做最大可见态深测 ===
        deep = page.evaluate(DEEP_PROBE_JS)

        # === 可选: 截图 ===
        shot_dir = None
        if args.screenshots:
            shot_dir = path.parent / (path.stem + "-check")
            shot_dir.mkdir(exist_ok=True)
            for i in range(1, total + 1):
                page.evaluate(
                    """(i) => {
                    const slides = [...document.querySelectorAll('.deck .slide')];
                    slides.forEach((s, j) => {
                        s.classList.toggle('active', j === i - 1);
                        if (j === i - 1) { s.classList.add('playing'); s.classList.add('no-anim'); }
                        else { s.classList.remove('playing'); s.classList.remove('no-anim'); }
                    });
                    const active = slides[i - 1];
                    if (active.classList.contains('stepped')) {
                        active.querySelectorAll('.step').forEach(st => st.classList.add('revealed'));
                    }
                    // windowed: 展开第一屏
                    active.querySelectorAll('.windowed').forEach(c => {
                        const K = +(c.dataset.window || '0');
                        [...c.querySelectorAll('.step')].forEach((st, idx) => {
                            st.classList.toggle('revealed', idx < K);
                            st.classList.remove('past');
                        });
                    });
                }""",
                    i,
                )
                page.wait_for_timeout(150)
                deck = page.query_selector(".deck")
                if deck:
                    deck.screenshot(path=str(shot_dir / f"slide-{i:02d}.png"))

        browser.close()

    # === 汇总 ===
    # dedupe console warns by slide idx, 保留最大 over
    by_idx = {}
    for w in console_warns:
        if w["idx"] not in by_idx or w["over"] > by_idx[w["idx"]]["over"]:
            by_idx[w["idx"]] = w

    deep_results = (deep or {}).get("results", [])
    deep_bad = [
        r
        for r in deep_results
        if r.get("bottomOverCqw", 0) > args.threshold
        or r.get("rightOverCqw", 0) > args.threshold
    ]

    # 稀疏告警：只在有 actionable 信号时报（避免把正常 body 底部留白误杀）
    # 任一条件成立即报：
    #   (a) fsRatio 异常小：h1 / 正文字号比悬殊（仅 body 版式检测，points/flow/table 的卡片小字正常）
    #   (b) 短段落并列（≥3 条 ≤40 字）+ verticalFill 小 + 底部大片空
    #       —— 只在当前**不是** points/flow/table/code 版式时报（已经是 points 就别再建议换了）
    #   (c) 极端稀疏：verticalFill < 0.30 且 bottomGap > 0.50
    sparse_bad = []
    for r in deep_results:
        f = r.get("fill")
        if not f:
            continue
        non_body_layout = (
            f.get("hasPointsGrid")
            or f.get("hasFlow")
            or f.get("hasTable")
            or f.get("hasCode")
        )
        triggers = []
        if (
            f.get("fsRatio") is not None
            and f["fsRatio"] < args.sparse_fs
            and not non_body_layout
        ):
            triggers.append(
                f"正文 / h1 字号比 {f['fsRatio']}（<{args.sparse_fs}，h1 过大或正文过小）"
            )
        if (
            f.get("shortParas", 0) >= 3
            and f["verticalFill"] < args.sparse_vfill
            and f["bottomGapRatio"] > args.sparse_gap
            and not non_body_layout
        ):
            triggers.append(
                f"{f['shortParas']} 条短段落并列 · 内容只占 {int(f['verticalFill'] * 100)}% 高度 · 底部空 {int(f['bottomGapRatio'] * 100)}%"
            )
        if f["verticalFill"] < 0.30 and f["bottomGapRatio"] > 0.50:
            triggers.append(
                f"整页明显空 · 内容只占 {int(f['verticalFill'] * 100)}% 高度 · 底部空 {int(f['bottomGapRatio'] * 100)}%"
            )
        if triggers:
            sparse_bad.append((r, triggers))

    # 结构告警：cover / divider / break / end 缺必备嵌套元素
    structure_bad = [r for r in deep_results if r.get("missingStructure")]

    # === JSON 输出（供 skill 循环自改用）===
    if args.json:
        report = {
            "file": str(path),
            "total_slides": total,
            "viewport": {"width": viewport["width"], "height": viewport["height"]},
            "clean": not (by_idx or deep_bad or sparse_bad or structure_bad),
            "console_warns": [
                {
                    "slide": idx,
                    "overCqw": by_idx[idx]["over"],
                    "tag": by_idx[idx]["tag"],
                }
                for idx in sorted(by_idx.keys())
            ],
            "overflow": [
                {
                    "slide": r["idx"],
                    "section": r["section"],
                    "section_name": r["name"],
                    "classes": r["classes"],
                    "win_stage": r["worstStage"],
                    "bottom_over_cqw": r["bottomOverCqw"],
                    "bottom_tag": r["bottomTag"],
                    "right_over_cqw": r["rightOverCqw"],
                    "right_tag": r["rightTag"],
                    "fix_options": [
                        "split_page",
                        "windowed_carousel",
                        "reduce_items",
                        "shrink_headings",
                    ],
                }
                for r in deep_bad
            ],
            "sparse": [
                {
                    "slide": r["idx"],
                    "section": r["section"],
                    "section_name": r["name"],
                    "classes": r["classes"],
                    "vertical_fill": r["fill"]["verticalFill"],
                    "bottom_gap_ratio": r["fill"]["bottomGapRatio"],
                    "fs_ratio": r["fill"].get("fsRatio"),
                    "short_paras": r["fill"].get("shortParas", 0),
                    "triggers": triggers,
                    "suggestion": r["fill"].get("hint"),
                    "fix_options": _sparse_fix_options(r["fill"]),
                }
                for r, triggers in sparse_bad
            ],
            "structure": [
                {
                    "slide": r["idx"],
                    "section": r["section"],
                    "section_name": r["name"],
                    "classes": r["classes"],
                    "missing": r["missingStructure"],
                    "fix_options": ["rewrite_layout_from_reference"],
                }
                for r in structure_bad
            ],
            "screenshot_dir": str(shot_dir) if shot_dir else None,
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["clean"] else 1

    print(f"course-slides visual-check · {path}")
    print(
        f"  共 {total} 页 · viewport {viewport['width']}×{viewport['height']}"
        + (f"（{vp_source}）" if vp_source else "")
    )
    print(
        f"  结构告警 {len(structure_bad)} 页 · controller 自然告警 {len(by_idx)} 页 · 溢出深测 {len(deep_bad)} 页 · 稀疏深测 {len(sparse_bad)} 页"
    )
    if shot_dir:
        print(f"  截图目录: {shot_dir}")
    print()

    if not by_idx and not deep_bad and not sparse_bad and not structure_bad:
        print("✅ 视觉干净，无结构缺失 / 像素级溢出 / 稀疏 / 字号异常。")
        return 0

    if structure_bad:
        print("⚠ 结构告警（版式必备嵌套缺失 · CSS 不命中会撑破版）:")
        for r in structure_bad:
            sec = f"§{r['section']}" if r["section"] and r["section"] != "0" else "·"
            print(f"   slide {r['idx']:>2}  {sec}  {r['name']} [{r['classes']}]")
            for m in r["missingStructure"]:
                print(f"     · {m}")
        print("   → 照 assets/layouts/<layout>.html 的嵌套结构重写该页\n")

    if by_idx:
        print("⚠ controller 自然翻页告警（用户实际播放时会在 console 看到）:")
        for idx in sorted(by_idx.keys()):
            w = by_idx[idx]
            print(f"   slide {idx:>2} · 底部超 {w['over']}cqw · {w['tag']}")
        print()

    if deep_bad:
        print("⚠ 溢出告警（最大可见态 · 底部越线 + 右侧撑宽）:")
        for r in deep_bad:
            sec = f"§{r['section']}" if r["section"] and r["section"] != "0" else "·"
            print(
                f"   slide {r['idx']:>2}  {sec}  {r['name']} [{r['classes']}]  win-stage={r['worstStage']}"
            )
            if r["bottomOverCqw"] > args.threshold:
                print(f"     · 底部越 {r['bottomOverCqw']}cqw · {r['bottomTag']}")
            if r["rightOverCqw"] > args.threshold:
                print(f"     · 右侧越 {r['rightOverCqw']}cqw · {r['rightTag']}")
        print(
            "   → C 拆页（推荐）/ A 开 data-window / 删除多余 item / 降 eyebrow 或 h1 字号\n"
        )

    if sparse_bad:
        print("⚠ 稀疏告警（内容挤在一角 / 字号失衡 / 版式可能选错）:")
        for r, triggers in sparse_bad:
            sec = f"§{r['section']}" if r["section"] and r["section"] != "0" else "·"
            f = r["fill"]
            print(f"   slide {r['idx']:>2}  {sec}  {r['name']} [{r['classes']}]")
            for t in triggers:
                print(f"     · {t}")
            if f.get("hint"):
                print(f"     → 建议：{f['hint']}")
            else:
                print(
                    "     → 加内容充实页面 / 加大正文字号 / 换稀疏友好版式（如 quote 居中）"
                )
        print("   注意：不自动改版式；用户确认后走 tweak 对照流程重排该页\n")

    return 1


if __name__ == "__main__":
    sys.exit(main())
