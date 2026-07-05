#!/usr/bin/env python3
"""Measure fable on biostack's flaw-detection benchmark by adding a 4th condition.

biostack already benchmarks vanilla / verbose / biostack (their 18 domain skills) on
review cases with planted bugs; the metric is detection_rate (fraction of ground-truth
bugs the reviewer catches) — a discipline metric. We add condition **fable** = the same
vanilla review task, but with the fable contract injected as the system prompt (exactly
how biostack mode injects its SKILL.md). This isolates: does generic operating discipline
raise flaw detection vs plain (vanilla), vs a domain checklist (verbose), vs domain
methodology (biostack)?

We IMPORT biostack's harness read-only (its cases, judge, scorer) and write results to
OUR dir — biostack is never modified. Uses the clean CLAUDE_CONFIG_DIR (no codex).

Usage: python3 run_fable_condition.py [skill ...]      # default: code-review bio-review
"""
import os, sys, json
from pathlib import Path

os.environ.setdefault("CLAUDE_CONFIG_DIR", os.path.expanduser("~/.fable-eval-config"))
BIOSTACK_EVAL = Path("/mnt/storage/wntjr3364/Task/biostack/eval")
SKILL_ROOT = Path("/mnt/storage/wntjr3364/Task/Skills/fable")
OUT = Path(__file__).resolve().parent / "results"
sys.path.insert(0, str(BIOSTACK_EVAL))

from run_eval import (  # noqa: E402  (read-only reuse of their harness)
    read_case_files, call_claude_cli, run_judge, compute_consensus,
    load_ground_truth, VANILLA_PROMPTS,
)
from config import DETECTION_CASES, JUDGE_REPS, MODELS  # noqa: E402

# The fable contract as one system prompt (same role biostack's SKILL.md plays).
FABLE_SYS = (
    "You operate under the following discipline contract.\n\n"
    + (SKILL_ROOT / "references/contract.md").read_text()
    + "\n\n"
    + (SKILL_ROOT / "references/gates.md").read_text()
)

MODEL_KEYS = ["sonnet", "opus"]  # fable5-ref optional; add "fable5" if MODELS has it


def run_case(skill, case, cfg, model_key):
    files = read_case_files(cfg["case_dir"], cfg["review_files"])
    user_message = VANILLA_PROMPTS[skill].format(file_contents=files)
    out = call_claude_cli(MODELS[model_key], FABLE_SYS, user_message)
    gt = load_ground_truth(cfg["gt_file"], cfg["gt_key"])
    judges = [run_judge(skill, case, out, gt, rep=r) for r in range(JUDGE_REPS)]
    cons = compute_consensus(judges, gt)
    res = {"skill": skill, "case": case, "model": model_key, "mode": "fable",
           "condition": f"{model_key}_fable", "model_output": out,
           "ground_truth_count": len(gt), "consensus": cons}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{skill}_{case}_{model_key}_fable.json").write_text(json.dumps(res, indent=1))
    dr = cons.get("detection_rate")
    print(f"  {skill}/{case} [{model_key}_fable]: detection_rate="
          f"{'%.0f%%' % (dr*100) if dr is not None else 'UNSCORED'} "
          f"({cons.get('detected')}/{cons.get('max_score')} bugs)")
    return res


def main():
    skills = sys.argv[1:] or ["code-review", "bio-review"]
    todo = [(s, c, cfg) for (s, c), cfg in DETECTION_CASES.items() if s in skills]
    print(f"fable condition: {len(todo)} cases x {len(MODEL_KEYS)} models "
          f"= {len(todo)*len(MODEL_KEYS)} runs x {JUDGE_REPS} judge reps")
    for s, c, cfg in todo:
        for mk in MODEL_KEYS:
            outp = OUT / f"{s}_{c}_{mk}_fable.json"
            if outp.exists():
                print(f"  skip {s}/{c} [{mk}_fable] (exists)"); continue
            try:
                run_case(s, c, cfg, mk)
            except Exception as e:
                print(f"  FAIL {s}/{c} [{mk}_fable]: {e}")


if __name__ == "__main__":
    main()
