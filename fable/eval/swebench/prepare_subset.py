#!/usr/bin/env python3
"""Select a deterministic django subset of SWE-bench Verified and write per-instance
metadata the agent runner reads. Django-only: light to pip-install on the host so the
agent can actually run tests (the discipline signal), and plentiful (231 in Verified).

Usage: python3 prepare_subset.py [N]   (default 12)
Writes: instances/<id>.json (one per task) and subset.txt (the id list).
Selection is deterministic (sorted ids, evenly sampled across difficulty) — no RNG, so
the subset is reproducible and auditable.
"""
import json, os, sys
from datasets import load_dataset

N = int(sys.argv[1]) if len(sys.argv) > 1 else 12
HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(HERE, "instances"), exist_ok=True)

ds = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
django = [d for d in ds if d["repo"] == "django/django"]

# Even split across the two most useful difficulty bands (skip >4h; <15min can be too
# trivial to discriminate but we include some as a floor).
bands = {"<15 min fix": [], "15 min - 1 hour": [], "1-4 hours": []}
for d in sorted(django, key=lambda x: x["instance_id"]):
    if d["difficulty"] in bands:
        bands[d["difficulty"]].append(d)

pick, i = [], 0
order = ["15 min - 1 hour", "<15 min fix", "1-4 hours"]  # prefer the discriminating middle
while len(pick) < N and any(bands[b] for b in order):
    b = order[i % len(order)]
    if bands[b]:
        pick.append(bands[b].pop(0))
    i += 1

keep = ("instance_id", "repo", "base_commit", "problem_statement", "difficulty",
        "FAIL_TO_PASS", "PASS_TO_PASS", "version")
ids = []
for d in pick:
    ids.append(d["instance_id"])
    meta = {k: d[k] for k in keep}
    with open(os.path.join(HERE, "instances", d["instance_id"] + ".json"), "w") as f:
        json.dump(meta, f)
with open(os.path.join(HERE, "subset.txt"), "w") as f:
    f.write("\n".join(ids) + "\n")

print(f"selected {len(ids)} django instances:")
for d in pick:
    print(f"  {d['instance_id']:32} {d['difficulty']}")
