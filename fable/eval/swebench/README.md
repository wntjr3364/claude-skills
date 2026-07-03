# SWE-bench Verified — discipline-instrumented A/B for fable

The **external, non-author** benchmark for fable's real effect (the behavior-trap tasks
one level up are author-built pilots; this is the "proper benchmark data"). Runs
SWE-bench Verified tasks with the skill on vs off across Sonnet/Opus, plus Fable 5 as the
reference ceiling, and measures **two** things:

- **Outcome (pass@1)** — the official swebench Docker harness scores resolved/unresolved.
  This is realized task performance; fable can move it on behaviorally-limited tasks.
- **Discipline signals** — extracted from the agent transcript: did it run the tests, did
  it verify before claiming done, did it avoid overclaiming, did it report failures
  honestly. fable should move these even where pass@1 doesn't.

## Why django-only

Django is pure-python and pip-installs fast, so the agent phase (host checkout + editable
install) is light enough that the agent can actually run the test suite in-place — which
is the discipline signal we need to observe. Django is also the largest slice of Verified
(231 tasks), so the subset is easy to scale. `prepare_subset.py` samples deterministically
across difficulty bands (favoring the discriminating 15min–4h middle).

## Pipeline (proven end-to-end on django-10097 + a gold-patch probe)

1. `./setup-clean-config.sh` (one level up) — isolated config, no codex contamination.
2. `python3 prepare_subset.py 12` — pick the subset, write `instances/*.json` + `subset.txt`.
3. `./agent_run.sh <inst> <cond> <seed>` — clone@base, editable install, run `claude -p`
   (skill on/off), capture `git diff` as the prediction patch.
4. `eval_and_score.py predictions` — assemble per-condition predictions.
5. `swebench.harness.run_evaluation` — official Docker eval → resolved/unresolved.
6. `eval_and_score.py signals` — transcript discipline table (heuristic first pass; the
   blinded judge in `../judge-prompt.md` is the authoritative grader).

`./run_batch.sh "<conditions>" [seed]` drives all of it.

## Cost (measured)

- Gold-patch eval probe: **resolved in ~42 s** (Docker image pulled + test run).
- One agent run (Sonnet, django-10097): **$0.75, 38 turns, ~4 min**; produced a correct
  24-line patch and — even with the skill OFF — ran tests and reported the 2 pre-existing
  failures honestly.
- Full first slice = 12 instances × 5 conditions × 1 seed = **60 agent runs** (~$60–90 mixed
  models) + 60 evals (12 unique images, cached) + judging. Several hours wall-clock.

## Pre-registered readout

- **pass@1**: on vs off per model, McNemar paired test on the 12 instances.
- **discipline**: per-signal on-vs-off rate + Wilson CI (reuse `../aggregate.py` shape).
- **gap-closure vs Fable 5** on discipline signals.
- Guardrail: if pass@1 doesn't move but discipline signals do → the subset was
  capability-limited, not behavior-limited (still informative; report it, don't bury it).

## Honest limits

- n=12, 1 seed → wide CIs. This is a first slice for signal; scale instances/seeds before
  any strong claim.
- django-only → results may not transfer to other repos/domains.
- The agent-phase host install may under-provision some tasks' test deps; a task where the
  agent *couldn't* run tests for env reasons is not a discipline failure — flag and exclude.
