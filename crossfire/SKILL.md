---
name: crossfire
description: |
  One-command adversarial + empirical verification. Spawns an auto-selected set
  (2–6) of parallel adversarial Claude lenses + a synchronous Codex review, runs
  the project's tests/typecheck/lint (health), consolidates findings by severity
  with stable IDs, and reports (or applies) fixes. Works WITHOUT git (explicit
  target + snapshot diff). Optional signal-gated power-ups: security (cso),
  statistics/methodology (scientific-skills), performance, visual. Use to verify
  code changes or a plan doc without re-requesting the same review pattern every
  time. Defaults are cheap and one-pass; heavy tools are opt-in. cycles>1 runs a
  carry-over convergence loop (Phase 2).
argument-hint: "[path] [mode=auto|code|plan] [fix=report|apply] [cycles=N] [lenses=auto|N|csv] [tools=+security,+stats,+perf,+visual|none] [url=...] [resume=<run>] [--refute]"
user-invocable: true
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, Agent, AskUserQuestion, Skill
metadata:
  short-description: Adversarial + empirical verify (1 command)
---

# Crossfire — adversarial + empirical verification (Phase 1 core)

You are the **orchestrator**. When `/crossfire` is invoked you run ONE verification
pass over a target (code files or a plan doc): spawn parallel adversarial lens
sub-agents + a synchronous Codex review + the project's own tests/lint (health),
then consolidate, gate, and report (or apply) fixes. You are the single durable
memory of this run — sub-agents are stateless workers you coordinate.

