---
description: Record income — usage: /add-income <amount> <source> [note]
allowed-tools: Bash(python budget.py:*)
---

Add income to the budget tracker.

## Your task

The user invoked this as: `/add-income $ARGUMENTS`

1. Parse `$ARGUMENTS` to extract:
   - `amount` — a number (required)
   - `source` — income source text (required)
   - `note` — the remaining text (optional)

2. If `$ARGUMENTS` is empty or missing required fields, ask the user for them before proceeding.

3. Run:
```
python budget.py income <amount> <source> [note]
```

4. Confirm the recorded income in one line.
