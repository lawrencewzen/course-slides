#!/usr/bin/env bash
# Install course-slides as a Claude Code and/or Codex skill.
# Symlinks this repo into ~/.claude/skills/course-slides and/or ~/.codex/skills/course-slides.
#
# Usage:
#   ./install.sh              install to both (if parent dirs exist)
#   ./install.sh --claude     install to Claude Code only
#   ./install.sh --codex      install to Codex only
#   ./install.sh --both       force install to both, creating parent dirs

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -f "${REPO_DIR}/SKILL.md" ]]; then
  echo "Error: SKILL.md not found in ${REPO_DIR}. Are you running this from the repo root?" >&2
  exit 1
fi

MODE="${1:-auto}"

install_one() {
  local label="$1"
  local parent="$2"
  local target="${parent}/course-slides"

  mkdir -p "${parent}"

  if [[ -L "${target}" ]]; then
    local current
    current="$(readlink "${target}")"
    if [[ "${current}" == "${REPO_DIR}" ]]; then
      echo "[${label}] already installed: ${target} -> ${REPO_DIR}"
      return 0
    fi
    echo "[${label}] existing symlink points to ${current}."
    read -rp "       replace with ${REPO_DIR}? [y/N] " ans
    [[ "${ans}" == "y" || "${ans}" == "Y" ]] || { echo "[${label}] skipped."; return 0; }
    rm "${target}"
  elif [[ -e "${target}" ]]; then
    local backup="${target}.backup.$(date +%Y%m%d%H%M%S)"
    echo "[${label}] existing directory at ${target}; moving to ${backup}"
    mv "${target}" "${backup}"
  fi

  ln -s "${REPO_DIR}" "${target}"
  echo "[${label}] installed: ${target} -> ${REPO_DIR}"
}

claude_parent="${HOME}/.claude/skills"
codex_parent="${HOME}/.codex/skills"

case "${MODE}" in
  --claude)
    install_one "claude-code" "${claude_parent}"
    ;;
  --codex)
    install_one "codex" "${codex_parent}"
    ;;
  --both)
    install_one "claude-code" "${claude_parent}"
    install_one "codex" "${codex_parent}"
    ;;
  auto)
    any=0
    if [[ -d "${HOME}/.claude" ]]; then
      install_one "claude-code" "${claude_parent}"
      any=1
    fi
    if [[ -d "${HOME}/.codex" ]]; then
      install_one "codex" "${codex_parent}"
      any=1
    fi
    if [[ ${any} -eq 0 ]]; then
      echo "Neither ~/.claude nor ~/.codex found. Pass --claude, --codex, or --both to force install." >&2
      exit 1
    fi
    ;;
  *)
    echo "Unknown option: ${MODE}" >&2
    echo "Usage: $0 [--claude | --codex | --both]" >&2
    exit 2
    ;;
esac

echo
echo "Restart your agent (Claude Code / Codex) or start a new session to pick up the skill."
echo
echo "Optional: to enable assets/visual_check.py (headless pixel overflow check), run once:"
echo "  pip install playwright && python3 -m playwright install chromium"
