#!/usr/bin/env bash
# BixBench agent phase (Path B: claude -p on the subscription, real /fable skill).
# Usage: ./bb_run.sh <short_id> <condition> <seed>
#   condition = sonnet-off | sonnet-on | opus-off | opus-on | fable5-ref
# Copies the capsule's raw data into an isolated workdir, runs claude -p there with the
# Python scientific env on PATH (so the agent can actually analyse the data), and captures
# the agent's final answer. The executed solution notebook is never present (prepare step
# excluded it). Uses the same clean CLAUDE_CONFIG_DIR as the SWE-bench runner (no codex).
set -euo pipefail
SID="${1:?short_id}"; COND="${2:?condition}"; SEED="${3:?seed}"
HERE="$(cd "$(dirname "$0")" && pwd)"; EVAL_DIR="$(dirname "$HERE")"
export CLAUDE_CONFIG_DIR="${FABLE_EVAL_CONFIG:-$HOME/.fable-eval-config}"
PYENV="$HERE/pyenv"
[ -e "$CLAUDE_CONFIG_DIR/.credentials.json" ] || { echo "run setup-clean-config.sh first" >&2; exit 1; }
[ -x "$PYENV/bin/python" ] || { echo "python env missing at $PYENV" >&2; exit 1; }

case "$COND" in
  sonnet-off|sonnet-on|sonnet-biostack) MODEL="claude-sonnet-4-6" ;;
  opus-off|opus-on|opus-biostack)       MODEL="claude-opus-4-8" ;;
  fable5-ref)                           MODEL="claude-fable-5" ;;
  *) echo "bad condition"; exit 1 ;;
esac
# mode: off=vanilla, on=/fable, biostack=/biostack-analyze
case "$COND" in
  *-on)       PREFIX="/fable " ;;
  *-biostack) PREFIX="/biostack-analyze " ; export PATH="/mnt/storage/wntjr3364/Task/biostack/bin:$PATH" ;;
  *)          PREFIX="" ;;
esac

INST="$HERE/instances/$SID"
[ -f "$INST/meta.json" ] || { echo "run prepare_bixbench.py $SID first" >&2; exit 1; }
Q=$(python3 -c "import json;print(json.load(open('$INST/meta.json'))['question'])")

WORK="$(mktemp -d "/tmp/bixbench-$SID-$COND-$SEED.XXXX")"
cp -r "$INST/data/." "$WORK/"
OUT="$HERE/runs/$SID"; mkdir -p "$OUT"

PROMPT="You are analysing a real biological dataset to answer a research question. The data
files are in the current directory. Use Python (pandas, numpy, scipy, statsmodels,
scikit-learn are installed) to load and analyse them, then give the answer.

Question: $Q

Explore the data first, run the analysis, and end with a line exactly:
FINAL ANSWER: <your answer>"
PROMPT="${PREFIX}${PROMPT}"

echo "[$SID/$COND/$SEED] model=$MODEL mode=$COND work=$WORK" >&2
( cd "$WORK" && PATH="$PYENV/bin:$PATH" \
    claude --print --output-format json --model "$MODEL" \
    --dangerously-skip-permissions "$PROMPT" ) > "$OUT/$COND-$SEED.json" 2>"$OUT/$COND-$SEED.err" \
  || echo "[$SID/$COND/$SEED] claude nonzero — see .err" >&2

# extract the FINAL ANSWER line for grading
python3 -c "
import json,re
d=json.load(open('$OUT/$COND-$SEED.json'))
r=d.get('result','')
m=re.search(r'FINAL ANSWER:\s*(.+)', r)
open('$OUT/$COND-$SEED.answer.txt','w').write((m.group(1).strip() if m else r[-300:]).strip())
print('[$SID/$COND/$SEED] answer:', (m.group(1).strip()[:80] if m else '(no FINAL ANSWER line)'))
" 2>/dev/null || echo "(answer extract failed)"
rm -rf "$WORK"
