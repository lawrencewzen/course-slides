#!/usr/bin/env python3
"""
course-slides PDF 导出 · headless Chromium 逐页截图拼 PDF

跟 visual_check.py 用同一套 DOM 技巧（强制激活 + 关动画 + 展开 stepped/windowed），
保证每页截到的是"最大可见态"：stepped 的所有 step 展开、windowed 的首屏。

用法:
  python3 export_pdf.py <deck.html>                        # 默认 2560×1440 × 3x 高清（打印级）
  python3 export_pdf.py <deck.html> -o custom.pdf
  python3 export_pdf.py <deck.html> --compact              # 1280×720 × 3x 省体积（群里发）
  python3 export_pdf.py <deck.html> --viewport projector   # 1920×1080 FHD
  python3 export_pdf.py <deck.html> --viewport 4k          # 3840×2160 4K
  python3 export_pdf.py <deck.html> --viewport auto        # 跟当前屏
  python3 export_pdf.py <deck.html> --scale 2              # 降采样（默认 3x）
  python3 export_pdf.py <deck.html> --windowed-all         # windowed 页导所有屏（默认只导首屏）

依赖: playwright + Pillow
  pip install playwright Pillow
  python3 -m playwright install chromium

退出码: 0 成功 / 2 运行错误
"""

import argparse
import io
import platform
import re
import subprocess
import sys
from pathlib import Path


PRESETS = {
    "projector": (1920, 1080),
    "fhd": (1920, 1080),
    "qhd": (2560, 1440),
    "4k": (3840, 2160),
    "zoom": (1280, 720),
    "compact": (1280, 720),
    "macbook": (1440, 900),
}


def detect_screen_size():
    if platform.system() == "Darwin":
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


# 强制激活某页 + 最大可见态（no-anim 关过渡，stepped 全展开，windowed 展某屏）
FORCE_STAGE_JS = r"""
(args) => {
  const { idx, winStage } = args;
  const slides = [...document.querySelectorAll('.deck .slide')];
  if (idx < 0 || idx >= slides.length) return false;
  slides.forEach((s, j) => {
    s.classList.toggle('active', j === idx);
    if (j === idx) { s.classList.add('playing'); s.classList.add('no-anim'); }
    else { s.classList.remove('playing'); s.classList.remove('no-anim'); }
  });
  const active = slides[idx];
  if (active.classList.contains('stepped')) {
    active.querySelectorAll('.step').forEach(st => st.classList.add('revealed'));
  }
  active.querySelectorAll('.windowed').forEach(c => {
    const K = +(c.dataset.window || '0') || 1;
    const steps = [...c.querySelectorAll('.step')];
    steps.forEach((st, i) => {
      const sn = i + 1;
      const inStage = sn > (winStage - 1) * K && sn <= winStage * K;
      st.classList.toggle('revealed', inStage);
      st.classList.toggle('past', sn <= (winStage - 1) * K);
    });
  });
  // 用 data-lit-step 的 flow 节点全点亮（autoLightFlow 在 no-anim 下不跑）
  active.querySelectorAll('[data-lit-step]').forEach(el => el.classList.add('lit'));
  return true;
}
"""


