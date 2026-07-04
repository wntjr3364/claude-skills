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
