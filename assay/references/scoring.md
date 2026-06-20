# assay scoring — judged CSV + precision (reuse the project scorer; DRY)

assay does the **judging**; scoring reuses the project's battle-tested scorer when present,
falling back to a built-in Wilson CI. Never reinvent stats the project already has.

## Judged CSV (what assay writes to `out=`)

Preserve the input columns and append:
`judge_verdicts` (the N fine verdicts, e.g. `correct;wrong_term;correct`) ·
`verdict` (coarse rollup: correct|incorrect|ambiguous) · `consensus_fine` · `vote_split` ·
`contested` (bool) · `n_judges`. Keep the input's item key (e.g. `run_accession,term_id`).

## score=auto — hand off to the project's scorer

Detect and reuse, in order:
1. **archivechat**: `conda run -n main python -m curation.tooling.precision_score --dir <dir>`
   — expects `<dir>/review.csv` (`item_id,verdict` with verdict ∈ correct|incorrect|ambiguous)
   + `<dir>/key.csv`. Build those from the judged CSV (coarse `verdict`, `item_id` = the item key),
   then invoke it. It returns per-term + per-method + **corpus-weighted Wilson CI** (post-stratified),
   with an exclude-ambiguous vs conservative sensitivity band. Also reuse `aggregate_verdicts.py` /
   `smoke_aggregate_cycle.py` if the run is a smoke/audit cycle.
2. any other `*precision*scor*` / `*aggregate*verdict*` script the project exposes — prefer it.
3. none found → built-in (below).

## Fallback — built-in Wilson CI

Per axis (and per term if enough n), precision = correct / (correct + incorrect), with
**Wilson 95% interval**. Ambiguous reported two ways (excluded = primary; counted-as-incorrect
= conservative) — mirror the project's convention.

```python
import math
def wilson(k, n, z=1.96):
    if n == 0: return (float('nan'),)*3
    p = k/n; den = 1 + z*z/n
    c = (p + z*z/(2*n))/den
    h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/den
    return (p, max(0.0, c-h), min(1.0, c+h))   # (point, lo, hi)
```

## Cycle comparison

If `cycle=N`, locate the prior cycle's report/precision (same axis) and show the delta
(precision point + CI overlap) so you can see whether a fix improved accuracy. Note regressions.

## Output

`summary.md`: precision headline per axis (`p [lo, hi], n`), exclude-ambiguous vs conservative band,
the contested/worst items to review by hand, and (if cycle) the vs-previous delta.
