#!/usr/bin/env python3
"""
course-slides 静态密度 linter · 无外部依赖

用法: python3 lint.py <deck.html>
退出码: 0 = 干净；1 = 有告警

按结构阈值扫超量容器，报告行号 / 超出量 / 建议。捕不到像素级
（长标题换行、长 cell 撑宽）这类溢出——那需要 headless 浏览器。
"""

import json
import sys
import re
from html.parser import HTMLParser


THRESHOLDS = {
    # (container_selector, child_selector, max_count, hint)
    "points_single": (
        ".points .items (not two-col / compact)",
        ".item",
        5,
        'C 拆成 3+3 / 3+4，或 A 开 data-window="3"',
    ),
    "points_two": (
        ".points .items.two-col",
        ".item",
        6,
        'C 拆成 4+4 两页，或 A 开 data-window="4"',
    ),
    "points_cmp": (
        ".points .items.compact",
        ".item",
        6,
        "已 compact 仍超 6 条 → C 拆页",
    ),
    "demo_steps": (
        ".demo-steps",
        ".demo-step",
        5,
        'C 拆成 3+3，或 A 开 data-window="3"',
    ),
    "table_rows": (
        ".table-page tbody",
        "tr (exc. .total)",
        6,
        'C 先删列再拆行，或 A 开 data-window="4"（tbody）',
    ),
    "body_paras": (".body", "> p", 6, "C 拆成 X（1/2）/ X（2/2）"),
    "flow_nodes": (
        ".flow-row",
        ".flow-node",
        6,
        "flow 超 6 节点考虑改竖向布局或拆阶段",
    ),
}