**Findings are a first pass — give them a second review.** The lenses and Codex do
the initial review; YOU re-check each finding against the real code (Step 4.5),
empirically where you can, before it reaches the user or the gate. The aim is to back
real issues with evidence and catch the occasional false-positive — *not* to assume
the lenses are wrong (don't over-prune real findings).

**Default is a single pass (`cycles=1`).** If `cycles=` is greater than 1, run the
**carry-over convergence loop** in `references/cycles.md`: Steps 2–5 below become one cycle,
and you carry a findings ledger between cycles (injecting a brief into each next-cycle worker)
with an acknowledgment contract. Recommend `cycles ≤ 5`.

References (read the relevant one before the step that needs it):
- `references/lenses.md` — lens catalog, signal→lens table, priority, prompt templates, the worker return schema (+ Phase-2 `acks`).
- `references/tools.md` — canonical tool registry (commands, prereqs, timeouts, cost).
- `references/cycles.md` — **Phase 2** loop: ledger, carry-over brief, acknowledgment contract, convergence, checkpoint, `resume`.
- `references/adjudicate.md` — **Step 4.5**: the main's second-pass review — confirm each finding against the real code before reporting.

---

## Step 0 — Parse args + preflight + budget

Parse args (all optional):
- `path=` — file / dir / glob to verify. May also be given as the first bare argument.
- `mode=auto|code|plan` (default `auto`).
- `fix=report|apply` (default `report`). Plan docs are **always report-only unless the user explicitly confirms** edits.
- `lenses=auto|N|csv` (default `auto`).
- `tools=` — additive opt-ins (`+security,+stats,+perf,+visual`) or `none` (lenses only). Default base = `codex,health`.
- `url=` — only when `+perf`/`+visual` opted in.
- `cycles=N` (default 1). N>1 → carry-over convergence loop (`references/cycles.md`).
- `resume=<run>` — continue a prior run's ledger (`references/cycles.md`).
- `--full-audit` — persist unmasked worker prompts (default masks secrets).
- `--refute` — extra rigor: spawn skeptic sub-agents to try to refute each confirmed P1 (off by default; see `references/adjudicate.md`).

Preflight (run via Bash, read-only):
```bash
WORK_ROOT="$(cd "$(dirname "${TARGET:-.}")" 2>/dev/null && pwd || pwd)"
RUN_ID="$(date +%Y%m%d-%H%M%S)-$$"
RUN_DIR="$HOME/.crossfire/runs/$RUN_ID"
mkdir -p "$RUN_DIR/baseline"
command -v codex >/dev/null && echo "codex: ok" || echo "codex: MISSING (skip + note)"
# REPO_ROOT only if inside a git work tree:
git -C "$WORK_ROOT" rev-parse --show-toplevel 2>/dev/null && echo "git: yes" || echo "git: no (non-git mode)"
```
Detect health tools from stack files (see `references/tools.md`). Any missing tool →
**skip that layer and note it in the report** (never silently fall back).

**Disclose the budget BEFORE running** (print to the user): the selected lenses + the
signal that triggered each, dropped candidates, the tool set, and a rough max wall-time.

## Step 1 — Resolve target (non-git friendly)

- If `path=` is given, that file/glob is the **verification subject**. `mode=code` unless the path is a `.md` plan (then `plan`), or honor explicit `mode=`.
- If `path=` omitted, auto-detect: ① `git diff` (staged→unstaged) present → code mode, capture diff + base; ② else a plan doc (active plan-mode file or `~/.claude/plans/*.md`; if several, newest or ask) → plan mode; ③ ambiguous/none → ask once with `AskUserQuestion`, or stop if nothing to verify.
- **Snapshot (non-git change tracking):** copy the target files into `$RUN_DIR/baseline/`. If no prior snapshot exists to diff against, treat the **whole specified file(s)** as the subject and say so in the report.

## Step 2 — Auto-select lenses (read `references/lenses.md`)

Mandatory lenses always run: **correctness/logic** and **edge-cases/failure-modes**
(plan mode: **feasibility/consistency** and **missing-cases**). Add signal-triggered
lenses (security, performance, concurrency, data-validity/stats, simplicity, API-contract)
per the detector table. **Clamp to 2–6**; when the cap binds, keep by priority
(security > data-validity > concurrency > performance > API > simplicity); **security and
data-validity are never dropped once triggered**. `lenses=N` keeps the top-N by priority
but is clamped to include the mandatory + non-droppable triggered lenses (reject impossible N).
`lenses=csv` adds/removes optional lenses only — mandatory lenses are force-added if missing.

## Step 3 — Run the panel (parallel)

Launch concurrently (one message, multiple tool calls):
- **Lens sub-agents** — one `Agent` (subagent_type `Explore`, read-only) per selected lens.
  Give each the lens prompt from `references/lenses.md` + the subject (diff or file contents)
  + the instruction to return findings in the **worker return schema** (strict JSON block).
  Adversarial framing: "find flaws, no praise, try to break it."
- **Codex (reviewer), synchronous foreground** — see `references/tools.md` for the exact command.
  Git: `codex review --base <base> ...`. Non-git/explicit files:
  `codex exec "<scoped guard> Adversarially review these files: <paths>. Tag findings [P1]/[P2]/[P3]." -C "$WORK_ROOT" -s read-only -c 'model_reasoning_effort="high"'`.
  **scoped safety guard** (prepend): "Only read the named target file(s). Do NOT read other files under ~/.claude/** (config/secrets)."
  Codex CLI is synchronous and NOT subject to the `ask` async guardrail — it completes in-turn.
  (Crossfire's synchronous Codex satisfies the CLAUDE.md reviewer checkpoint for this run.)
- **health** — detect & run the project's tests/typecheck/lint directly (see `references/tools.md`).
  **Baseline first:** record pre-existing failures separately; only **new / target-related** failures are P1.

## Step 4 — Consolidate (stable IDs + dedupe)

Merge all lens findings + codex findings + health failures. Assign each a
**deterministic id = short hash of (normalized location + bug_type + short claim)**;
dedupe by id (wording differences don't matter). Severity P1/P2/P3.
- **Keep single-lens P1s** (only drop low-confidence non-P1 with no substantiation).
- **Empirical evidence only strengthens:** a failing test is a confirmed P1. A *passing*
  test does NOT downgrade a reasoning finding — at most annotate "covered by test, lower priority."

## Step 4.5 — Confirm findings (second-pass review)

The lenses and Codex did a first review; you give each consolidated finding a **second
pass** before gating — confirm it against reality rather than forwarding it as-is
(full method: `references/adjudicate.md`).

For each finding (prioritize P1/P2; batch P3): **check it against the real code,
empirically when you can** — `Read` the cited code and, where cheap, *confirm* it with a
quick probe (run the regex/function on the claimed input, a 3-line repro, grep the test).
Weigh corroboration (independent sources, health backing). Judge whether it's a real defect
or **by-design / a nitpick / a known trade-off**, and adjust severity.

Assign each finding a **verdict** with your evidence:
- `confirmed` — checked out · `uncertain` — plausible, couldn't confirm either way (**the default when unsure — keep it**) · `rejected` — you have positive evidence it's wrong / by-design.

Only `confirmed` gates; `uncertain` is surfaced (flagged) but non-gating; **`rejected` is
listed in a "Filtered" section with your reason — never dropped silently.** Don't reject a
finding just because you couldn't quickly reproduce it (→ `uncertain`), and don't assert an
unconfirmed finding as fact. (Optional `--refute` adds an adversarial skeptic pass on confirmed P1s.)

## Step 5 — Gate + fix

- **Gate (confirmed findings only):** PASS iff `confirmed P1 == 0 AND (confirmed P2 == 0 OR each remaining deferred with a reason)`.
  `uncertain` is surfaced but does not gate; `rejected` never gates. Plan mode may also apply a rubric gate (overall ≥ 7, every dimension > 3).
- **fix=report** (default): print findings + suggested fixes only. No edits.
- **fix=apply:** only **`confirmed`** findings are eligible. Apply **Mechanical** fixes (obvious, high-confidence, empirically backed) automatically;
  **Taste / User-Challenge** decisions go through `AskUserQuestion`. **Never edit a plan doc without explicit user approval.**

## Step 6 — Report + persist

Print a findings table: `id · severity(orig→adjudicated) · location · source(lens/tool) · verdict · claim · evidence · fix · status`,
then the gate result, skipped tools, and a cost summary. Add a **"Filtered (rejected / by-design)"**
section listing every `rejected` finding with your reason — so the filtering is auditable and the
user can override your judgment.

Persist to `$RUN_DIR/`:
- `findings.jsonl` — every finding (incl. `verdict` + adjudication evidence), one JSON object per line (append-only).
- `summary.md` — the human-readable report (table + gate + skipped + cost).
- `cost.json` — lenses run, codex calls, tools, approx tokens/wall-time.

---

## Degrade / edge cases
- Nothing to verify (no path, no diff, no plan) → ask once, else stop cleanly.
- codex / a health tool / an opt-in skill missing → skip that layer, note it in the report (no silent fallback).
- `+security`(`gstack:cso`) / `+stats`(`scientific-skills:...`) etc. invoked via the Skill tool; if the
  invocation fails or is unavailable, **downgrade to a written recommendation** in the report (no hard dependency).
- ≥2 opt-in Layer-3 tools would run → list them + cost estimate and confirm via `AskUserQuestion`.
- `cycles>1` → run the convergence loop in `references/cycles.md` (ledger + carry-over + acks + checkpoint).
