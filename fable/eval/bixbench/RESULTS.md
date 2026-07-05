# BixBench (bioinformatics domain) A/B — smoke results (2026-07-04)

Path B: subscription `claude -p` + real `/fable` skill, local Python scientific env,
capsule solution-notebooks withheld. **Smoke only: 3 questions × {sonnet-off, sonnet-on,
fable5-ref}.** n=3 is not a verdict — a signal check.

## Accuracy (blind LLM judge vs ideal)

| condition | correct | avg turns | $/run |
|---|---|---|---|
| sonnet-off | 2/3 | 13 | 0.389 |
| sonnet-on | 2/3 | 13 | 0.577 (+48%) |
| fable5-ref | 2/3 | 10 | 0.466 |

Per question: bix-16 (% DEGs) and bix-17 (median) — **all three correct** (easy, no
discrimination). bix-10 (odds-ratio reduction with covariates) — **all three wrong**,
including Fable 5 (capability wall). No question landed in a discipline-discriminating
middle.

## Process check (bix-10, the shared failure)

Both sonnet-off and sonnet-on gave a **confidently wrong** answer with ZERO
uncertainty/caveat language — fable's "honest about uncertainty / don't overclaim"
discipline did not fire where it would have mattered most. Flat on process too.

## Conclusion (consistent with SWE-bench)

Same structural pattern as the code benchmark: easy tasks → everyone succeeds (no gap);
hard tasks → everyone fails (capability); the thin discipline-bottleneck middle isn't
captured by aggregate binary accuracy. fable moved **nothing** (accuracy, process) and
added cost (+48% on sonnet here). This is a smoke (n=3), not a domain verdict — but it
mirrors SWE-bench exactly, so scaling is unlikely to flip it without deliberately
selecting discipline-bottleneck questions (which reintroduces author bias).

## + biostack condition (user's domain methodology, /biostack-analyze)

Added biostack as a 4th condition (agent solves via /biostack-analyze). Result on the
same 3 questions: **biostack 2/3 — identical to vanilla / fable / fable5.** On the hard
bix-10, biostack returned **exactly 3.10%**, the same wrong answer as vanilla (target
24-26%); its methodology did not change the analysis approach. Validity note: the
/biostack-analyze command DID load and drive the analysis loop (Bash), but did NOT invoke
its reporting sub-skills (Skill calls = 0) — biostack's own README warns skill routing is
best-effort; the deterministic plugin machinery (hooks, bin CLIs) was not in play.

## Why even biostack is null here — the real lesson

BixBench measures **task-solving answer accuracy** (did you compute the right number).
Both fable (generic discipline) and biostack (domain methodology) are **discipline/review
tools** — their value is catching errors / not cutting corners, which shows up as
**flaw-detection**, not as a better analysis number on a well-posed question. So on a
capability/interpretation task like bix-10 (everyone makes the same modeling-choice error),
neither moves the answer. This is the SAME structural miss as SWE-bench.

**Key implication:** the instrument that CAN measure these tools is a **review /
flaw-detection benchmark** (does the model catch planted flaws?), not a task-solving one.
biostack already HAS exactly that (its own eval: biostack > vanilla at catching planted
bugs) — and it is proven there. A task-solving benchmark (BixBench, SWE-bench) is the
wrong instrument for a discipline/review tool, whether that tool is fable or biostack.
