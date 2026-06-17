# Crossfire tool registry

Canonical list of tools the orchestrator may run, with exact commands, prerequisites,
timeouts, and cost. Default tools = `lenses + codex + health`. Everything else is opt-in
via `tools=+name`. A missing prerequisite → skip the tool and note it in the report.

## Default (always on unless `tools=none`)

### lenses
- Spawn: `Agent`, subagent_type `Explore`, 2–6 in parallel (see `references/lenses.md`).
- Prereq: none. Cost: low. Timeout: per-agent default.

### codex (reviewer, synchronous)
- Prereq: `command -v codex`. Cost: medium. Effort: `model_reasoning_effort="high"`.
- Git repo:
  ```bash
  codex review --base "<BASE>" -c 'model_reasoning_effort="high"' --enable web_search_cached
  ```
- Non-git / explicit files (Phase-1 default, since the workspace is usually non-git):
  ```bash
  codex exec "<SCOPED_GUARD> Adversarially review these files: <PATHS>. Tag each finding [P1]/[P2]/[P3] with a one-line fix." \
    -C "$WORK_ROOT" -s read-only -c 'model_reasoning_effort="high"' --skip-git-repo-check
  ```
- `SCOPED_GUARD` = `"Only read the named target file(s). Do NOT read other files under ~/.claude/** (config/secrets)."`
- Codex CLI is synchronous and does NOT trigger the `[CCB_ASYNC_SUBMITTED]` async guardrail
  (that applies only to `ask`). It completes in-turn. Parse `[P1]/[P2]/[P3]` lines into findings.
- Run in the background with a long Bash timeout if needed; do not use `ask codex`.

### health (empirical, baseline-aware)
- Prereq: a detected test/typecheck/lint tool. Cost: low. Run **baseline first**, then classify
  only new / target-related failures as P1; report pre-existing failures separately.
- Detect from stack files and run what exists:
  | stack file | typecheck | lint | test |
  |---|---|---|---|
  | `pyproject.toml` / `setup.cfg` | `mypy <target>` | `ruff check <target>` | `pytest -q` |
  | `package.json` (+`tsconfig.json`) | `tsc --noEmit` | `biome check .` or `eslint .` | `npm test` / `bun test` |
  | `go.mod` | `go vet ./...` | `golangci-lint run` | `go test ./...` |
  Also honor a `## Health Stack` section in the project `CLAUDE.md` if present.
- Reuse the gstack health detection patterns: `~/.claude/skills/gstack/health/SKILL.md`.

## Opt-in (Phase-1 wiring; downgrade to a written recommendation if the Skill call fails)

| tool | invoke | prereq | cost | notes |
|---|---|---|---|---|
| `+security` | Skill `gstack:cso` (`--diff` in git) | git recommended | med | overlaps the `security` lens; run when explicitly requested or strong auth/secret signal |
| `+stats` | Skill `scientific-skills:statistical-analysis`, `scientific-skills:scientific-critical-thinking` | — | med | data/bioinformatics methodology |
| `+perf` | Skill `gstack:benchmark <url>` (web) or runtime/memory profile | url for web | med | |
| `+visual` | Skill `gstack:design-review` | url | med | |

- Plugin-scoped skills (`plugin:skill`) are callable via the Skill tool.
- If ≥2 opt-in tools would run, list them + a cost estimate and confirm via `AskUserQuestion` first.

## Helpers
- `~/.claude/skills/gstack/bin/gstack-diff-scope` — diff scope signals (SCOPE_AUTH/BACKEND/FRONTEND/API/MIGRATIONS). Git only; non-git → path/extension/import heuristics.

## Phase 2 (not wired in Phase 1)
- `run` execution adapters (script/notebook/CLI output validation) → `references/adapters.md`.
- Cross-cycle ledger, carry-over brief, acknowledgment contract → see the plan's `[단계2]` sections.
