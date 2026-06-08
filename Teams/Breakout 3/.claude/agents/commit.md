---
description: Stage and commit current changes after verifying changed Python files have up-to-date tests. Before committing, run the ensure-tests skill to keep unit tests current.
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git add:*), Bash(git commit:*), Bash(git log:*), Bash(powershell python -m unittest:*), Read, Edit, Write, Glob
---

Create a git commit for the current changes.

## Context

- Current status: !`git status --short`
- Staged + unstaged diff: !`git diff --`
- Recent commits (for style): !`git log --oneline -10`

## Your task

1. Run the `ensure-tests` skill first. Ensure all changed Python files have passing unit test coverage and add or update tests if necessary.
2. If `ensure-tests` finds gaps, fix them before proceeding to commit.
3. Review the working tree and diff. If nothing is staged, stage only the files that belong in this commit; do NOT use `git add -A` blindly.
4. Write a clear, descriptive commit message:
   - If `$ARGUMENTS` is provided, use it verbatim as the summary line.
   - Otherwise write an imperative summary line of about 50 characters with a short body if needed.
5. Commit the staged changes.
6. Show the resulting commit with `git log --oneline -1`.

Usage: `/commit [title]` — optional `title` becomes the commit summary line. Do NOT push unless explicitly asked.
