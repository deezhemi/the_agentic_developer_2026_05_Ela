---
description: Show a monthly spending summary — usage: /monthly-report [YYYY-MM]
allowed-tools: Bash(python budget.py:*)
---

Generate a monthly budget report.

## Your task

The user invoked this as: `/monthly-report $ARGUMENTS`

1. If `$ARGUMENTS` contains a month in `YYYY-MM` format, use it. Otherwise omit `--month`
   (the app defaults to the current month).

2. Run:
   ```
   python budget.py report [--month YYYY-MM]
   ```

3. Display the output. Then add a one-sentence observation — e.g. the largest spending
   category, or whether the total seems high or low relative to a typical budget.
   Keep it brief; don't invent numbers not in the data.
