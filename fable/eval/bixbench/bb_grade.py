#!/usr/bin/env python3
"""Grade BixBench agent answers vs the ideal (BixBench open-answer style: an LLM judge
assigns correct / incorrect / refused). Judge = claude -p (subscription), blind to which
condition produced the answer. Also pulls token/turns for the cost comparison.

Usage: python3 bb_grade.py            # grades everything under runs/, writes graded.json + table
"""
import json, os, glob, subprocess, re

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "runs")
CONDS = ["sonnet-off", "sonnet-on", "opus-off", "opus-on", "fable5-ref"]

JUDGE = """You are grading one answer to a bioinformatics data-analysis question against the target.
Question: {q}
Target answer: {ideal}
Predicted answer: {pred}

Compare ONLY the substance. Numeric answers match if they agree to reasonable precision or
fall in the target range (e.g. target "1-50" means the value/group 1-50). Reply with exactly
one word on the first line: CORRECT, INCORRECT, or REFUSED (the prediction declined / said it
couldn't determine). Then one short sentence of reason."""


def judge(q, ideal, pred):
    env = dict(os.environ, CLAUDE_CONFIG_DIR=os.path.expanduser(
        os.environ.get("FABLE_EVAL_CONFIG", "~/.fable-eval-config")))
    p = subprocess.run(
        ["claude", "--print", "--model", "claude-sonnet-4-6",
         "--dangerously-skip-permissions",
         JUDGE.format(q=q[:600], ideal=ideal, pred=pred[:600])],
        capture_output=True, text=True, env=env, timeout=180)
    out = p.stdout.strip()
    verdict = "REFUSED"
    m = re.search(r"\b(CORRECT|INCORRECT|REFUSED)\b", out)
    if m:
        verdict = m.group(1)
    return verdict, out[:200]


def main():
    rows = []
    for sid_dir in sorted(glob.glob(os.path.join(RUNS, "*"))):
        sid = os.path.basename(sid_dir)
        meta = json.load(open(os.path.join(HERE, "instances", sid, "meta.json")))
        for cond in CONDS:
            af = os.path.join(sid_dir, f"{cond}-1.answer.txt")
            jf = os.path.join(sid_dir, f"{cond}-1.json")
            if not os.path.exists(af):
                continue
            pred = open(af).read().strip()
            v, reason = judge(meta["question"], meta["ideal"], pred)
            tok = turns = cost = 0
            if os.path.exists(jf):
                d = json.load(open(jf))
                u = d.get("usage", {})
                tok = u.get("output_tokens", 0); turns = d.get("num_turns", 0)
                cost = d.get("total_cost_usd", 0)
            rows.append(dict(sid=sid, condition=cond, verdict=v, pred=pred[:60],
                             ideal=str(meta["ideal"]), out_tok=tok, turns=turns, cost=cost))
            print(f"  {sid:8} {cond:12} {v:9} pred={pred[:30]!r} ideal={meta['ideal']!r}")
    json.dump(rows, open(os.path.join(HERE, "graded.json"), "w"), indent=1)

    print("\n=== accuracy per condition (CORRECT / graded) ===")
    from collections import defaultdict
    by = defaultdict(list)
    for r in rows:
        by[r["condition"]].append(r)
    for c in CONDS:
        rs = by.get(c, [])
        if not rs:
            continue
        corr = sum(r["verdict"] == "CORRECT" for r in rs)
        ref = sum(r["verdict"] == "REFUSED" for r in rs)
        ct = sum(r["cost"] for r in rs) / len(rs)
        tn = sum(r["turns"] for r in rs) / len(rs)
        print(f"  {c:12} {corr}/{len(rs)} correct, {ref} refused  | avg {tn:.0f} turns, ${ct:.3f}/run")
    print("\nn is tiny (smoke) — signal only. Judge = sonnet, blind to condition.")


if __name__ == "__main__":
    main()
