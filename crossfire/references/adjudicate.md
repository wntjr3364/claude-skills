# Step 4.5 — Second-pass review (the orchestrator confirms findings)

The lenses and Codex produce a **first-pass** review. Before findings reach the user
or the gate, the orchestrator (you, the main agent) gives each one a **second-pass
review** — confirming it against the real code, preferably empirically. This is a
normal review-of-the-review, **not distrust of the lenses**: the point is to back real
issues with evidence and catch the occasional false-positive or by-design nitpick.
**Bias toward keeping findings** — reject only with positive evidence; when you can't
confirm either way, mark `uncertain` and keep it. (Sometimes the second pass also
*strengthens* a finding or surfaces one the lens under-rated — that's fine too.)

## Per-finding review (prioritize P1/P2; batch P3)

For each consolidated finding, decide a **verdict** with YOUR OWN evidence:

1. **Verify against reality — empirically when you can.** Don't re-reason; *check*.
   - **Read the cited location yourself** (the orchestrator can `Read`/`Grep` the
     real file — you are not limited to what the lens reported).
   - **Prove it with a cheap probe** where feasible — this is the strongest signal:
     - regex/string claim → run it: `python3 -c "import re; print(bool(re.search(PAT, 'claimed input')))"`
     - function behavior → a 3-line repro / call with the claimed input
     - "test doesn't cover X" → grep the test file
     - "crashes on empty" → actually call it with `[]`
   - Reasoning-only confirmation is the **fallback**, not the default.
2. **Weigh corroboration.** How many *independent* sources flagged it? Any
   empirical (health) backing? One low-confidence lens with no code-verification is weak.
3. **Judge severity & intent.** Is it a real defect, or **by-design / a nitpick /
   a style preference / a known trade-off**? Downgrade or reject over-strict calls.
   (e.g. "single-element list normalizes to 0" may be intended, not a bug.)

## Verdicts

- `confirmed` — you checked it and it holds (cite your evidence: the probe result / the code you read).
- `uncertain` — plausible but you couldn't confirm either way. **This is the default when unsure — keep it**, don't reject for lack of a quick repro.
- `rejected` — you have **positive evidence** it's wrong / by-design (cite WHY). Not "I didn't bother to check."

Severity may be **adjusted** either way (e.g. lens said P1 but your repro shows it only
fires on implausible input → P3; or a lens under-rated something you confirmed is worse).
Record original vs adjudicated severity. The goal is accuracy, not minimizing the count.

## How verdicts flow

- The **gate** uses only `confirmed` findings (and surfaces `uncertain` as flagged,
  not gating). `rejected` never gates.
- **`rejected` findings are NOT dropped silently** — list them in a
  "Filtered (likely false-positive / by-design)" section with your reason. The
  filtering must be auditable so the user can override your judgment.
- **Never assert an unverified finding as fact.** If you couldn't check it, say so (`uncertain`).
- Under `fix=apply`, only `confirmed` findings are eligible for auto-fix.

## Optional extra rigor — `--refute`

For maximum confidence on `confirmed` P1s, spawn N independent skeptic sub-agents
each told to REFUTE the finding (prove it's NOT a real bug); keep it only if it
survives the majority. Off by default (orchestrator-direct adjudication is the
default the user asked for); use when the cost of a wrong P1 is high.

## Worked example (from a real run)

Lens claim: *"normalize() single-element list returns [0.0] — semantically odd (P3)."*
Adjudication: read the code → the `rng==0` guard is intentional; a 1-element list
having no spread → 0 is the defined behavior, not a defect. **Verdict: rejected
(by-design).** → goes to the Filtered section, does not gate.

Lens claim: *"non-GM regex drops BAO:0000241 even when a separate modified sample is in the same blob (P1)."*
Adjudication: `python3 -c "import re; print(bool(PAT.search('non-GM control vs the genetically modified line')))"`
→ `True`, and the code removes 241 unconditionally for the whole blob. **Verdict:
confirmed (empirically reproduced).** → gates.
