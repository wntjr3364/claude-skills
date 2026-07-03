#!/usr/bin/env bash
# Drive the full SWE-bench A/B: agent phase for every (instance x condition), then build
# predictions, then the official eval, then the discipline-signal table. Idempotent-ish:
# skips an (instance,condition) whose .patch already exists.
#
# Usage: ./run_batch.sh "sonnet-off sonnet-on opus-off opus-on fable5-ref" [seed]
# Agent runs are serialized (each spins a venv + claude session); eval is one harness call.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
CONDS="${1:-sonnet-off sonnet-on opus-off opus-on fable5-ref}"
SEED="${2:-1}"
mapfile -t INSTS < "$HERE/subset.txt"

echo "== agent phase: ${#INSTS[@]} instances x $(wc -w <<<"$CONDS") conditions =="
for inst in "${INSTS[@]}"; do
  for cond in $CONDS; do
    if [ -s "$HERE/runs/$inst/$cond-$SEED.patch" ]; then
      echo "skip $inst/$cond (patch exists)"; continue
    fi
    "$HERE/agent_run.sh" "$inst" "$cond" "$SEED" || echo "  (agent failed $inst/$cond)"
  done
done

echo "== predictions =="
python3 "$HERE/eval_and_score.py" predictions --conditions "$(tr ' ' ',' <<<"$CONDS")"

echo "== eval (official swebench harness, per condition) =="
for cond in $CONDS; do
  python3 -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path "$HERE/preds/$cond.jsonl" \
    --max_workers 4 --run_id "fable_$cond" --cache_level instance \
    || echo "  (eval failed for $cond)"
done

echo "== discipline signals =="
python3 "$HERE/eval_and_score.py" signals
echo "Done. Outcome reports: fable-<cond>.fable_<cond>.json ; signals: signals.json"
