# assay judges — prompts, verdict enums, rubric, return schema, aggregation

Each judge is one independent sub-agent (`Agent`, subagent_type `Explore`, read-only)
that renders a verdict on ONE item. Spawn `judges=N` (default 3) per item; they don't
share. Skeptical, refute-first framing — the point is to catch wrong labels.

## Verdict enums

**Fine (judge output, default):**
`correct` · `wrong_term` · `wrong_context` · `too_narrow` · `too_broad` · `cannot_judge`

**Coarse rollup (for precision scoring):**
- `correct` → **correct**
- `wrong_term` | `wrong_context` | `too_narrow` | `too_broad` → **incorrect**
- `cannot_judge` → **ambiguous**

`verdicts=` overrides the fine set; keep the rollup mapping consistent (correct vs not vs abstain).

## Aggregation / kill rule

Per item, combine the N fine verdicts:
- **consensus** = the modal coarse verdict; record the vote split.
- **kill rule** (default `>=2/3 not-correct`): if at least ⌈2N/3⌉ judges say not-`correct`
  (any incorrect bucket), mark the label **wrong**. Configurable via `kill=`.
- ties / low agreement (e.g. 1-1-1, or a 2-vs-1 with a strong dissent) → flag **contested**
  → handled in SKILL Step 4 (orchestrator second-pass), not auto-finalized.
- a judge that returned `cannot_judge` or failed does not count toward the kill numerator;
  if a majority is `cannot_judge`, the item is **ambiguous** (abstain), not wrong.

## Return schema (REQUIRED — each judge ends with this JSON block)

```json
{"verdict":"correct|wrong_term|wrong_context|too_narrow|too_broad|cannot_judge",
 "reason":"one-sentence justification grounded in the item's evidence",
 "confidence":"high|med|low"}
```
Orchestrator parses only this block; missing/unparseable → retry once, else treat that judge as `cannot_judge` and note the gap.

## Judge prompt template

> You are an ADVERSARIAL accuracy judge for an ontology/label mapping. Be SKEPTICAL — try to
> REFUTE that the assigned label is correct for THIS sample. No benefit of the doubt.
> Decide ONE verdict from: correct | wrong_term | wrong_context | too_narrow | too_broad | cannot_judge.
>
> Axis: `<AXIS>`  ·  Assigned label: `<term_id> <term_name>`  (source `<source>`, confidence `<confidence>`)
> Sample evidence:
>   scientific_name: `<scientific_name>`
>   sample_title / alias: `<sample_title>` / `<sample_alias>`
>   description: `<sample_description>`
>   isolation_source / environment: `<isolation_source>` / `<environment...>`
>   protocol / library: `<library_construction_protocol>`
> Axis rubric: `<RUBRIC for AXIS — see below>`
>
> Judge whether `<term_name>` is the correct `<AXIS>` for this sample given ONLY the evidence.
> wrong_term = a different term is right; wrong_context = label not supported by the evidence;
> too_narrow/too_broad = right area but wrong granularity; cannot_judge = evidence insufficient.
> End with the JSON block (schema above) and nothing after.

## Per-axis rubric notes (archivechat Plant Ontology; extend as needed)

- **tissue / dev_stage** → Plant Ontology (PO) terms. dev_stage = developmental stage
  (seedling/flowering/etc.); tissue = plant anatomical entity. Watch over-broad PO parents.
- **genotype** → closed vocab (WT / mutant / transgenic / KO / KD / OE / CRISPR / genetic_modification).
  WT vs modified hinges on ACTUAL modification evidence; non-GM/conventional ≈ WT.
- **peco** → Plant Experimental Conditions Ontology (treatment/condition arms); watch competing arms.
- **generic** (unknown axis) → "is `<term_name>` the correct label for this item given the evidence?"

(For a non-archivechat dataset, pass `axis=generic` or a short rubric describing the label space.)
