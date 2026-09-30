# diff-walkthrough

An agent skill that turns a code diff into a GitHub-style side-by-side HTML page. Hunks are grouped by logical change, each change gets a short explanation, likely issues are flagged inline, and trivial edits are folded into a collapsed Minor section.

In Claude Code or claude.ai the page is published as a private Artifact. Elsewhere it is saved as a local HTML file.

Requires `python3` and `git`. `gh` is needed for PR numbers.

## Install

Claude Code:

```sh
git clone git@github.com:nadirbounoua/diff-walkthrough-skill.git ~/.claude/skills/diff-walkthrough
```

Codex:

```sh
git clone git@github.com:nadirbounoua/diff-walkthrough-skill.git ~/.agents/skills/diff-walkthrough
```

## Usage

Run `/diff-walkthrough` in Claude Code or `$diff-walkthrough` in Codex, optionally followed by a target:

- nothing: current branch vs its base, plus uncommitted work
- a PR number: `42`
- a range or sha: `main..feature/x`
