# Skills — authored Claude Code skills

Source-of-truth for Claude Code skills I author. Each skill lives in its own
folder here and is **symlinked into `~/.claude/skills/`** so edits are live
everywhere (no copy/deploy step) while the source stays versioned & backed up,
separate from third-party skills (gstack, scientific-skills, …).

## Skills

| skill | what |
|---|---|
| [`crossfire`](crossfire/) | One-command adversarial (sub-agent lenses + Codex) + empirical (tests/lint) verification, with an optional cycle convergence loop. |

## Dev / install pattern

Skill source is here; `~/.claude/skills/<name>` is a symlink to it:

```bash
ln -s "$PWD/crossfire" ~/.claude/skills/crossfire   # install (symlink = live edit)
ls -l ~/.claude/skills/crossfire                     # -> .../Task/Skills/crossfire
```

Edit files under `crossfire/` → changes are immediately live in every session.
To install on a new machine, clone this repo and re-create the symlink(s).
(Claude Code auto-discovers `SKILL.md`; skills are **not** registered in any CLAUDE.md.)
