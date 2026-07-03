#!/usr/bin/env python3
"""Aggregate judged eval scores into paired on-vs-off win rates with Wilson CIs, plus
gap-closure vs the Fable 5 reference ceiling.

Input: runs/<task>/judged.csv with columns:
    task, condition, seed, dimension, score   (score in {0,1,2})
condition in {sonnet-off, sonnet-on, opus-off, opus-on, fable5-ref}

Usage: python3 aggregate.py runs/*/judged.csv
"""
import csv, sys, math
from collections import defaultdict


def wilson(k, n, z=1.96):
    """Wilson score interval for a binomial proportion. Returns (lo, point, hi)."""
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (center - half, p, center + half)


def load(paths):
    # scores[(task, model, dimension)][cond_kind][seed] = score
    rows = []
    for path in paths:
        with open(path) as f:
            rows.extend(csv.DictReader(f))
    return rows


def main(paths):
    rows = load(paths)
    # index: (task, dimension) -> condition -> list of scores
    idx = defaultdict(lambda: defaultdict(list))
    for r in rows:
        idx[(r["task"], r["dimension"])][r["condition"]].append(int(r["score"]))

    models = [("sonnet", "sonnet-off", "sonnet-on"), ("opus", "opus-off", "opus-on")]
    print(f"{'task/dim':32} {'model':7} {'off':>5} {'on':>5} {'fable5':>7} "
          f"{'on>off win% [Wilson95]':>26} {'gap-closure':>12}")
    for (task, dim), byc in sorted(idx.items()):
        f5 = byc.get("fable5-ref", [])
        f5_mean = sum(f5) / len(f5) if f5 else None
        for model, off_c, on_c in models:
            off, on = byc.get(off_c, []), byc.get(on_c, [])
            if not off or not on:
                continue
            off_mean, on_mean = sum(off) / len(off), sum(on) / len(on)
            # Paired win: compare on vs off per matched seed; win if on>off, tie=0.5.
            n = min(len(off), len(on))
            wins = sum((on[i] > off[i]) + 0.5 * (on[i] == off[i]) for i in range(n))
            lo, p, hi = wilson(round(wins), n)
            # Gap closure vs Fable 5 ceiling (only where fable5 > off).
            if f5_mean is not None and f5_mean > off_mean:
                gap = (on_mean - off_mean) / (f5_mean - off_mean)
                gap_s = f"{gap:+.0%}"
            else:
                gap_s = f"raw{on_mean - off_mean:+.2f}"
            f5s = f"{f5_mean:.2f}" if f5_mean is not None else "  -  "
            print(f"{task+'/'+dim:32} {model:7} {off_mean:5.2f} {on_mean:5.2f} "
                  f"{f5s:>7} {p:>10.0%} [{lo:.0%},{hi:.0%}] n={n:<3} {gap_s:>12}")
    print("\nGap-closure = (on-off)/(fable5-off): how much of the model's gap to the "
          "Fable 5 ceiling the skill closed. Wide CIs at small n → signal, not proof.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: aggregate.py runs/*/judged.csv")
    main(sys.argv[1:])
