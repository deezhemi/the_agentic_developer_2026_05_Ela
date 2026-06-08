---
name: project-testing-conventions
description: Testing conventions for the Breakout 3 Python budget app — framework, output capture, file naming, and module import patterns
metadata:
  type: project
---

## Framework
- `unittest.TestCase` exclusively — no pytest. All test classes inherit from it.
- No third-party test libraries; stdlib only (mirrors the app's stdlib-only constraint).

## Output capture
- Primary pattern: `io.StringIO` + `contextlib.redirect_stdout`. A `_render(rows)` helper wraps `pie_chart` and returns captured output as a string.
- For asserting *no* output: `unittest.mock.patch('builtins.print')` and call `.assert_not_called()`.
- Both approaches are used in the same file — choose based on whether you need the text or just proof it was/wasn't called.

## File naming and location
- Test files sit alongside source files inside `Teams/Breakout 3/` (not a separate `tests/` directory).
- Naming: `test_<module>.py` (e.g., `test_chart.py`, `test_budget.py`).
- All tests for the budget CLI, expenses, income, and charting live in `test_budget.py`; chart-specific tests now also live in `test_chart.py`.

## Module import pattern
- Source files are NOT installed as packages; tests add `sys.path.insert(0, os.path.dirname(__file__))` so imports resolve regardless of working directory.
- Modules imported inside test methods (lazy import) in `test_budget.py`; top-level imports are fine in `test_chart.py` since `chart.py` has no DB dependency.

## Mocking
- DB layer: `patch("db.get_conn", return_value=<in-memory sqlite3 conn>)` via a `_DBMixin` base class in `test_budget.py`.
- Print capture preferred over print mocking for content assertions.
- `unittest.mock.patch` used sparingly, only when the absence of a call is the assertion.

## Helper patterns observed
- `_rows(*pairs)` — builds `[{"category": cat, "total": amt}]` dicts from `(name, amount)` tuples.
- `_render(rows)` — calls the function under test and returns stdout as a string.
- `_extract_bar(output)` — parses the `[...]` bar line inner content.
- `_extract_legend_lines(output)` — filters out blank lines and bar lines, leaving only legend rows.

## Known edge cases in chart.py
- Empty list or all-zero totals: early return, no print calls.
- Last segment absorbs rounding remainder (may be 0 or negative if earlier rounding overshoots — currently guarded by `_WIDTH - used`).
- Fill characters cycle via `i % len(_FILLS)` for both bar segments and legend lines.
- Single-category input: bar is entirely one fill char; loop over `totals[:-1]` is empty so the only segment is the last-segment fallback.
