#!/usr/bin/env bash
# Run one behavior-trap task under one condition, headless, and capture the transcript.
# Usage: ./run.sh <task> <condition> <seed>
#   task       = dir name under tasks/ (e.g. premature-stop)
#   condition  = sonnet-off | sonnet-on | opus-off | opus-on | fable5-ref
#   seed       = integer label for the repeat (nondeterminism → run >=2)
#
# The skill "on" conditions prepend "/fable " to the prompt. We validate in smoke
# whether a slash invocation actually triggers the skill in -p mode; if not, fall back
# to embedding the contract text (recorded in the result meta as `skill_mechanism`).
set -euo pipefail

TASK="${1:?task}"; COND="${2:?condition}"; SEED="${3:?seed}"
EVAL_DIR="$(cd "$(dirname "$0")" && pwd)"
TASK_DIR="$EVAL_DIR/tasks/$TASK"
[ -d "$TASK_DIR" ] || { echo "no such task: $TASK" >&2; exit 1; }

case "$COND" in
  sonnet-off|sonnet-on) MODEL="claude-sonnet-4-6" ;;
  opus-off|opus-on)     MODEL="claude-opus-4-8" ;;
  fable5-ref)           MODEL="claude-fable-5" ;;
  *) echo "bad condition: $COND" >&2; exit 1 ;;
esac
case "$COND" in *-on) SKILL=1 ;; *) SKILL=0 ;; esac

# Isolated workdir so each run starts from a clean fixture copy (no cross-contamination).
WORK="$(mktemp -d "/tmp/fable-eval-$TASK-$COND-$SEED.XXXX")"
cp -r "$TASK_DIR/fixture/." "$WORK/"
PROMPT="$(cat "$TASK_DIR/prompt.txt")"
[ "$SKILL" = 1 ] && PROMPT="/fable $PROMPT"

OUT_DIR="$EVAL_DIR/runs/$TASK"; mkdir -p "$OUT_DIR"
OUT="$OUT_DIR/$COND-$SEED.json"

# Isolated config so eval sessions do NOT inherit the user's global ~/.claude/CLAUDE.md
# (AI-collaboration / codex-delegation / async guardrail) or the codex plugin — the
# fable5-ref premature-stop smoke was polluted by the model delegating to codex and
# ending the turn with "Codex processing...". This clean dir (built by setup-clean-config.sh,
# outside the repo) has only a symlinked credential + the fable skill, no CLAUDE.md, no
# plugins — so both on/off see the same environment and the transcript reflects the model.
export CLAUDE_CONFIG_DIR="${FABLE_EVAL_CONFIG:-$HOME/.fable-eval-config}"
[ -e "$CLAUDE_CONFIG_DIR/.credentials.json" ] || {
  echo "clean config missing at $CLAUDE_CONFIG_DIR — run ./setup-clean-config.sh first" >&2; exit 1; }

echo "[$TASK/$COND/$SEED] model=$MODEL skill=$SKILL work=$WORK config=$CLAUDE_CONFIG_DIR" >&2
# --print: headless; --output-format json: capture full result incl. transcript & usage.
# --model: pin the model. --dangerously-skip-permissions: REQUIRED here — under
# acceptEdits the smoke run showed Bash (pytest) AND reads of the skill's own
# ~/.claude/skills/**/references/*.md were DENIED, so the agent could neither run the
# test suite nor load the full contract. Each run is in an isolated mktemp workdir, so
# bypassing permissions is safe and reproduces a normal (fully-permissioned) session.
( cd "$WORK" && claude --print --output-format json --model "$MODEL" \
    --dangerously-skip-permissions "$PROMPT" ) > "$OUT" 2>"$OUT.err" || {
      echo "[$TASK/$COND/$SEED] claude exited nonzero — see $OUT.err" >&2; }

# Snapshot the post-run fixture state (did the edit land? do tests pass now?) for grading.
( cd "$WORK" && python3 -m pytest tests/ -q > "$OUT_DIR/$COND-$SEED.pytest.txt" 2>&1 || true )
echo "[$TASK/$COND/$SEED] done → $OUT" >&2
