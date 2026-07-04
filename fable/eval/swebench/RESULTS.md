# SWE-bench Verified A/B — results (2026-07-04)

12 django instances, 1 seed, isolated clean config. Skill-on confirmed loaded in
**28/28** on-transcripts (read refs / Skill tool / contract language). Empty patches
(hard tasks the weaker model couldn't solve in budget) count as unresolved.

## pass@1 (official swebench Docker eval) — the rigorous metric

| condition | resolved | pass@1 | Wilson 95% |
|---|---|---|---|
| sonnet-off | 4/12 | 33% | 17–69% (of 10 completed: 40%) |
| **sonnet-on** | **4/12** | **33%** | identical instances |
| opus-off | 8/12 | 67% | 39–86% |
| **opus-on** | **8/12** | **67%** | identical instances |
| fable5-ref (ceiling) | 9/12 | 75% | 47–91% |

**On-vs-off (McNemar, shared instances):** sonnet Δ0, opus Δ0. **The exact same
instances resolved in both conditions** (sonnet: 10880/10914/11095/11138; opus: those +
10554/10973/11087/11885). McNemar p = 1.000. **gap-closure vs Fable 5 = 0%.**

## Discipline signals (from full transcripts incl. tool calls — the real signal)

| condition | ran_tests | verified_after_edit | avg test-runs |
|---|---|---|---|
| sonnet-off | 92% | 83% | 6.2 |
| sonnet-on | 83% | 75% | 5.3 |
| opus-off | 100% | 83% | 4.7 |
| opus-on | 100% | 92% | 7.3 |
| fable5-ref | 100% | 100% | 5.8 |

Paired: sonnet ran_tests Δ−1 / verified Δ−1; opus ran_tests Δ0 / verified Δ+1 — all
within ±1 instance = noise at n=12.

## Honest conclusion

**fable produced no measurable benefit on this benchmark, and we can say why.**

1. **Capability-bound.** SWE-bench pass@1 rewards producing the correct patch; the
   failures here are the model not knowing the fix, which a prompt can't supply. The
   Fable 5 ceiling (75%) vs Sonnet (33%) is a real *capability* gap the skill doesn't
   touch — consistent with the skill's own "discipline, not capability" claim.
2. **No discipline headroom.** Even with the skill OFF, Sonnet/Opus already ran tests
   (92–100%) and verified after editing (83%) on these tasks — because on a well-scoped
   "make the test pass" task, running the test is the obvious move. There is almost no
   discipline gap for fable to close, so it doesn't.
3. Therefore **SWE-bench is the wrong instrument to detect fable's intended value.** The
   skill targets discipline where the right action is *non-obvious* or where weaker
   models cut corners (finish without a full re-check, trust a wrong suggestion, report
   dishonestly). SWE-bench stresses neither.

fable's benefit therefore remains **plausible but unproven on unbiased tasks.** The only
place it visibly separated models is the author-built behavior traps (Fable 5 aced all 3;
Sonnet-on still fell for premature-stop) — a biased instrument. A fair discipline
benchmark (independently-generated, discipline-bottlenecked tasks, transcript-judged)
would be needed to actually prove or refute the skill's value.
