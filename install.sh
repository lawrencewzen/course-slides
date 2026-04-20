#!/usr/bin/env bash
# Install course-deck as a Claude Code skill.
# Symlinks this repo into ~/.claude/skills/course-deck.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="${HOME}/.claude/skills/course-deck"

if [[ ! -f "${REPO_DIR}/SKILL.md" ]]; then
  echo "Error: SKILL.md not found in ${REPO_DIR}. Are you running this from the repo root?" >&2
  exit 1
fi

mkdir -p "${HOME}/.claude/skills"

if [[ -L "${SKILL_DIR}" ]]; then
  current_target="$(readlink "${SKILL_DIR}")"
  if [[ "${current_target}" == "${REPO_DIR}" ]]; then
    echo "Already installed: ${SKILL_DIR} -> ${REPO_DIR}"
    exit 0
  fi
  echo "Existing symlink points to ${current_target}."
  read -rp "Replace with ${REPO_DIR}? [y/N] " ans
  [[ "${ans}" == "y" || "${ans}" == "Y" ]] || { echo "Aborted."; exit 1; }
  rm "${SKILL_DIR}"
elif [[ -e "${SKILL_DIR}" ]]; then
  backup="${SKILL_DIR}.backup.$(date +%Y%m%d%H%M%S)"
  echo "Existing directory at ${SKILL_DIR}; moving to ${backup}"
  mv "${SKILL_DIR}" "${backup}"
fi

ln -s "${REPO_DIR}" "${SKILL_DIR}"
echo "Installed: ${SKILL_DIR} -> ${REPO_DIR}"
echo "Restart Claude Code (or start a new session) to pick up the skill."
