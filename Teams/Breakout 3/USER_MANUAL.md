# Personal Budget Tracker — User Manual

## Overview

Personal Budget Tracker is a lightweight Python app for recording income and expenses on your local machine. All data is stored in a SQLite database (`budget.db`) that is created automatically on first run.

The app offers two interfaces that share the same data store:

- **CLI** — run commands directly in your terminal with `budget.py`
- **Web UI** — a browser dashboard served by `server.py`

You can use both interfaces at the same time. Changes made in one are immediately visible in the other.

---

## Requirements & Installation

**Required:**

- Python 3.8 or later (standard library only for the CLI)

**Required for the web UI only:**

```powershell
pip install flask
```

No other third-party packages are needed. The web dashboard loads Chart.js from a CDN at runtime, so the browser must have internet access for the pie chart to render.

---

## Quick Start

### CLI path

```powershell
# Navigate to the project folder
cd "Teams\Breakout 3"

# Record an expense
python budget.py add 45.00 Food "weekly groceries"

# Record income
python budget.py income 3000.00 Salary "June paycheck"

# View this month's report
python budget.py report
```

### Web UI path

```powershell
# Start the server (Flask must be installed first)
python server.py
```

Open `http://localhost:5000` in your browser. The dashboard loads the current month automatically.

Stop the server with `Ctrl+C` in the terminal.

---

## CLI Commands Reference

All commands follow the pattern:

```powershell
python budget.py <command> [arguments]
```

### `add` — Record an expense

```powershell
python budget.py add <amount> <category> [note]
```

