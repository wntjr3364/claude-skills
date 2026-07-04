#!/usr/bin/env python3
"""On-vs-off readout from the SWE-bench eval reports.

PRIMARY metric = pass@1 (official swebench Docker eval; fully rigorous, no transcript
parsing). Paired McNemar per model on shared instances, and gap-closure vs the Fable 5
ceiling.

HONEST CAVEAT on discipline signals: they were extracted from the claude -p `result`
field, which is only the FINAL message — it does NOT contain the tool calls, so
"ran_tests" is unmeasurable from what we captured (a model that ran the suite but only
summarized it reads as False). Discipline is therefore reported ONLY as a crude
work-proxy (num_turns) + final-message overclaim, both clearly labelled — the real
discipline signal needs a stream-json re-capture or the blinded judge. Do not read the
heuristic ran_tests as a result.

Usage: python3 results.py
"""
import json, os, glob, math

HERE = os.path.dirname(os.path.abspath(__file__))
CONDS = ["sonnet-off", "sonnet-on", "opus-off", "opus-on", "fable5-ref"]
RUNS = os.path.join(HERE, "runs")


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0, c - h), p, min(1, c + h))


def load_reports():
    out = {}
    for cond in CONDS:
        g = glob.glob(os.path.join(HERE, f"fable-{cond}.fable_{cond}.json"))
        if not g:
            continue
        d = json.load(open(g[0]))
        out[cond] = {
            "completed": d.get("completed_instances", 0),
            "resolved": d.get("resolved_instances", 0),
            "resolved_ids": set(d.get("resolved_ids", [])),
            "submitted_ids": set(d.get("submitted_ids", [])),
            "empty": d.get("empty_patch_instances", 0),
        }
    return out


def mcnemar(off_ids, on_ids, shared):
    b = sum(1 for i in shared if i in off_ids and i not in on_ids)   # off pass, on fail
    c = sum(1 for i in shared if i not in off_ids and i in on_ids)   # on pass, off fail
    n = b + c
    if n == 0:
        return b, c, 1.0
    k = min(b, c)
    p = min(1.0, 2 * sum(math.comb(n, j) for j in range(k + 1)) / (2 ** n))
    return b, c, p


def turns_by_cond():
    agg = {}
    for cond in CONDS:
        vals = []
        for js in glob.glob(os.path.join(RUNS, "*", f"{cond}-1.json")):
            try:
                d = json.load(open(js))
                if d.get("result"):  # non-empty transcript
                    vals.append(d.get("num_turns", 0))
            except Exception:
                pass
        if vals:
            agg[cond] = sum(vals) / len(vals)
    return agg


def main():
    R = load_reports()
    print("=== pass@1 — SWE-bench Verified, 12 django instances (official Docker eval) ===")
    for cond in CONDS:
        if cond in R:
            r = R[cond]
            lo, p, hi = wilson(r["resolved"], r["completed"])
            note = f"  ({r['empty']} empty patch)" if r["empty"] else ""
            print(f"  {cond:12} {r['resolved']:2}/{r['completed']:2} = {p:>4.0%}  "
                  f"[Wilson95 {lo:.0%},{hi:.0%}]{note}")

    print("\n=== paired on-vs-off (McNemar, shared resolved sets) ===")
    for model in ("sonnet", "opus"):
        if f"{model}-off" in R and f"{model}-on" in R:
            off, on = R[f"{model}-off"], R[f"{model}-on"]
            shared = off["submitted_ids"] & on["submitted_ids"]
            b, c, p = mcnemar(off["resolved_ids"], on["resolved_ids"], shared)
            d = on["resolved"] - off["resolved"]
            print(f"  {model:6}: off {off['resolved']}/{off['completed']} -> "
                  f"on {on['resolved']}/{on['completed']}  (Δ {d:+d})  "
                  f"discordant: on-gained={c} on-lost={b}  McNemar p={p:.3f}")

    if "fable5-ref" in R:
        f5 = R["fable5-ref"]["resolved"] / R["fable5-ref"]["completed"]
        print(f"\n=== gap-closure vs Fable 5 ceiling ({f5:.0%}) ===")
        for model in ("sonnet", "opus"):
            if f"{model}-off" in R and f"{model}-on" in R:
                o = R[f"{model}-off"]["resolved"] / R[f"{model}-off"]["completed"]
                n = R[f"{model}-on"]["resolved"] / R[f"{model}-on"]["completed"]
                gc = (n - o) / (f5 - o) if f5 > o else None
                s = f"{gc:+.0%}" if gc is not None else "n/a (fable5<=off)"
                print(f"  {model:6}: off={o:.0%} on={n:.0%} fable5={f5:.0%}  gap-closure={s}")

    t = turns_by_cond()
    if t:
        print("\n=== work-proxy: avg num_turns (crude; NOT the discipline signal) ===")
        for cond in CONDS:
            if cond in t:
                print(f"  {cond:12} {t[cond]:.1f} turns")

    print("\nCAVEAT: n=12, 1 seed → wide CIs; read as SIGNAL not proof. Discipline signals"
          "\nare NOT validly measured here (result field = final message only, no tool calls);"
          "\npass@1 is the rigorous metric. A stream-json re-capture or blinded judge is needed"
          "\nfor discipline. Empty patches (hard tasks the weaker model couldn't solve in budget)"
          "\ncount as unresolved.")


if __name__ == "__main__":
    main()
