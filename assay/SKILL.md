---
name: assay
description: |
  Grade a set of candidate rows/claims for ACCURACY with a panel of independent
  skeptical judges. For each row, N judges render a structured verdict (e.g.
  correct / wrong_term / wrong_context / too_narrow / too_broad / cannot_judge),
  votes are aggregated by a kill rule (e.g. >=2/3 not-correct), and precision is
  scored (Wilson CI — reusing the project's scorer when present). Use when
  measuring the accuracy of DATA outputs: ontology mappings, extraction/curation
  rows, labeled candidates, any CSV/table of items to adjudicate. NOT for reviewing
  code or a plan for bugs -> use `crossfire`. Sibling to crossfire (data <-> code).
argument-hint: "[input.csv] [axis=...] [judges=N] [verdicts=csv] [kill=...] [cycle=N] [score=auto|none] [out=path]"
user-invocable: true
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, Agent, AskUserQuestion, Skill
metadata:
  short-description: Multi-judge accuracy adjudication for data rows (1 command)
---

# assay — multi-judge accuracy adjudication (data rows / claims)

You are the **orchestrator**. `/assay` grades a set of candidate items (rows of a
CSV/table) for **accuracy**: for each item you spawn N independent skeptical judges,
aggregate their verdicts by a kill rule, then score precision (reusing the project's
scorer when present). This is the data-side sibling of `crossfire` (which verifies
code/plans). You are the single durable memory; the judges are stateless workers.

References (read the one you need before the step that uses it):
- `references/judges.md` — judge prompt templates, verdict enums (fine + coarse rollup), per-axis rubric, return schema, kill/aggregate rule.
- `references/scoring.md` — judged-CSV format, how to hand off to the project's scorer (Wilson CI), fallback scorer, cycle comparison.

---

## Step 0 — Fit-check (is assay the right tool?) + parse args

**Decide fit before doing anything.** assay grades **a set of items/rows for accuracy**
(a CSV/table where each row is a candidate to be judged correct vs not).
- Target is **code / a diff / a plan** ("is this code correct? any bugs?") → **stop and
  recommend `/crossfire`** (the sibling for code/plans). Do not grade code as rows.
- **Not a verification/grading task** at all ("write X", "explain Y") → say assay doesn't
  fit; do it directly without a skill (or suggest a better one).
- It **is** a row/claim accuracy task → proceed.
Never force a non-fitting request into assay's shape.

Then parse args (all optional): `input.csv` (or first bare arg) · `axis=` (genotype|peco|
tissue|dev_stage|… or generic) · `judges=N` (default 3) · `verdicts=` (csv enum; default the
fine set in `references/judges.md`) · `kill=` (default `>=2/3 not-correct`) · `cycle=N` ·
`score=auto|none` (default auto) · `out=` (judged-CSV path; default `<input>_judged.csv`).

## Step 1 — Load input + pick rubric

Read the CSV. Identify the **item key** (e.g. `run_accession`+`term_id`) and the **evidence
columns** the judges need (sample_title, sample_description, isolation_source, scientific_name,
library/source, confidence/band, …). Choose the **axis rubric + verdict enum** (`references/judges.md`);
for a known axis use its rubric, else a generic "is this label correct for this item?" rubric.
Disclose the plan + cost before running (items × judges, est. wall-time).

## Step 2 — Run the judge panel (the harness you used to do by hand)

For each item (batch rows; cap concurrency), spawn **N independent judges** — one `Agent`
(subagent_type `Explore`, read-only) per judge — each given: the item's term/label + its
evidence columns + the axis rubric, and the **skeptical claim-verifier** framing from
`references/judges.md` ("be skeptical; try to refute that this label is correct"). Each judge
returns a **structured verdict** (enum + one-line reason) in the return schema. Judges are
independent (don't share). Persist each judge's prompt under the run dir (mask secrets).

## Step 3 — Aggregate per item

Combine the N verdicts per item → **consensus verdict** + apply the **kill rule** (e.g.
`>=2/3 not-correct` → mark the label wrong). Record vote split + disagreement. Roll the fine
verdict up to coarse `correct|incorrect|ambiguous` for scoring (mapping in `references/judges.md`).

## Step 4 — Second-pass on contested items (don't blind-trust the majority)

Like crossfire's adjudication: for **split / low-agreement / cannot_judge** items, the
orchestrator spot-checks against the evidence/ontology yourself before finalizing — confirm
the majority verdict holds, or flag it `uncertain`. Bias toward keeping the judges' call;
override only with positive evidence. (Don't silently rubber-stamp a 2-vs-1 split.)

## Step 5 — Score precision (reuse the project's scorer — DRY)

Write the **judged CSV** in the project's format (`out=`, default `<input>_judged.csv`).
Then score:
- `score=auto` (default): if the project has a scorer (e.g. archivechat
  `python -m curation.tooling.precision_score`), build the inputs it expects and **invoke it**
  for Wilson CI / per-term / corpus-weighted precision (see `references/scoring.md`).
- else: built-in **Wilson CI** precision per axis (formula in `references/scoring.md`).
- `score=none`: skip scoring, just verdicts.
If `cycle=` given, compare against the previous cycle's precision.

## Step 6 — Report + persist

Print: per-item verdict summary (consensus, split, contested flags), **precision headline
(point + Wilson CI)** per axis, and the worst/contested items to review by hand. Persist to
`~/.assay/runs/<run>/`: `verdicts.jsonl` (per item × judge), `judged.csv` copy, `summary.md`,
`cost.json`. The judged CSV also lands at `out=` for your existing pipeline.

---

## Degrade / edge cases
- Input isn't a table / has no judgeable rows → fit-check redirect (above) or ask once.
- A judge agent fails/returns malformed → retry once, else count that judge as `cannot_judge` and note it.
- Project scorer missing/erroring → fall back to built-in Wilson CI and note it.
- Huge input → batch rows, cap concurrency, disclose if you sample (never silently truncate).
- Code/plan target → recommend `/crossfire` and stop.
