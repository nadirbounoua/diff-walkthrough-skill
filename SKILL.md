---
name: diff-walkthrough
description: Walk a human through a code diff as a GitHub-style side-by-side HTML page, published as a private claude.ai Artifact when the host supports it, else saved as a local HTML file. Groups hunks by logical change, gives each change one short explanation, flags issues inline, and folds trivial edits (imports, renames, lockfiles) into a collapsed Minor section. Use when the user runs /diff-walkthrough, or asks to explain, walk through or visually review a branch, PR or diff.
---

# Diff walkthrough

Output is one page a reviewer reads top to bottom: each change explained once, its code
shown side by side beneath it. Minimal text; the diff carries the detail.

## 1. Get the diff

Argument decides the target; work in a `diff-walkthrough/` folder in the session scratchpad (or a temp dir if there is none).

- **None** — current branch vs its base plus uncommitted work. Base from
  `git symbolic-ref refs/remotes/origin/HEAD` (fall back to `main`):
  `git diff $(git merge-base origin/<base> HEAD)`, then append each untracked file with
  `git diff --no-index /dev/null <file>` (from `git ls-files --others --exclude-standard`).
- **PR number** — `gh pr diff <n>`.
- **Range** (`a..b`, `a...b`, a sha) — `git diff <range>`.

Save it as `diff.patch`. Empty diff → say so and stop.

## 2. Plan the changes

Run `python3 <skill dir>/build.py list diff.patch` (`<skill dir>` = the folder holding this file) for the hunk ids
(`path#n`, or bare `path` for a file with no hunks, e.g. binary or pure rename). Read the diff,
opening surrounding code only where a hunk is unclear.

Write `plan.json`:

```json
{
  "title": "feature/x walkthrough",
  "target": "`feature/x` vs `main` · 12 files",
  "summary": "One or two sentences: what the diff does overall.",
  "changes": [
    {"title": "Retry failed webhooks", "explain": "…", "issues": ["…"], "hunks": ["src/a.go#2", "src/b.go"]}
  ],
  "minor": [{"title": "Unused imports removed", "hunks": ["src/a.go#1"]}],
  "skipped": [{"file": "package-lock.json", "text": "updated"}]
}
```

Rules:

- **One change = one intent.** Hunks serving the same change share one entry and one explanation,
  across files. Order changes so each reads after what it depends on (core logic before callers,
  code before tests).
- **`explain`**: 1–3 short sentences — what it does and why, not a line-by-line retelling.
  Backticks for identifiers.
- **`issues`**: likely bugs, missing handling, risky or inconsistent code, leftover debug.
  One line each, concrete. Omit the key when there are none; never pad.
- **`minor`**: imports, renames, formatting, comments, trivial tweaks — title only, no `explain`.
  Promote to `changes` when it matters (e.g. a new dependency).
- **`skipped`**: lockfiles, generated code, snapshots, binaries — one line, no diff.
- Every hunk must be in exactly one place; the build fails on unassigned or unknown ids.

## 3. Build and publish

1. `python3 <skill dir>/build.py build diff.patch plan.json walkthrough.html`
   — fix `plan.json` and rerun on errors.
2. Deliver the page, based on the tools you actually have:
   - **Artifact tool available** (Claude Code / claude.ai): load `artifact-design` (page is
     pre-built; only the contract matters) and publish `walkthrough.html` with the Artifact tool,
     icon `code`. Re-running on the same target republishes to the same file path, so the URL stays.
   - **Otherwise**: if the host has an equivalent rendered-page feature (canvas, preview pane),
     use it. Else keep `walkthrough.html` in the working folder (not the repo, or the next run
     diffs it), open it with `xdg-open` / `open` / `start` if a desktop is present, and give
     its absolute path.
3. Reply with the link or path, the change count, and the issues as a short list. Nothing else.
