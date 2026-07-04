#!/usr/bin/env python3
"""Dump a BixBench subset's metadata for the agent runner. Downloads each capsule zip and
extracts ONLY the CapsuleData folder (the raw data) into instances/<short_id>/data — the
CapsuleNotebook (executed solution, contains the answer) is never exposed to the agent.

Usage: python3 prepare_bixbench.py bix-10 bix-16 bix-17    # explicit smoke ids
"""
import json, os, sys, zipfile, shutil
from datasets import load_dataset
from huggingface_hub import hf_hub_download

HERE = os.path.dirname(os.path.abspath(__file__))
ids = sys.argv[1:] or ["bix-10", "bix-16", "bix-17"]

ds = load_dataset("futurehouse/BixBench", split="train")
by = {r["short_id"]: r for r in ds}
os.makedirs(os.path.join(HERE, "instances"), exist_ok=True)

for sid in ids:
    r = by[sid]
    inst_dir = os.path.join(HERE, "instances", sid)
    data_dir = os.path.join(inst_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    # capsule zip
    zp = hf_hub_download("futurehouse/BixBench", r["data_folder"], repo_type="dataset",
                         local_dir=os.path.join(HERE, "capsules"))
    with zipfile.ZipFile(zp) as z:
        for n in z.namelist():
            # expose ONLY CapsuleData/* ; never the solution notebook
            if "/CapsuleData-" in ("/" + n) or n.startswith("CapsuleData-"):
                if n.endswith("/"):
                    continue
                base = n.split("CapsuleData-", 1)[1].split("/", 1)[-1]
                if not base:
                    continue
                dst = os.path.join(data_dir, os.path.basename(base))
                with z.open(n) as src, open(dst, "wb") as out:
                    shutil.copyfileobj(src, out)
    meta = {k: r[k] for k in ("short_id", "question", "ideal", "eval_mode",
                              "hypothesis", "categories", "data_folder")}
    meta["data_files"] = sorted(os.listdir(data_dir))
    with open(os.path.join(inst_dir, "meta.json"), "w") as f:
        json.dump(meta, f, indent=1)
    print(f"{sid}: {len(meta['data_files'])} data files, ideal={r['ideal']!r}")

print(f"\nprepared {len(ids)} instances under instances/")
