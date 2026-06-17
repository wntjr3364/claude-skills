# Crossfire lenses — catalog, signal routing, prompts, return schema

Each lens is one adversarial sub-agent (`Agent`, subagent_type `Explore`, read-only).
The orchestrator selects 2–6 lenses per Step 2 and gives each the template below
plus the verification subject (diff or file contents).

## Worker return schema (REQUIRED)

Every lens **and** the Codex pass must end their output with a single strict JSON block:

```json
{
  "findings": [
    {
      "severity": "P1|P2|P3",
      "location": "path:line  (or plan section)",
      "bug_type": "logic|bounds|type|race|security|perf|resource|style|missing-case|api-contract|data-validity|methodology|other",
      "claim": "one-sentence description of the flaw",
      "evidence": "concrete reason / snippet / why it fails",
      "fix": "suggested remedy",
      "confidence": "high|med|low"
    }
  ]
}
```

The orchestrator parses ONLY this block. If it is missing or unparseable, treat that
worker's result as `inconclusive`, retry once, then note it as a gap in the report.

**Phase 2 (cycles>1)** — the same block additionally carries an `acks` array reporting the
current status of every carried-over item the worker was asked to re-verify:

```json
{
  "findings": [ { …same finding fields… } ],
  "acks": [
    { "id": "<carried id>", "status": "fixed|still-failing|regressed|inconclusive", "evidence": "what you checked" }
  ]
}
```

Phase 1 needs only `findings`. In Phase 2 a worker MUST return an ack for each carried
`unresolved` + recently-`fixed` id it was given (silence on a carried item is a gap that fails the gate).

## Mandatory lenses (always selected)

| lens | code mode focus | plan mode focus |
|---|---|---|
| `correctness` | logic errors, wrong conditions, off-by-one, contract violations | feasibility, internal consistency, will-it-actually-work |
| `edge-cases` | empty/null/boundary inputs, error paths, failure modes | missing cases, unhandled states, rollback gaps |

## Signal-triggered lenses (added when the signal fires)

| lens | trigger signal (detectors) | priority |
|---|---|---|
| `security` | files/paths matching auth/login/secret/token/crypto; input parsing; network/HTTP; `subprocess`/`eval`/`os.system`; SQL; `gstack-diff-scope` SCOPE_AUTH | 1 (never dropped) |
| `data-validity` | numeric/array/dataframe code; imports `numpy/pandas/scipy/scanpy/anndata/sklearn/torch`; `.ipynb`; stats/ML; bioinformatics | 2 (never dropped) |
| `concurrency` | `thread`/`async`/`await`/`asyncio`/`lock`/`mutex`/multiprocessing | 3 |
| `performance` | nested loops over large data, O(n^2) patterns, heavy IO, large file/array ops | 4 |
| `api-contract` | changes to a public signature / exported interface / CLI args / schema | 5 |
| `simplicity` | large or complex diff (many lines/branches), duplication, over-engineering | 6 |

**Selection rule:** mandatory (2) + triggered, clamped to 6. When the cap binds, keep by
priority number ascending; `security` and `data-validity` are never dropped once triggered.
Detect signals from file extensions, imported libraries (grep the subject), and — when in a
git repo — `~/.claude/skills/gstack/bin/gstack-diff-scope`. Non-git: use path/content heuristics.

## Lens prompt template (code mode)

> You are an ADVERSARIAL `<LENS>` reviewer. Your job is to BREAK this code, not praise it. No compliments.
> Subject (changed code / files):
> ```
> <DIFF OR FILE CONTENTS>
> ```
> Through the **`<LENS>`** lens specifically (`<LENS FOCUS>`), find concrete flaws. For each:
> default to reporting a real problem only when you can point to specific evidence.
> Be specific about location. Do not invent issues to look thorough — but do not let a real one slide.
> End your output with the required JSON block (schema above). Return `{"findings": []}` if you genuinely find nothing.

## Lens prompt template (plan mode)

> You are an ADVERSARIAL `<LENS>` reviewer of a DESIGN/PLAN document. No praise. Try to find where this plan
> fails when implemented. Subject:
> ```
> <PLAN TEXT>
> ```
> Through the **`<LENS>`** lens (`<LENS FOCUS>`), find concrete gaps, contradictions, or unrealistic assumptions.
> Cite the exact section/line. End with the required JSON block. Return `{"findings": []}` if nothing.

## Carry-over block (Phase 2, prepended to every worker prompt when cycle>1)

> CONTEXT FROM PRIOR CYCLES (you are stateless; this is everything you know about earlier work):
> - Unresolved items to RE-VERIFY (report each in `acks`): for each, state fixed | still-failing | regressed | inconclusive with evidence:
>   `<id> · <status> · <one-sentence claim>`  …(repeat)…
> - Fixes applied in the previous cycle (check for regressions): `<diff or summary>`
> - Already-closed items (do NOT resurface unless you have strong new evidence): `<id · status>` …
>
> Your job this cycle: (a) do NOT re-report a known item as a NEW finding; (b) for each carried item above,
> explicitly verify its current state and put it in `acks` (no silence); (c) find any NEW issues not in the list.
> Detailed evidence for any id is in `$RUN_DIR/findings.jsonl` if you need it.

## Codex (reviewer) — not a Claude lens

Codex runs synchronously as a separate reviewer (see `references/tools.md` for the command).
Its `[P1]/[P2]/[P3]` output is parsed into the same finding shape (source = `codex`).
