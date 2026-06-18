#!/usr/bin/env bash
# Install the authored skills on THIS machine by symlinking each skill folder
# into ~/.claude/skills/. Idempotent — re-run after cloning/pulling on a new server.
#
#   git clone <this repo> && cd <repo> && ./install.sh
#
set -euo pipefail
REPO="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/.claude/skills"
mkdir -p "$DEST"
linked=0
for d in "$REPO"/*/; do
  d="${d%/}"
  [ -f "$d/SKILL.md" ] || continue          # only real skill folders
  name="$(basename "$d")"
  ln -sfn "$d" "$DEST/$name"                  # -n so an existing symlink is replaced, not nested
  echo "linked  $name  ->  $DEST/$name"
  linked=$((linked+1))
done
echo "done: $linked skill(s) linked. They are now globally available in Claude Code on this machine."
echo "note: 'codex' CLI (installed + authenticated) is recommended for the Codex review layer;"
echo "      without it crossfire still runs (lenses + health) and notes codex as skipped."
