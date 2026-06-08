---
description: Ensure test coverage for all new or modified Python files. Use this skill when the user asks to check or ensure test coverage, asks "do we have tests for this?", or after implementing new Python code when tests should be verified. TRIGGER — invoke when: user mentions "ensure tests", "check coverage", "add missing tests", "do we have tests", or after writing/modifying Python source files.
allowed-tools: Bash(git diff:*), Bash(git status:*), Bash(python -m unittest:*), Read, Edit, Write, Glob
---

Ensure that every new or modified Python file has corresponding unit test coverage.

### Step 1 — Find changed Python files

Run:
```
git diff --name-only HEAD
git status --short
```

Collect all `.py` files that are new (`??`) or modified (`M`, `A`). Exclude files that are
themselves test files (name starts with `test_` or ends with `_test.py`).

### Step 2 — Identify the test file for each changed file

For a source file `foo.py` the expected test file is `test_foo.py` in the same directory.

For each changed source file:
- Check whether the expected test file exists.
- If it exists, grep it for test functions that exercise the changed file's public functions/classes.

### Step 3 — Run existing tests

Run all tests with:
```
python -m unittest discover -v 2>&1
```

Report: how many tests ran, how many passed, and any failures.

### Step 4 — Gap analysis

For each changed source file, determine:
- **Covered** — test file exists and tests ran green.
- **Partially covered** — test file exists but one or more public functions/classes in the source
  file have no corresponding test function.
- **Not covered** — no test file exists at all.

List the results in a short table:

| File | Status | Notes |
|------|--------|-------|
| foo.py | Covered | 4 tests, all green |
| bar.py | Partially covered | `bar.new_function` has no test |
| baz.py | Not covered | No test_baz.py found |

### Step 5 — Fill gaps

For each **Partially covered** or **Not covered** file:

1. Tell the user what is missing.
2. Write the missing test functions (or create the test file if absent). Follow the same
   patterns already used in existing test files in this project:
   - Use `unittest.TestCase`
   - Patch `db.get_conn` with an in-memory SQLite connection for any code that touches the database
   - Keep tests focused: one behaviour per test method
3. Re-run the tests to confirm the new tests pass.

### Step 6 — Summary

End with a one-sentence verdict: either "All changed Python files have passing test coverage" or
a count of files that still need attention (with a reason if you chose not to fill the gap).
