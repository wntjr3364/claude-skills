# assay

Multi-judge **accuracy adjudication for data rows / claims** — the data-side sibling of
`crossfire` (which verifies code/plans). For each candidate row, a panel of N independent
skeptical judges renders a structured verdict; votes are aggregated by a kill rule; precision
is scored (Wilson CI, reusing the project's scorer when present). Codifies the
"Adversarial Claim Verifier (voter k/N)" / smoke-judge / precision-audit pattern.

## Quick usage

```bash
/assay audit_cycle29_genotype_n200.csv axis=genotype judges=3 cycle=29
/assay rows.csv axis=generic judges=5 verdicts=correct,incorrect,ambiguous score=none
```
Args: `input.csv` · `axis=` · `judges=N` (3) · `verdicts=` · `kill=">=2/3 not-correct"` ·
`cycle=N` · `score=auto|none` · `out=`.

## What it does / doesn't

- **Does**: grade a CSV/table of items for accuracy — ontology mappings, extraction/curation
  rows, labeled candidates. Produces per-item verdicts + precision (point + Wilson CI).
- **Doesn't**: review code or a plan for bugs → that's **`crossfire`**. assay's Step 0 fit-check
  redirects code/plan targets to crossfire, and declines non-grading requests.

## Files
- `SKILL.md` — orchestrator (fit-check → load → judge panel → aggregate → second-pass → score → report).
- `references/judges.md` — judge prompts, verdict enums (+ coarse rollup), per-axis rubric, return schema, kill rule.
- `references/scoring.md` — judged-CSV format, hand-off to the project scorer (archivechat `precision_score.py`), built-in Wilson CI fallback, cycle comparison.

## Design

Sibling of crossfire, same shared idea (N adversarial agents → structured verdict → aggregate →
orchestrator second-pass), different unit & output: **rows graded for accuracy + precision**, not
findings/gate. assay automates the **LLM judging** you did by hand and hands **scoring** to the
project's existing scorer (DRY). Runs log to `~/.assay/runs/`; the judged CSV lands at `out=`.
