# fable — postmortem (discarded 2026-07-06)

`fable` was a skill that tried to distill Fable-class **operating discipline**
(outcome-first reporting, an end-of-turn completion gate, evidence-matched actions,
delegation economy, empirical verification, honest degrade) into a prompt contract +
two pre-stop gates, so a weaker model (Opus/Sonnet) would work more like Fable. It was
built and hardened well (5-cycle crossfire convergence). It was then **empirically
validated — and the validation failed to show any benefit.** Discarded on the evidence.

## What the evaluation found

| instrument | result |
|---|---|
| SWE-bench Verified (12 django, on vs off, skill confirmed loaded) | pass@1 33%=33% (sonnet), 67%=67% (opus). Identical instances resolved, McNemar p=1.0, 0% gap-closure vs the Fable 5 ceiling (75%). Discipline signals (ran-tests/verified/regression) all flat. Cost +10% sonnet / +52% opus. |
| BixBench (bioinformatics, n=3 smoke) | vanilla 2/3, fable 2/3, fable5 2/3 — identical; fable and vanilla gave the same wrong answer on the hard question. Process (uncertainty honesty) also flat. Cost +48%. |
| BixBench + biostack condition | biostack (a proven domain-methodology skill pack) also 2/3 — same as everything, including vanilla's exact wrong answer. |

## Why it failed to show value

1. **Wrong instrument, consistently.** SWE-bench and BixBench measure task-solving
   **capability** (produce the right patch / the right number). fable changes
   **discipline**, not capability. On easy tasks everyone succeeds (no gap); on hard
   tasks everyone fails the same way (capability wall). The thin discipline-bottleneck
   middle isn't captured by aggregate binary accuracy.
2. **The value of a discipline/review tool shows up as flaw-detection**, not as a better
   answer on a well-posed task. The same null hit even biostack — so this is about the
   *class* of tool, not fable specifically. The instrument that *can* measure such tools
   is a review / flaw-detection benchmark (e.g. biostack's own eval, where biostack is
   proven), which was not fable's framing.
3. **It is not free.** The contract adds real token/turn overhead (up to +52% on Opus)
   with no measured return on these tasks.

## Lessons kept

- **Validate a skill's EFFECT before trusting it.** Build-and-review only proves internal
  consistency; the claimed behavioral benefit is a separate empirical question. Here the
  A/B did its job — it caught a null that "it passed crossfire" would have hidden.
- **Match the benchmark to what the skill claims to change.** A discipline/review skill
  must be measured on a review/flaw-detection benchmark, not a task-solving one.
- **Prompt scaffolding can't buy capability**, and generic discipline (fable) did not even
  beat plain on discipline-adjacent metrics where domain methodology (biostack) is proven.

The eval harness (SWE-bench + BixBench runners, isolated-config + transcript-discipline
extractors, biostack-as-condition wiring) and the results were removed with the skill;
this note preserves the conclusion.
