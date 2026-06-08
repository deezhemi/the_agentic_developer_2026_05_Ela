---
description: Record an expense — usage: /add-expense <amount> <category> [note]
allowed-tools: Bash(python budget.py:*)
---

Add an expense to the budget tracker.

## Categories available

Food, Transport, Housing, Entertainment, Health, Utilities, Other

## Your task

The user invoked this as: `/add-expense $ARGUMENTS`

1. Parse `$ARGUMENTS` to extract:
   - `amount` — a number (required)
   - `category` — one of the categories above (required, case-insensitive — normalise to title case)
   - `note` — the remaining text (optional)

2. If `$ARGUMENTS` is empty or missing required fields, ask the user for them before proceeding.

3. Run:
   ```
   python budget.py add <amount> <category> [note]
   ```

4. Confirm the recorded entry to the user in one line.
