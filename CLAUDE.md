# Skills workspace — manager context

Source-of-truth for the Claude Code skills I author. **This file is inherited by
every skill subfolder** (e.g. `crossfire/`): a Claude session opened inside a skill
folder automatically reads this (cwd → root CLAUDE.md chain + global), so the
manager context flows down to each per-skill session.

> Scope: only this folder and its children. Sibling projects (e.g. `../archivechat`)
> do NOT inherit this — they only get the globally-installed skills, not this context.

## Layout
- One folder per skill: `<skill>/SKILL.md` (+ optional `references/*.md`, `README.md`).
- Each skill is symlinked into `~/.claude/skills/<skill>` → globally available + live-edited.
- Skills are **auto-discovered** by Claude Code; they are NOT registered in any CLAUDE.md.

## Authoring a new skill (do it here)
1. `mkdir <skill>`; write `<skill>/SKILL.md` with YAML frontmatter:
   `name`, `description` (say *when to use it*), `argument-hint`, `user-invocable`,
   `allowed-tools`, `metadata.short-description`. Push long detail/templates to `<skill>/references/*.md`.
2. Install once (symlink → live): `ln -s "$PWD/<skill>" ~/.claude/skills/<skill>`
3. Add a short `<skill>/README.md`.
4. `git add -A && git commit` here — this folder is the versioned source.

## Conventions
- Keep `SKILL.md` lean (the orchestrator); push detail to `references/`.
- **Dogfood before declaring done**: build a tiny real case and actually run it. For code, `/crossfire`.
- **Honest degrade**: a skill must report what it skipped / couldn't verify — no silent fallback.
- Persist run artifacts OUTSIDE the repo (e.g. under `~/`), never write into a target project.

## Skills here
- `crossfire/` — adversarial (sub-agent lenses + Codex) + empirical (tests/lint) verification,
  with an optional cycle convergence loop (carry-over + acknowledgment). Phase 1+2 built & validated; Phase 3 deferred.
