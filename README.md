# course-slides

> Turn Markdown lecture notes into a single-file HTML slide deck — on-brand AI Spark, Keynote-restrained, ready to project.

A [Claude Code Skill](https://docs.claude.com/en/docs/claude-code/skills) that converts a Markdown source (lecture / tutorial / tech talk / internal doc) into a single `.html` file you can actually project and present from — with navigation, step reveals, speaker notes, a time bar, and keyboard shortcuts.

Built for 2–3 hour single-presenter lectures, bootcamps, and internal deep-dive sessions, with the **AI Spark** brand identity baked in.

## What you get

- **One file, no build step** — pure HTML + CSS + JS, double-click to open
- **Presenter-ready** — arrow keys / space to advance, `N` for speaker notes, time bar across the bottom
- **On-brand** — white background, AI Spark blue accent, flame logo, system fonts; no framework, no external fonts
- **Restrained animations** — Apple-Keynote-style fade-and-rise, 0.85s ease; no bounce or spin
- **Layout at the model's discretion** — per-page layout chosen from the content, not a fixed template

## Brand: AI Spark

The skill is built around AI Spark's identity — it's the brand the final deck ships with.

| Asset | Value |
|---|---|
| Name | AI Spark |
| Primary color | `#1E40FF` (CSS variable `--brand`) |
| Slogan | 始于火花 · 成于实战 |
| Logo | 火苗 (flame) SVG, defined once as `<symbol id="logo-flame">` |

## How it works

1. **Parse** — read the Markdown, normalize into sections / timings / speaker notes via `references/source-schema.md`. Missing fields degrade gracefully (no speaker notes → hide that panel; no timings → hide the time bar).
2. **Skeleton** — load `assets/final-deck-example.html` as the technical donor: CSS tokens, JS controller, deck chrome, flame logo, speaker notes panel, time bar, keyboard bindings — reused verbatim.
3. **Assemble** — generate one divider + N content slides per section. Per-slide layout is chosen by the model from the section's content, subject to 4 visual guardrails (see `SKILL.md`).
4. **Output** — write `<source>-PPT.html` alongside the source; open in browser for review.

## Install

Works with both **Claude Code** and **OpenAI Codex CLI** — they use the same `SKILL.md` format.

```bash
git clone https://github.com/lawrencewzen/course-slides.git
cd course-slides
./install.sh
```

By default the script auto-detects which agents you have installed (`~/.claude/` and/or `~/.codex/`) and symlinks this repo into the matching skills directory:

- `~/.claude/skills/course-slides/` — for Claude Code
- `~/.codex/skills/course-slides/` — for Codex CLI

Flags if you want one side only:

```bash
./install.sh --claude     # Claude Code only
./install.sh --codex      # Codex only
./install.sh --both       # force both (creates parent dir if missing)
```

If the target path already exists as a real directory, it's moved to a timestamped backup. If it's an old symlink, you'll be asked before it's replaced.

Restart your agent (or start a new session) to pick up the skill. Then, in any project with a Markdown lecture, say *"把这份讲义做成 PPT"* — the skill triggers automatically.

### Uninstall

```bash
rm ~/.claude/skills/course-slides   # Claude Code
rm ~/.codex/skills/course-slides    # Codex
```

(Both are symlinks — removing them doesn't delete the repo.)

## What's in here

```
course-slides/
├── SKILL.md                       ← skill definition loaded by Claude Code / Codex
├── references/
│   ├── source-schema.md           ← Markdown → structured schema rules + graceful degradation
│   └── design-system.md           ← brand assets + 3 key technical techniques
└── assets/
    └── final-deck-example.html    ← technical donor + on-brand reference deck (AI Spark 04)
```

## Input format

Your Markdown should include:

- Section markers (any of `## §1 Intro` / `## 一、引入` / plain `## Intro` all work)
- Optional per-section timing (`· 5min`) — shows up as a pill and wires the time bar
- Optional presenter-side content (`讲解策略：…` / `跟学员说：…`) — shows up in the speaker notes panel
- Bullets, tables, code blocks, or flow diagrams inside each section

Fields are detected semantically — no fixed template. Missing any of the optional fields just disables the matching UI (not a hard error).

## Post-assembly validation

Two scripts close the loop so content doesn't silently spill off-screen:

```bash
# 1. Structural density lint — zero-dependency, fast
python3 assets/lint.py <source>-PPT.html

# 2. Pixel-level visual check — catches overflow lint can't see
pip install playwright && python3 -m playwright install chromium   # one-time
python3 assets/visual_check.py <source>-PPT.html
python3 assets/visual_check.py <source>-PPT.html --screenshots     # dump PNG per slide
```

`lint.py` flags over-stuffed containers by structural count; `visual_check.py` boots headless Chromium, walks through every slide, captures the controller's console warnings, and runs a deeper probe that catches right-side overflow the natural-navigation pass misses. Both should exit clean before you ship.

## Design constraints (non-negotiable)

| Aspect | Rule |
|---|---|
| Palette | White background + brand color as ≤10% accent; exceptions: break slide `--brand-faint`, code block `#1a1d24` |
| Animation | Fade + slight rise, 0.85s ease. No bounce, spin, or large translation |
| Fonts | System stack (PingFang SC / Hiragino / Microsoft YaHei). No web fonts |
| Framework | None — no reveal.js, no Slidev, no Tailwind CDN |
| Sizing | Everything in `cqw` (container query units) so text scales with slide |

Rationale: the lecture experience should feel calm and native. No cognitive tax on the audience parsing a busy color palette.

## License

MIT
