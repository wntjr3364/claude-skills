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

## Token / cost (the skill is not free)

Per-run averages (12 django instances): fable overhead on vs off —
- **sonnet: +10% cost** ($0.639→$0.703), output +6%, turns 25.8→29.7
- **opus: +52% cost** ($1.029→$1.564), output +46%, turns 23.4→31.4
- fable5-ref: $2.139/run, 75% pass@1

fable makes the model do MORE (extra verification steps → more turns/tokens) but on
capability-bound tasks that buys no pass@1 → on the wrong tasks it is pure wasted cost,
and the waste is large on Opus (+52%).

## Regression avoidance (another discipline proxy, also flat)

Did the agent's patch break an existing PASS_TO_PASS test? sonnet off 2 → on 2; opus off
1 → on 1. The SAME instances (10097, 11141) regress across every condition including
Fable 5 — capability-bound, not discipline. So ALL four discipline measures (pass@1,
ran_tests, verified_after_edit, regression-avoidance) are flat: SWE-bench django has no
discipline headroom for fable to act on.
