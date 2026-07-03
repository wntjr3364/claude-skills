#!/usr/bin/env bash
# SWE-bench agent phase: run one instance under one condition, capture the patch.
#
# Usage: ./agent_run.sh <instance_id> <condition> <seed>
#   condition = sonnet-off | sonnet-on | opus-off | opus-on | fable5-ref
#
# Design (django-only subset): check out the repo at base_commit on the host, pip-install
# it into a throwaway venv so the agent CAN run tests (the discipline signal we measure),
# run claude -p with the problem statement, and capture `git diff` as the prediction patch.
# Eval is done separately by the official swebench Docker harness (eval_run.sh) on a clean
# rebuild, so host-side install only needs to be good enough for the agent to run tests.
#
# Uses the SAME clean CLAUDE_CONFIG_DIR as run.sh (no codex/CLAUDE.md contamination).
set -euo pipefail

INST="${1:?instance_id}"; COND="${2:?condition}"; SEED="${3:?seed}"
HERE="$(cd "$(dirname "$0")" && pwd)"; EVAL_DIR="$(dirname "$HERE")"
export CLAUDE_CONFIG_DIR="${FABLE_EVAL_CONFIG:-$HOME/.fable-eval-config}"
[ -e "$CLAUDE_CONFIG_DIR/.credentials.json" ] || { echo "run setup-clean-config.sh first" >&2; exit 1; }

case "$COND" in
  sonnet-off|sonnet-on) MODEL="claude-sonnet-4-6" ;;
  opus-off|opus-on)     MODEL="claude-opus-4-8" ;;
  fable5-ref)           MODEL="claude-fable-5" ;;
  *) echo "bad condition: $COND" >&2; exit 1 ;;
esac
case "$COND" in *-on) SKILL=1 ;; *) SKILL=0 ;; esac

OUT_DIR="$HERE/runs/$INST"; mkdir -p "$OUT_DIR"
META="$HERE/instances/$INST.json"
[ -f "$META" ] || { echo "missing instance meta $META — run prepare_subset.py" >&2; exit 1; }
REPO=$(python3 -c "import json;print(json.load(open('$META'))['repo'])")
BASE=$(python3 -c "import json;print(json.load(open('$META'))['base_commit'])")
PROBLEM=$(python3 -c "import json;print(json.load(open('$META'))['problem_statement'])")

WORK="$(mktemp -d "/tmp/swebench-$INST-$COND-$SEED.XXXX")"
echo "[$INST/$COND/$SEED] repo=$REPO base=${BASE:0:8} work=$WORK" >&2
git clone --quiet "https://github.com/$REPO" "$WORK/repo"
git -C "$WORK/repo" checkout --quiet "$BASE"

# Editable install so the agent can import + run the test suite in-place.
python3 -m venv "$WORK/venv"
"$WORK/venv/bin/pip" install -q -e "$WORK/repo" 2>"$OUT_DIR/$COND-$SEED.install.log" || \
  echo "[$INST/$COND/$SEED] install warnings — see install.log" >&2

PROMPT="$PROBLEM

Work in this repository to resolve the issue. The project is pip-installed in the active
environment, so you can run its test suite."
[ "$SKILL" = 1 ] && PROMPT="/fable $PROMPT"

( cd "$WORK/repo" && PATH="$WORK/venv/bin:$PATH" VIRTUAL_ENV="$WORK/venv" \
    claude --print --output-format json --model "$MODEL" \
    --dangerously-skip-permissions "$PROMPT" ) > "$OUT_DIR/$COND-$SEED.json" 2>"$OUT_DIR/$COND-$SEED.err" \
  || echo "[$INST/$COND/$SEED] claude nonzero — see .err" >&2

# The prediction is whatever the agent changed, as a patch against base.
git -C "$WORK/repo" add -A
git -C "$WORK/repo" diff --cached "$BASE" > "$OUT_DIR/$COND-$SEED.patch" || true
echo "[$INST/$COND/$SEED] patch $(wc -l < "$OUT_DIR/$COND-$SEED.patch") lines → $OUT_DIR" >&2
rm -rf "$WORK"
