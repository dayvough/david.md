---
name: fable-advisor
description: Run the original Claude Fable read-only planning and review workflow through the local Claude Code harness. Use only when the user explicitly invokes $fable-advisor or asks for the legacy Fable Advisor workflow. Generic Fable requests belong to $fable.
---

# Fable Advisor

Use the bundled launcher instead of calling `claude -p` directly. Resolve
`scripts/fable_advisor.py` relative to this `SKILL.md`, then invoke its absolute
path:

```sh
printf '%s\n' "<bounded advisory brief>" | \
  python3 "<this-skill-directory>/scripts/fable_advisor.py" \
    --cwd "<repo-or-worktree>"
```

Fable can also inspect another local directory when the brief genuinely spans
repositories:

```sh
--add-dir /another/readable/repo
```

The launcher maximizes evidence access while keeping the advisor free of side
effects. It:

- uses the local Claude Code engine with `--model fable --effort high`;
- provides repository reading, search, web research, and Bash;
- uses `dontAsk` plus a fixed read-only allowlist, so other tools fail closed
  instead of pausing for an invisible prompt;
- removes editing, orchestration, and messaging tools from Claude's built-in
  inventory, and refuses inherited wildcard permissions or hooks;
- lets Claude Code's own classifier admit ordinary read-only Bash commands while
  denying redirection and mutation;
- streams verbose JSON so tool progress stays visible;
- stores the raw transcript and exposes the session ID for follow-ups;
- rejects incomplete runs, denied required read tools, and non-Fable responses.

Blocking side effects is part of making Fable an advisor. It is not a reduction
in useful advisory access: Fable can inspect broadly, but Codex remains the
execution layer and independently verifies advice before acting.

## Operating contract

1. Give Fable a bounded decision or review brief. Point it at source-of-truth
   files rather than pasting a large synthetic summary.
2. Poll the running process. Do not infer a hang from a quiet interval and do
   not impose a short timeout.
3. On success, return Fable's actual result. Codex still cross-checks facts,
   diffs, tests, and source-of-truth systems before acting. If the launcher
   reports `success_with_denials`, include the denied tool names in the outcome.
4. On a transient failure, retry once in the same session with a smaller
   follow-up:

```sh
printf '%s\n' "Continue with a narrower evidence packet: ..." | \
  python3 "<this-skill-directory>/scripts/fable_advisor.py" \
    --cwd "<same-cwd>" --resume "<session-id>"
```

5. If the retry fails, report the exact Fable blocker and log path. Do not
   substitute a Codex-authored advisory answer.

## Prerequisites

- Claude Code installed as `claude` and already authenticated.
- Access to the `fable` model in that Claude Code account.
- Python 3.10 or newer.

## Fidelity boundary

CLI and Claude Code Desktop share the Claude Code engine, settings, `CLAUDE.md`,
skills, and hooks. The launcher restores Desktop-like live tool visibility and
resumable context. It uses the CLI-only `dontAsk`
permission mode to enforce headless read-only operation; Desktop's Plan mode can
also write a plan file. The launcher cannot provide Desktop-only attachments,
visual diff panes, or computer-use approvals.
