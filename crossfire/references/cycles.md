# Crossfire Phase 2 — cycles, carry-over brief, acknowledgment contract

Triggered when `cycles=N` with N>1 (default 1 = Phase-1 single pass). Recommend `cycles ≤ 5`.
**You (the orchestrator, the single-turn main agent) are the only durable memory.** Sub-agents are
stateless workers; carry-over works because YOU hold the ledger across cycles and inject a summary
into each new worker's prompt — not because sub-agents talk to each other.

## Ledger (single source of truth)

Held in your context AND persisted to `$RUN_DIR/findings.jsonl`. Append-only; on load, **latest record
wins per `id`**. Each finding record:
`id · severity · bug_type · location · claim · evidence · fix · confidence · sources · verdict · status · cycle_found · cycle_resolved`
(`verdict ∈ {confirmed, uncertain, rejected}` — assigned by the orchestrator in adjudication, Step 4.5.)

`status ∈ {open, fixed, still-failing, regressed, rejected, deferred, obsolete}`.
`unresolved = {open, still-failing, regressed, deferred}`.

Transitions (each requires `source` + `evidence`):
- `open` → `fixed` (fix applied AND verified) | `still-failing` (re-verify failed) | `rejected` (refuted) | `deferred` (reason) | `obsolete` (target code gone)
- `fixed` → `regressed` (regression found later)
- `still-failing`/`regressed` → `fixed` (later fix verified)
- Illegal transitions (e.g. `fixed`→`open` without cause) are rejected.

## The loop — for cycle k = 1..N

1. **Build the carry-over brief** (k>1 only), from the ledger:
   - **ALL `unresolved` items**, each compressed to `id · status · one-sentence claim` (evidence stays in the
     ledger; a worker may read `findings.jsonl` for detail). Never drop unresolved P1/P2.
   - **Cycle k-1's applied fixes** (diff/summary) — for regression checking.
   - **Closed** items (`fixed`/`rejected`/`obsolete`) as `id · status` one-liners.
   - **Token cap ≈ 3.5k** for the brief. If exceeded, move oldest *low-severity* unresolved to `deferred`
     (note it); P1/P2 are never dropped.
2. **Persist the injected prompt** per worker to `$RUN_DIR/cycle_k/<lens>.prompt.md` and `cycle_k/codex.prompt.md`
   (mask secrets: `AKIA…`, `BEGIN … PRIVATE KEY`, `api_key=…`, tokens → `[REDACTED]`; full text only with `--full-audit`).
3. **Run the panel** (lenses + codex + health) with the brief injected (k>1). Each worker returns the
   **Phase-2 return schema** (`findings` + `acks`, see `references/lenses.md`).
4. **Acknowledgment cross-check** (k>1): for every carried `unresolved` + recently-`fixed` id,
   confirm at least one worker returned an ack.
   - Apply ack status updates (`fixed`/`still-failing`/`regressed`) to the ledger (with evidence).
   - `inconclusive` ack → keep prior status.
   - **Any carried unresolved P1/P2 with no ack, or only `inconclusive` acks across all workers → mark it
     `still-failing`/inconclusive and it FORCES the gate to FAIL** (not merely a logged gap).
5. **Second-pass review of NEW findings** (Step 4.5 / `references/adjudicate.md`) — re-check each against
   the code, assign a `verdict`; `confirmed`/`uncertain` enter the ledger as `open`, `rejected` go to the
   Filtered list. Then **merge** (id not seen before). Dedup by id.
6. **Regression section**: for each file/function changed by cycle k-1's fixes, record `checked_by`
   (health|codex|lens) + evidence; anything unverified → `inconclusive`.
7. **If `fix=apply`**: auto-edit only `open` items that are **`confirmed` with an executable reproduction**
   (Step 4.5 form (i)). Apply each through the **apply → verify → keep-or-revert loop immediately this cycle**
   (re-run its reproduction fail→pass + health no-regression; else revert + downgrade the verdict) — do **not**
   defer verification to the next cycle. Record fix + before/after in the ledger and `cycle_k.md`; a kept fix is
   marked `fixed` now (the next cycle's ack re-checks for regression). **Confirmed-but-cited-only (form (ii)) and
   `uncertain` items are reported suggestions, not auto-edited.** **Taste / User-Challenge** → `AskUserQuestion`.
   Never edit a plan doc without approval.
8. **Write `cycle_k.md`** journal: lenses run + trigger signals, fixes applied + diff, decisions
   (Mechanical/Taste/Challenge), gate result, regression section, ack coverage (`unresolved N carried / M acknowledged`).
9. **Convergence check** — STOP when **all** hold: (new-open this cycle == 0) AND (regressions == 0) AND
   (gate satisfied: no unresolved P1, every unresolved P2 deferred-with-reason, no unack/inconclusive unresolved P1/P2).
   Otherwise continue to cycle k+1.
10. **Bound / auto-checkpoint**: if ledger findings > ~100 OR tokens used > ~150k, checkpoint to disk, tell the
    user to re-run with `resume=<run>`, and stop the turn (best-effort one turn).

**End condition:** N reached with unresolved P1 → **gate FAIL** (report it). Otherwise gate PASS at convergence.

## `resume=<run>`
Load `$RUN_DIR/findings.jsonl` (latest-wins per id), recompute `unresolved`, **hash current target files vs
`baseline/`** → note external drift, then continue from the next cycle.

## Gate (final)
PASS iff: no `unresolved` P1 **and** every `unresolved` P2 is `deferred` with a reason **and** no carried
unresolved P1/P2 left unacknowledged/inconclusive.
