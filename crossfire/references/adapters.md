# Crossfire execution adapters (Phase 2 — `run` tool)

Stub. The `run` tool (actually execute the target and validate its outputs) is **Phase 2**,
opt-in via `tools=+run`. Phase 1 ships lenses + codex + health only.

Planned adapters (per project type), each: detect → run command → output checks → hard timeout (default 300s):

- **python-script / pipeline**: run on sample/real input → exit 0, no exception → validate outputs
  (file created & loadable, e.g. AnnData `.h5ad` / non-empty DataFrame; shape; no unexpected all-NaN;
  value ranges; plots produced; reproducibility: seed set, re-run gives same key stats).
- **notebook**: `jupyter nbconvert --execute` → error cell = P1; output sanity.
- **cli**: `--help` + one real invocation → exit/stderr/output checks.
- **server/service**: start → health/smoke request → log errors.
- **web frontend** (`url=`): gstack browse daemon → `goto / console --errors / snapshot / perf`.
- **library**: tests + a representative usage example.

Rules: if an adapter needs input and none is provided, ask once, else skip with a note.
Long runs → hard timeout → mark `inconclusive` and continue. Reuse project-type detection
patterns from the `run` / `verify` skills.