| Argument | Required | Description |
|---|---|---|
| `amount` | Yes | Dollar amount (e.g. `12.50`) |
| `category` | Yes | One of the valid categories (see [Categories](#categories)) |
| `note` | No | Free-text description |

**Examples:**

```powershell
# Expense with no note
python budget.py add 3.50 Transport

# Expense with a note
python budget.py add 85.00 Utilities "electric bill"
```

### `income` — Record income

```powershell
python budget.py income <amount> <source> [note]
```

| Argument | Required | Description |
|---|---|---|
| `amount` | Yes | Dollar amount |
| `source` | Yes | Free-text source label (e.g. `Salary`, `Freelance`) |
| `note` | No | Free-text description |

**Examples:**

```powershell
python budget.py income 2500.00 Salary
python budget.py income 350.00 Freelance "logo design project"
```

### `list` — List recent expenses

```powershell
python budget.py list [--month YYYY-MM]
```

Without `--month`, the command returns the 50 most recent expenses across all time. With `--month`, it returns all expenses for that month.

**Examples:**

```powershell
# Last 50 expenses
python budget.py list

# All expenses for a specific month
python budget.py list --month 2026-06
```

### `report` — Monthly spending summary

```powershell
python budget.py report [--month YYYY-MM]
```

Prints a table showing spending by category, total expenses, total income (if any), and net balance. Also renders an ASCII pie chart in the terminal. Defaults to the current month.

**Examples:**

```powershell
# Current month
python budget.py report

# Specific month
python budget.py report --month 2025-12
```

---

## Web UI

### Starting the server

```powershell
python server.py
```

The server starts on port 5000. Open `http://localhost:5000` in any browser.

The server auto-reloads when you edit `server.py` (Flask's debug mode is enabled by default during development). Do not use debug mode in production.

### What the dashboard shows

The dashboard has three sections:

1. **Summary stats** — Income, Expenses, and Net balance for the selected month, shown as colored cards at the top.
2. **Pie chart** — Expense breakdown by category. The chart updates automatically when you change the month or add an entry. If there are no expenses, a "No expense data" message is shown instead. Chart.js is loaded from a CDN; the chart will not render without an internet connection.
3. **Add Entry form** — Expandable form for recording a new expense or income (see below).

### Changing the month

Use the **Month** picker in the top-right corner. The stats and pie chart update immediately.

### Adding an entry

1. Click **+ Add Entry** to expand the form.
2. Select the **Type**: Expense or Income.
   - For an expense: choose a **Category** from the dropdown.
   - For income: enter a **Source** (e.g. `Salary`).
3. Enter the **Amount** in dollars.
4. Optionally enter a **Note**.
5. Click **Save Entry**.

The dashboard stats and pie chart refresh automatically after a successful save. Error messages appear inline if the amount is missing or the category is invalid.

### API endpoints

The dashboard uses these JSON endpoints. You can call them directly with `curl` or any HTTP client.

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/report?month=YYYY-MM` | Returns income, expense totals by category, and month |
| `POST` | `/api/expense` | Add an expense — body: `{"amount": float, "category": str, "note": str}` |
| `POST` | `/api/income` | Add income — body: `{"amount": float, "source": str, "note": str}` |

**Example — fetch a report:**

```powershell
Invoke-RestMethod "http://localhost:5000/api/report?month=2026-06"
```

**Example — add an expense via API:**

```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:5000/api/expense" `
  -ContentType "application/json" `
  -Body '{"amount": 12.50, "category": "Food", "note": "lunch"}'
```

---

## Categories

Expenses must use one of these fixed categories:

| Category | Description |
|---|---|
| `Food` | Groceries, restaurants, takeout |
| `Transport` | Fuel, transit, rideshare |
| `Housing` | Rent, mortgage, repairs |
| `Entertainment` | Streaming, events, hobbies |
| `Health` | Medical, pharmacy, gym |
| `Utilities` | Electric, water, internet, phone |
| `Other` | Anything that doesn't fit above |

Category names are case-sensitive. Use the exact spelling shown above. The CLI will reject an unrecognised category with an error message listing valid options.

Income does not use categories — it uses a free-text `source` label instead.

---

## Custom Slash Commands

These commands are available inside Claude Code (`.claude/commands/`). Run them by typing `/command-name` in the Claude Code chat.

### `/add-expense <amount> <category> [note]`

Parses your arguments, normalises the category to title case, and runs `budget.py add`. Asks for missing required fields before proceeding.

```
/add-expense 9.99 Food coffee
```

### `/add-income <amount> <source> [note]`

Parses your arguments and runs `budget.py income`. Asks for missing required fields before proceeding.

```
/add-income 1500 Freelance "consulting invoice"
```

### `/monthly-report [YYYY-MM]`

Runs `budget.py report` for the given month (or the current month if omitted) and adds a one-sentence observation about the data.

```
/monthly-report
/monthly-report 2026-05
```

### `/categorize <amount> <description>`

Claude reads the description, picks the best-fit category, and asks you to confirm before recording the expense. Useful when you are unsure which category to use.

```
/categorize 22.00 "Uber to the airport"
```

### `/commit [title]`

Stages relevant changes, runs the `ensure-tests` skill, writes a concise commit summary, and commits. Does not push to the remote.

```
/commit "add web UI"
```

---

## Tips & Common Workflows

**End-of-month review**

```powershell
python budget.py report --month 2026-05
```

Or open the dashboard, pick the month in the picker, and review the pie chart visually.

**Bulk data entry via CLI**

The CLI is faster than the web form when entering many transactions at once. Open PowerShell, navigate to the project folder, and run one `add` command per transaction.

**Checking a specific category**

Use `list` with `--month` and scan the output — the category column is right-aligned for easy reading.

```powershell
python budget.py list --month 2026-06
```

**Using both interfaces simultaneously**

Start the server in one terminal window and keep a second terminal open for CLI commands. Both read from and write to the same `budget.db`, so the dashboard reflects CLI entries immediately on the next page load or month change.

**Letting Claude categorize for you**

Use `/categorize` when you are unsure of the right category. Claude reasons from the description and asks for confirmation, so you stay in control of the final choice.

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'flask'`

Flask is not installed. Run:

```powershell
pip install flask
```

Then start the server again.

### `python: command not found` or similar

Your Python 3 installation may be registered as `python3` on your system. Try:

```powershell
python3 budget.py report
python3 server.py
```

### `budget.py: error: argument category: invalid choice`

The category you entered does not match the allowed list. Categories are case-sensitive. Valid values: `Food`, `Transport`, `Housing`, `Entertainment`, `Health`, `Utilities`, `Other`.

### The pie chart does not appear in the web UI

Chart.js loads from `cdn.jsdelivr.net`. If you are offline or the CDN is blocked, the chart canvas stays hidden. The stats (Income, Expenses, Net) still work because they are calculated server-side.

### Port 5000 is already in use

Another process is using port 5000. Either stop that process, or edit the last line of `server.py` to use a different port:

```python
app.run(debug=True, port=5001)
```

Then open `http://localhost:5001` instead.

### `budget.db` permissions error

SQLite creates `budget.db` in the same folder as `budget.py`. Make sure your user account has write permission to the `Teams\Breakout 3\` directory.

### Changes in the web UI do not appear in the CLI report

Both tools share the same `budget.db`. If data seems out of sync, verify you are running both commands from the same `Teams\Breakout 3\` directory — running `budget.py` from a different working directory would create a second database file.
