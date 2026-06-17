# crossfire

One-command **adversarial + empirical** verification for code or a plan doc.
Spawns an auto-selected set (2–6) of parallel adversarial Claude lenses + a
synchronous Codex review + the project's own tests/typecheck/lint (health),
consolidates findings by severity with stable IDs, and reports (or applies) fixes.
Works **without git** (explicit target + snapshot diff). Persists to
`~/.gstack/crossfire/runs/<run>/` (outside your repo).

## Quick usage

```bash
/crossfire                                  # auto-detect git diff / plan
/crossfire path=src/foo.py fix=report       # read-only review (default)
/crossfire path=src/foo.py cycles=3 fix=apply   # fix → re-verify convergence loop
/crossfire path=mod.py tools=+security,+stats   # opt-in domain reviewers
/crossfire path=plan.md mode=plan           # review a plan doc (always report-only)
```

Args: `path=` · `mode=auto|code|plan` · `fix=report|apply` · `cycles=N` ·
`lenses=auto|N|csv` · `tools=+security,+stats,+perf,+visual|none` · `url=` ·
`resume=<run>` · `--full-audit`.

## Files

- `SKILL.md` — orchestrator (preflight → target → lens panel → consolidate → gate → report/persist).
- `references/lenses.md` — lens catalog, signal→lens routing, prompt templates, worker return schema (+ Phase-2 `acks`).
- `references/tools.md` — tool registry (codex/health + opt-in cso/benchmark/design-review/scientific-skills).
- `references/cycles.md` — **Phase 2**: ledger, carry-over brief, acknowledgment contract, convergence, checkpoint, resume.
- `references/adapters.md` — **Phase 3** stub (script/notebook/CLI/web execution adapters — not built).

## Status

- **Phase 1 (single pass)** — built + validated (4/4 planted bugs found on a non-git file).
- **Phase 2 (cycles + carry-over + acknowledgment)** — built + validated (fix→re-verify, acks, convergence, gate PASS).
- **Phase 3 (execution adapters, multi-run trends, custom lens sets)** — deferred.

Validated paths: non-git + **git** code mode, lens auto-select, sync Codex (scoped
guard), health baseline, cycles=2 carry-over/acks. Implemented-but-lightly-exercised:
`mode=plan`, opt-in `tools=+…`, `resume=`, large-cycle checkpointing.

## Design provenance

Designed and hardened through 3 rounds of its own adversarial + Codex review
(see the design plan). It surfaces *candidate* findings — a domain expert
adjudicates which are real; crossfire's strength is code/logic + methodology, not
adjudicating individual data records.