class SlideScanner(HTMLParser):
    """逐 slide 拆块，收集每个 slide 内的结构性计数。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.slides = []  # list of dict: {idx, section, name, classes, issues}
        self.cur = None  # current slide dict
        self.cur_depth = None  # depth at which current slide opened
        self.stack = []  # stack of (tag, classes) for counting children
        # counters per slide, reset on slide enter
        self._reset_counters()

    def _reset_counters(self):
        self.counters = {
            "points_items": [],  # list of .items containers: {variant, count, has_window}
            "demo_steps": [],  # list of .demo-steps containers
            "tbody_rows": [],  # list of tbody containers
            "body_paras": [],  # list of .body containers
            "flow_rows": [],  # list of .flow-row containers
        }
        self._open_stack = []  # stack of active counting containers

    def handle_starttag(self, tag, attrs):
        attrs_d = dict(attrs)
        classes = set((attrs_d.get("class") or "").split())
        self.depth += 1

        # Enter new slide: top-level div inside .deck with class="slide ..."
        if tag == "div" and "slide" in classes and self.cur is None:
            skip_raw = attrs_d.get("data-lint-skip", "") or ""
            self.cur = {
                "idx": len(self.slides) + 1,
                "section": attrs_d.get("data-section", "?"),
                "name": attrs_d.get("data-section-name", ""),
                "classes": classes,
                "issues": [],
                "skip": set(s.strip() for s in skip_raw.split(",") if s.strip()),
            }
            self.cur_depth = self.depth
            self._reset_counters()
            return

        if self.cur is None:
            return

        # Counting containers — push onto open stack
        if tag == "div" and "items" in classes:
            variant = (
                "two"
                if "two-col" in classes
                else ("compact" if "compact" in classes else "single")
            )
            has_window = "windowed" in classes
            entry = {
                "kind": "points_items",
                "variant": variant,
                "count": 0,
                "has_window": has_window,
            }
            self.counters["points_items"].append(entry)
            self._open_stack.append(entry)
        elif tag == "div" and "demo-steps" in classes:
            has_window = "windowed" in classes
            entry = {"kind": "demo_steps", "count": 0, "has_window": has_window}
            self.counters["demo_steps"].append(entry)
            self._open_stack.append(entry)
        elif tag == "tbody":
            entry = {"kind": "tbody_rows", "count": 0, "has_window": False}
            self.counters["tbody_rows"].append(entry)
            self._open_stack.append(entry)
        elif tag == "div" and "body" in classes:
            entry = {"kind": "body_paras", "count": 0, "has_window": False}
            self.counters["body_paras"].append(entry)
            self._open_stack.append(entry)
        elif tag == "div" and "flow-row" in classes:
            entry = {"kind": "flow_rows", "count": 0, "has_window": False}
            self.counters["flow_rows"].append(entry)
            self._open_stack.append(entry)

        # Count children of the innermost applicable container
        if self._open_stack:
            top = self._open_stack[-1]
            kind = top["kind"]
            if kind == "points_items" and tag == "div" and "item" in classes:
                top["count"] += 1
            elif kind == "demo_steps" and tag == "div" and "demo-step" in classes:
                top["count"] += 1
            elif kind == "tbody_rows" and tag == "tr" and "total" not in classes:
                top["count"] += 1
            elif kind == "body_paras" and tag == "p":
                # only count direct children — approximation: count all <p>
                top["count"] += 1
            elif kind == "flow_rows" and tag == "div" and "flow-node" in classes:
                top["count"] += 1

    def handle_endtag(self, tag):
        # Pop counting container when its div/tbody closes
        if self._open_stack:
            # crude: pop when tag matches kind-expected closing
            top = self._open_stack[-1]
            if (top["kind"] == "tbody_rows" and tag == "tbody") or (
                top["kind"] != "tbody_rows" and tag == "div"
            ):
                # only pop if we're at the depth where this container opened
                # we don't track per-container depth; use heuristic: any matching close pops.
                # good enough because containers don't self-nest in this deck.
                self._open_stack.pop()

        # End of slide
        if self.cur is not None and self.depth == self.cur_depth and tag == "div":
            self._finalize_slide()
            self.cur = None
            self.cur_depth = None

        self.depth -= 1

    def _finalize_slide(self):
        c = self.counters
        skip = self.cur["skip"]

        def add(kind, count):
            if kind not in skip:
                self.cur["issues"].append((kind, count))

        for items in c["points_items"]:
            if items["has_window"]:
                continue
            if items["variant"] == "single" and items["count"] > 5:
                add("points_single", items["count"])
            elif items["variant"] == "two" and items["count"] > 6:
                add("points_two", items["count"])
            elif items["variant"] == "compact" and items["count"] > 6:
                add("points_cmp", items["count"])

        for ds in c["demo_steps"]:
            if ds["has_window"]:
                continue
            if ds["count"] > 5:
                add("demo_steps", ds["count"])

        for tb in c["tbody_rows"]:
            if tb["count"] > 6:
                add("table_rows", tb["count"])

        for b in c["body_paras"]:
            if b["count"] > 6:
                add("body_paras", b["count"])

        for fr in c["flow_rows"]:
            if fr["count"] > 6:
                add("flow_nodes", fr["count"])

        self.slides.append(self.cur)


KIND_FIX_OPTIONS = {
    "points_single": ["split_page", "windowed_carousel"],
    "points_two": ["split_page", "windowed_carousel"],
    "points_cmp": ["split_page"],
    "demo_steps": ["split_page", "windowed_carousel"],
    "table_rows": ["drop_columns", "split_page", "windowed_carousel"],
    "body_paras": ["split_page"],
    "flow_nodes": ["vertical_layout", "split_phases"],
}


def main():
    args = [a for a in sys.argv[1:] if a]
    want_json = "--json" in args
    args = [a for a in args if a != "--json"]
    if len(args) != 1:
        print("usage: lint.py <deck.html> [--json]", file=sys.stderr)
        sys.exit(2)

    path = args[0]
    with open(path, encoding="utf-8") as f:
        html = f.read()

    # 只扫 .deck 内（跳过 head/style 里可能的伪 div）
    m = re.search(
        r'<div class="deck">(.*?)\n</div>\s*(?:<!-- end deck -->)?\s*(?=<div class="notes"|<div class="hotkey-help"|<script)',
        html,
        re.DOTALL,
    )
    body = m.group(1) if m else html

    scanner = SlideScanner()
    scanner.feed(body)

    total = len(scanner.slides)
    bad = [s for s in scanner.slides if s["issues"]]

    if want_json:
        report = {
            "file": path,
            "total_slides": total,
            "clean": not bad,
            "issues": [
                {
                    "slide": s["idx"],
                    "section": s["section"],
                    "section_name": s["name"],
                    "violations": [
                        {
                            "kind": kind,
                            "count": count,
                            "threshold": THRESHOLDS[kind][2],
                            "container": THRESHOLDS[kind][0],
                            "hint": THRESHOLDS[kind][3],
                            "fix_options": KIND_FIX_OPTIONS.get(
                                kind, ["manual_review"]
                            ),
                        }
                        for kind, count in s["issues"]
                    ],
                }
                for s in bad
            ],
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if not bad else 1

    print(f"course-slides lint · {path}")
    print(f"  共 {total} 页，{len(bad)} 页超量\n")

    if not bad:
        print("✅ 干净，无结构性超量。")
        return 0

    for s in bad:
        sec = f"§{s['section']}" if s["section"] != "0" else "·"
        print(f"⚠ slide {s['idx']:>2}  {sec}  {s['name']}")
        for kind, count in s["issues"]:
            container, child, thresh, hint = THRESHOLDS[kind]
            print(f"     {container}  {child}  {count} > {thresh}")
            print(f"     → {hint}")
        print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
