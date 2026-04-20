# course-deck

> Turn Markdown lecture notes into a single-file HTML slide deck — Keynote-style, interview-driven, no surprises.

A [Claude Code Skill](https://docs.claude.com/en/docs/claude-code/skills) that converts a Markdown lecture outline (with sections, timings, and "what to say" notes) into a single `.html` file you can actually project and present from — with navigation, step reveals, speaker notes, a time bar, and keyboard shortcuts.

Built for 2–3 hour single-presenter lectures, bootcamps, and internal deep-dive sessions.

## What you get

- **One file, no build step** — pure HTML + CSS + JS, double-click to open
- **Presenter-ready** — arrow keys / space to advance, `N` for speaker notes, time bar across the bottom
- **Restrained by default** — white background, brand accent ≤10%, Apple-Keynote-style fade-and-rise animations (no bouncing, no spinning)
- **Deterministic flow** — a 12-question interview locks design decisions before any HTML is written, so you don't get surprise typography
- **4 rounds of playground** — cover, divider, content, components each rendered as side-by-side candidates you pick from, so the final deck matches your taste

## How it works

The skill enforces a strict four-phase workflow:

1. **Interview** — 12 decisions across 3 groups (structure, components, presenter aids)
2. **Brand lock** — default AI Spark identity or swap in your own logo / hex / slogan
3. **Playground ×4** — `01-cover`, `02-divider`, `03-content-pages`, `04-components`, each as a side-by-side candidate page
4. **Assembly** — read the Markdown, generate one divider + N content pages per section, drop into the proven deck shell

Typical outcome: 9-section lecture → ~36 slides in ~30 minutes of interaction.

## Install

```bash
git clone https://github.com/lawrencewzen/course-deck.git
cd course-deck
./install.sh
```

The script symlinks this repo into `~/.claude/skills/course-deck/`. If that path already exists as a real directory, it gets moved to a timestamped backup. If it's an old symlink, you'll be asked before it's replaced.

Restart Claude Code (or start a new session) to pick up the skill. Then, in any project with a Markdown lecture, say *"把这份讲义做成 PPT"* — the skill triggers automatically.

### Uninstall

```bash
rm ~/.claude/skills/course-deck
```

(It's a symlink — removing it doesn't delete the repo.)

## What's in here

```
course-deck/
├── SKILL.md                       ← skill definition loaded by Claude Code
├── references/
│   ├── design-system.md           ← colors, animation, units, key techniques
│   ├── interview-script.md        ← 12-question interview with recommended answers
│   ├── slide-templates.md         ← HTML skeletons for 6 slide types
│   └── components.md              ← HTML for tree / flow / compare / code components
└── assets/
    ├── playground-templates/      ← seed files for each of the 4 playground rounds
    └── final-deck-example.html    ← reference final deck (AI Spark 04)
```

## Input format

Your Markdown should include:

- Section markers (`## §1 Intro` or `## 一、引入`)
- Per-section timing (`· 5min`)
- Presenter-side content (`讲解策略：…` or `跟学员说：…`)
- Bullets, tables, or flow diagrams inside each section

The clearer the structure, the less back-and-forth during interview.

## Design constraints (non-negotiable)

| Aspect | Rule |
|---|---|
| Palette | White background + brand color as ≤10% accent |
| Animation | Fade + slight rise, 0.85s ease. No bounce, spin, or large translation |
| Fonts | System stack (PingFang SC / Hiragino / Microsoft YaHei). No web fonts |
| Framework | None — no reveal.js, no Slidev, no Tailwind CDN |
| Sizing | Everything in `cqw` (container query units) so text scales with slide |

Rationale: the lecture experience should feel calm and native. No cognitive tax on the audience trying to parse a busy color palette.

## License

MIT
