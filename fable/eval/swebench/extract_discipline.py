#!/usr/bin/env python3
"""Extract REAL discipline signals from the saved session transcripts (which include tool
calls), NOT the -p `result` field (final message only). This salvages the discipline
dimension from the runs already done — no re-capture needed.

Transcripts live under the clean config's projects dir; each SWE-bench run's dir is named
after its workdir, e.g. `-tmp-swebench-django--django-10097-sonnet-off-1-XXXX-repo`.

Signals per (instance, condition):
  ran_tests        — agent issued >=1 Bash test-runner command (runtests.py/pytest/manage test)
  n_test_runs      — how many
  verified_after_edit — ran tests AFTER its last file edit (the core "verify your fix" discipline)
  n_edits          — file-edit tool calls

Usage: python3 extract_discipline.py            # prints table + writes discipline.json
"""
import json, os, glob, re
from collections import defaultdict

CONF = os.path.expanduser("~/.fable-eval-config/projects")
HERE = os.path.dirname(os.path.abspath(__file__))
CONDS = ["sonnet-off", "sonnet-on", "opus-off", "opus-on", "fable5-ref"]

TEST_CMD = re.compile(r"runtests\.py|pytest|manage(\.py)? test|python -m django test|\btox\b")
EDIT_TOOLS = {"str_replace", "create_file", "Edit", "Write", "NotebookEdit", "MultiEdit"}
# dir: -tmp-swebench-django--django-10097-sonnet-off-1-XXXX-repo
DIRRE = re.compile(r"-tmp-swebench-(.+?)-(sonnet-off|sonnet-on|opus-off|opus-on|fable5-ref)-1-\w+-repo$")


def parse_transcript(path):
    """Return ordered list of ('edit'|'test'|other, detail) events from tool calls."""
    events = []
    for line in open(path):
        try:
            d = json.loads(line)
        except Exception:
            continue
        m = d.get("message")
        content = m.get("content") if isinstance(m, dict) else None
        if not isinstance(content, list):
            continue
        for c in content:
            if not isinstance(c, dict) or c.get("type") != "tool_use":
                continue
            name = c.get("name", "")
            if name == "Bash":
                cmd = (c.get("input", {}) or {}).get("command", "") or ""
                if TEST_CMD.search(cmd):
                    events.append(("test", cmd[:60]))
            elif name in EDIT_TOOLS:
                events.append(("edit", name))
    return events


def main():
    # instance -> condition -> signals (latest transcript wins if duplicated)
    rows = {}
    for d in sorted(glob.glob(os.path.join(CONF, "*"))):
        mm = DIRRE.search(os.path.basename(d))
        if not mm:
            continue
        inst = mm.group(1).replace("--", "__")
        cond = mm.group(2)
        tj = glob.glob(os.path.join(d, "*.jsonl"))
        if not tj:
            continue
        ev = parse_transcript(max(tj, key=os.path.getmtime))
        tests = [i for i, (k, _) in enumerate(ev) if k == "test"]
        edits = [i for i, (k, _) in enumerate(ev) if k == "edit"]
        verified = bool(tests and edits and max(tests) > max(edits))
        rows[(inst, cond)] = dict(instance=inst, condition=cond,
                                  ran_tests=bool(tests), n_test_runs=len(tests),
                                  n_edits=len(edits), verified_after_edit=verified)

    data = list(rows.values())
    with open(os.path.join(HERE, "discipline.json"), "w") as f:
        json.dump(data, f, indent=1)

    print(f"parsed {len(data)} transcripts with tool calls\n")
    by = defaultdict(list)
    for r in data:
        by[r["condition"]].append(r)
    print(f"{'condition':12} {'n':>3} {'ran_tests':>10} {'verified_after_edit':>20} {'avg_test_runs':>14}")
    for cond in CONDS:
        rs = by.get(cond, [])
        if not rs:
            continue
        n = len(rs)
        rt = sum(r["ran_tests"] for r in rs)
        va = sum(r["verified_after_edit"] for r in rs)
        atr = sum(r["n_test_runs"] for r in rs) / n
        print(f"{cond:12} {n:>3} {rt:>4}/{n:<2}={rt/n:>4.0%} {va:>10}/{n:<2}={va/n:>4.0%} {atr:>14.1f}")

    print("\n--- paired on-vs-off (same instances) ---")
    for model in ("sonnet", "opus"):
        off = {r["instance"]: r for r in by.get(f"{model}-off", [])}
        on = {r["instance"]: r for r in by.get(f"{model}-on", [])}
        shared = sorted(set(off) & set(on))
        if not shared:
            continue
        for sig in ("ran_tests", "verified_after_edit"):
            o = sum(off[i][sig] for i in shared)
            n = sum(on[i][sig] for i in shared)
            print(f"  {model} [{sig}]: off {o}/{len(shared)} -> on {n}/{len(shared)}  (Δ {n-o:+d})")


if __name__ == "__main__":
    main()
