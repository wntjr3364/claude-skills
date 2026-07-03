# fable

Push any model in a Claude Code session **toward the way Fable works** — by injecting
an explicit operating contract (distilled Fable-class discipline) plus two hard
pre-stop gates. Aimed at Opus/Sonnet/Haiku sessions: same tasks, more disciplined
behavior (see the honest cap below — this is scaffolding, not a capability upgrade).

## Quick usage

```bash
/fable                       # adopt the discipline for the session (best-effort: prompt-level,
                             # survives as long as context does — re-invoke to re-anchor)
/fable fix the flaky test in tests/test_io.py    # wrap one task in it
/fable off                   # drop the contract
```

## What it changes (and what it can't)

**Changes** — the failure modes that separate a weaker-model session from a Fable one:

| Failure mode | Contract answer |
|---|---|
| Stops on "I'll do X next" instead of doing X | Gate A: end-of-turn completion check |
| Buries the answer mid-turn / trails off | Gate B: outcome-first, self-sufficient final message |
| Blindly applies what a sub-agent/reviewer said | Verify: empirical beats agreement |
| Restarts/deletes on a pattern-match | Act: evidence must support the *specific* action |
| Burns context reading whole files serially | Context economy: delegate sweeps, parallel calls, narrow reads |
| Over-hedged or over-claimed reports | Honest degrade: failures verbatim, skips named, done stated plainly |

**Can't**: raise reasoning capability. This is prompt scaffolding — expect Fable-like
*reliability and communication*, not Fable-level intelligence. The skill says so itself.

## Files

- `SKILL.md` — orchestrator: fit-check → adopt contract → execute → gate every stop.
- `references/contract.md` — the five-section operating contract (Orient / Context
  economy / Act / Verify / Report).
- `references/gates.md` — Gate A (may I stop?) and Gate B (is the final message
  readable and honest?), written to be re-run literally every turn.

## Design notes

- Third sibling in this workspace: `crossfire` verifies **code/plans**, `assay` grades
  **data rows**, `fable` upgrades **the operator itself**. Fit-check cross-refers.
- No `allowed-tools` restriction on purpose — it's a behavioral wrapper; the wrapped
  task dictates the tools.
- Precedence is explicit: system rules, the active permission/plan mode, project
  CLAUDE.md, and more-restrictive concurrent skills always win; the contract only adds
  discipline. Explicit user instructions override it too (with a one-clause honest
  note when discipline is skipped). Plan mode in particular: presenting a plan and
  stopping for approval is a valid stop, carved out of Gate A explicitly.
- Instruction decay is the known killer of "behavioral" prompts, so the gates are
  deliberately short, verbatim checklists, SKILL.md orders re-reads at natural
  boundaries — and the skill is honest that adoption is prompt-level: after heavy
  compaction the contract can be lost, and the durable fix is re-invoking `/fable`
  (idempotent), not a pretended guarantee.
