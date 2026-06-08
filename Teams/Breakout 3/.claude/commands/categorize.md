---
description: Suggest a category for a transaction description, then record it — usage: /categorize <amount> <description>
allowed-tools: Bash(python budget.py:*)
---

Use a sub-agent to pick the best category for a transaction, then add it.

## Categories

Food, Transport, Housing, Entertainment, Health, Utilities, Other

## Your task

The user invoked this as: `/categorize $ARGUMENTS`

Parse `$ARGUMENTS` to extract:
- `amount` — a number (required)
- `description` — the rest of the text (required)

**Step 1 — categorize (you are the sub-agent here)**

Read the description and pick the single best-fit category from the list above.
Reason in one sentence, then state your choice clearly:
> Category: <chosen category>

**Step 2 — confirm with the user**

Show the user:
- Amount, description, and your chosen category
- Ask: "Does this look right? (yes / pick another)"

If they say yes (or just press enter), proceed to step 3.
If they name a different category, use that instead.

**Step 3 — record**

Run:
```
python budget.py add <amount> <category> "<description>"
```

Confirm the recorded entry in one line.