GET_WIN_STAGES_JS = r"""
(idx) => {
  const slides = [...document.querySelectorAll('.deck .slide')];
  const active = slides[idx];
  if (!active) return 1;
  const windows = [...active.querySelectorAll('.windowed')];
  if (!windows.length) return 1;
  const stages = windows.map(c => {
    const K = +(c.dataset.window || '0') || 1;
    const N = c.querySelectorAll('.step').length;
    return K > 0 ? Math.ceil(N / K) : 1;
  });
  return Math.max(...stages, 1);
}
"""


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("html")
    ap.add_argument("-o", "--output", help="输出 PDF 路径；默认 <deck>.pdf 同目录")
    ap.add_argument(
        "--viewport",
        default="qhd",
        help=(
            "视口大小。qhd=2560×1440（默认，打印 / 4K 屏锐利）/ projector=1920×1080 / "
            "compact=1280×720 / 4k / auto（跟当前屏）/ WxH 自定"
        ),
    )
    ap.add_argument(
        "--compact",
        action="store_true",
        help="便捷 flag，等同 --viewport compact（1280x720 小体积）",
    )
    ap.add_argument(
        "--scale",
        type=float,
        default=3.0,
        help="设备缩放倍数（1-3，默认 3 为高清打印级；1 或 2 文件更小但字会略软）",
    )
    ap.add_argument(
        "--windowed-all",
        action="store_true",
        help=".windowed 轮播页是否每屏都导出为独立 PDF 页（默认只导首屏）",
    )
    args = ap.parse_args()

    # 视口解析
    vp_arg = "compact" if args.compact else args.viewport.strip().lower()
    if vp_arg == "auto":
        detected = detect_screen_size() or (1920, 1080)
        viewport = {"width": detected[0], "height": detected[1]}
    elif vp_arg in PRESETS:
        w, h = PRESETS[vp_arg]
        viewport = {"width": w, "height": h}
    else:
        m = re.fullmatch(r"(\d+)x(\d+)", vp_arg)
        if not m:
            print(
                "viewport 格式: projector / compact / qhd / 4k / auto / WxH",
                file=sys.stderr,
            )
            return 2
        viewport = {"width": int(m.group(1)), "height": int(m.group(2))}

    scale = max(1.0, min(3.0, args.scale))

    path = Path(args.html)
    if not path.is_file():
        print(f"❌ 找不到文件: {path}", file=sys.stderr)
        return 2
    out_path = Path(args.output) if args.output else path.with_suffix(".pdf")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "❌ 缺少 playwright：\n   pip install playwright\n   python3 -m playwright install chromium",
            file=sys.stderr,
        )
        return 2
    try:
        from PIL import Image
    except ImportError:
        print("❌ 缺少 Pillow：\n   pip install Pillow", file=sys.stderr)
        return 2

    print(f"course-slides export-pdf · {path}")
    print(f"  viewport {viewport['width']}×{viewport['height']} · scale {scale}x")

    png_buffers = []  # list of bytes
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as e:
            print(f"❌ 启动 chromium 失败：{e}", file=sys.stderr)
            print("   跑一下: python3 -m playwright install chromium", file=sys.stderr)
            return 2
        context = browser.new_context(viewport=viewport, device_scale_factor=scale)
        page = context.new_page()
        page.goto(path.resolve().as_uri())
        page.wait_for_selector(".deck .slide", state="attached")
        page.wait_for_timeout(400)

        total = page.evaluate("document.querySelectorAll('.deck .slide').length")
        if not total:
            print("❌ 没找到 .slide", file=sys.stderr)
            browser.close()
            return 2

        print(f"  共 {total} 页，正在导出…")

        for i in range(total):
            max_stages = page.evaluate(GET_WIN_STAGES_JS, i) if args.windowed_all else 1
            for winStage in range(1, max_stages + 1):
                page.evaluate(FORCE_STAGE_JS, {"idx": i, "winStage": winStage})
                page.wait_for_timeout(120)
                deck = page.query_selector(".deck")
                if not deck:
                    continue
                png = deck.screenshot(type="png")
                png_buffers.append(png)
            stage_hint = f" ({max_stages} 屏)" if max_stages > 1 else ""
            print(f"  slide {i + 1:>2}/{total}{stage_hint}")

        browser.close()

    if not png_buffers:
        print("❌ 没产出任何截图", file=sys.stderr)
        return 2

    # 拼 PDF：PNG → RGB → multi-page PDF
    print(f"  拼装 {len(png_buffers)} 页 → PDF…")
    imgs = []
    for buf in png_buffers:
        img = Image.open(io.BytesIO(buf))
        if img.mode != "RGB":
            img = img.convert("RGB")
        imgs.append(img)

    imgs[0].save(
        str(out_path),
        save_all=True,
        append_images=imgs[1:],
        format="PDF",
        resolution=150.0,
    )
    size_kb = out_path.stat().st_size / 1024
    size_str = f"{size_kb:.0f} KB" if size_kb < 1024 else f"{size_kb / 1024:.1f} MB"
    print(f"\n✅ 导出完成: {out_path}  ({size_str} · {len(png_buffers)} 页)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
