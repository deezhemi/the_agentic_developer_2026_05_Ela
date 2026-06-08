# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in this repository.

## What this is

This is the **Breakout 3 team workspace** for *The Agentic Developer* workshop — a hands-on training in building software collaboratively with Claude Code. Everything here is exploratory and learning-oriented: expect rapid iteration, experiments, and work-in-progress over polished production code.

## Working agreement

- **Explain as you go.** This is a teaching context. When you make a non-obvious choice, say why in a sentence — the goal is for the human to learn, not just to ship.
- **Small steps.** Prefer incremental, reviewable changes over large rewrites. Pause at natural checkpoints so we can inspect together.
- **Ask before scaffolding.** Don't introduce a framework, language, or large dependency without checking first — part of the exercise is deciding these together.
- **Plan first for anything non-trivial.** Outline the approach before editing files.

## Conventions

- Keep new work inside this team folder (`Teams/Breakout 3/`) unless told otherwise.
- Match the style of surrounding code once a project is established here.
- Only commit when explicitly asked.

## Environment

- Platform: Windows (PowerShell). Use PowerShell syntax for shell commands.
- Git repo root is the workshop root; this folder is one team's workspace.

## Custom slash commands

`/commit [title]` — defined at the repo root in `Teams/Heimeshoff/.claude/commands/commit.md`. Stages relevant files, writes a conventional commit message (or uses the provided title as the summary line), commits, and shows the result. Does **not** push.

## Project state

Personal budgeting CLI app — Python 3 + SQLite (stdlib only, no dependencies).

**Run / test**
```powershell
# Add an expense
python budget.py add 12.50 Food "lunch"

# List recent expenses
python budget.py list

# Monthly report (defaults to current month)
python budget.py report
python budget.py report --month 2026-06
```

**Architecture**
- `db.py` — schema, `CATEGORIES` list, all SQL queries. Single source of truth for data access.
- `budget.py` — CLI entry point (`argparse`). Calls `db.py`; no SQL here.
- `budget.db` — created on first run, gitignored.

**Custom slash commands** (in `.claude/commands/`)
- `/add-expense <amount> <category> [note]` — parse args and record an expense
- `/monthly-report [YYYY-MM]` — run the report and add a one-line observation
- `/categorize <amount> <description>` — Claude picks a category, confirms, then records
