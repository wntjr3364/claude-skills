#!/usr/bin/env bash
# Build the isolated Claude config the eval runs use, OUTSIDE the repo.
#
# Why: eval sessions must NOT inherit the user's global ~/.claude/CLAUDE.md (which carries
# AI-collaboration / codex-delegation / async-guardrail instructions) or the codex plugin —
# a fable5-ref run was polluted by the model delegating to codex and ending its turn with
# "Codex processing...", making the transcript ungradeable. This clean dir has only:
#   - a SYMLINK to the real credential (no token copy is persisted — avoids credential leakage)
#   - a symlink to the fable skill (so the -on condition can load /fable)
#   - NO CLAUDE.md, NO plugins
# so on/off share one environment and the transcript reflects the model, not codex.
#
# Location is outside the git repo on purpose; never commit a credential artifact.
set -euo pipefail
CLEAN="${FABLE_EVAL_CONFIG:-$HOME/.fable-eval-config}"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"   # .../Skills/fable

mkdir -p "$CLEAN/skills"
ln -sfn "$HOME/.claude/.credentials.json" "$CLEAN/.credentials.json"
ln -sfn "$SKILL_DIR" "$CLEAN/skills/fable"

echo "clean config ready at $CLEAN"
echo "  credential: symlink -> ~/.claude/.credentials.json (no copy)"
echo "  skills/fable: symlink -> $SKILL_DIR"
echo "  (no CLAUDE.md, no plugins → no codex/ask, no async guardrail)"
