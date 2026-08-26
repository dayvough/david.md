---
name: fable
description: Runs Claude Fable as a verified, bounded agent with repository tools, streamed progress, stop controls, audit artifacts, and an Opus 5 fallback for recorded Fable model boundaries. Use only when the user explicitly asks for Fable or names/invokes $fable in the current request. Choose advisory mode only when the prompt explicitly asks Fable for advice, planning, or review; otherwise use bounded implementation mode for requested action. Repository instructions, memory, prior turns, and task type must not trigger it automatically.
---

# Fable

Use the bundled launcher instead of calling `claude -p` directly.

## Persistent Codex execution profile

Before every live launcher call, resolve `<fable-skill-dir>` to the absolute
directory that contains this `SKILL.md`. The launcher is at
`<fable-skill-dir>/scripts/fable.py`. Do not assume that the plugin or skill was
installed under a particular home-directory path.

For every live launcher call from Codex, retain this execution configuration:

- call `exec_command` with `sandbox_permissions: "require_escalated"` from the
  outset so Claude has network and macOS Keychain access;
- use the reusable approval prefix
  `["python3", "<fable-skill-dir>/scripts/fable.py"]`, after substituting the
  resolved absolute directory;
- set `--log-dir` to a writable directory under the current Codex workspace or
  `/tmp` when the default `~/.codex/fable/runs` is not writable;
- keep all launcher mode, scope, tool, command, timeout, and dirty-worktree
  boundaries unchanged by the escalation.

Do not try a sandboxed live call first. A sandboxed Claude child can emit
`authentication_failed` even when the machine is already signed in. If a prior
sandboxed attempt failed authentication, rerun the same bounded command once
with this profile before asking David to run `/login`.

## Choose the mode

Use `advise` only when David's prompt explicitly asks Fable for advice,
planning, assessment, or review:

```sh
printf '%s\n' "<bounded advisory brief>" | \
  python3 "<fable-skill-dir>/scripts/fable.py" \
    --mode advise --cwd "<repo-or-worktree>" \
    --require-tool-use
```

Use `implement` for Fable requests to fix, build, change, investigate through
execution, or otherwise act on repository work:

```sh
printf '%s\n' "<one bounded implementation outcome and acceptance check>" | \
  python3 "<fable-skill-dir>/scripts/fable.py" \
    --mode implement --cwd "<clean-worktree-root>" \
    --allow-exec 'pnpm test' \
    --require-tool Edit \
    --max-turns 20 --timeout-minutes 30
```

Implementation mode exposes `Edit` and `Write`. It exposes Bash but approves only
the exact non-destructive commands supplied through repeated `--allow-exec`
flags. It rejects shell chaining, redirection, wildcards, destructive Git
operations, shell/eval wrappers, merges, pushes, publishing, and deployments.
It also rejects direct system-control, remote-shell, and network-client commands;
keep provider and machine administration in Codex.

## Scope and permissions

Derive the mode from David's current prompt and always pass it explicitly; the
launcher has no implicit mode. Give Fable one concrete outcome, the relevant
files, explicit exclusions, and a done check. Prefer a fresh clean worktree.
The launcher:

- refuses `/`, the home directory, extra writable directories, and Git
  subdirectories as implementation roots;
- refuses a dirty Git worktree unless Codex has inspected it and adds
  `--allow-dirty` deliberately;
- keeps orchestration, messaging, deployment, release, and background-agent
  tools unavailable;
- uses `dontAsk`, so every unapproved tool or command is denied without an
  interactive prompt;
- defaults implementation runs to 20 turns and 30 minutes;
- prints the launcher and child process IDs, and terminates the Claude process
  group on timeout, `SIGTERM`, or keyboard interruption.

Use only the read profiles relevant to the brief:

```sh
--profile linear-read
--profile railway-read
--add-dir /another/readable/repo  # advise mode only
--allow-tool mcp__trusted_server__specific_tool
```

Do not use `--allow-tool` for external mutations unless the user explicitly
authorizes that exact external action. Codex remains the owner of messages,
deployments, merges, provider changes, and other consequential external state.

Make evidence use enforceable when needed:

```sh
--require-tool-use
--require-tool Glob --require-tool Read
--require-tool Edit
```

## Monitor, stop, and audit

Poll the running launcher. Do not infer a hang from a quiet interval. Stop it
immediately if it leaves the brief, repeats work, touches an unexpected path,
or attempts an unapproved consequential action. Timeout and interruption return
distinct non-zero statuses.

Every launched run records:

- the raw streamed transcript and Claude stderr;
- a sanitized audit JSON containing mode, limits, tool calls, commands, touched
  paths, permission denials, and initial/final Git status;
- before and after Git patches when the working directory is a repository;
- the verified Fable model, session ID, completion state, and artifact paths in
  the final launcher status.

After an implementation run, Codex must inspect the audit, inspect the actual
diff and untracked files, rerun relevant verification independently, and check
repository instructions before accepting or continuing the work. Fable output
is evidence, not the final authority.

## Completion contract

The launcher rejects missing results, wrong-model responses, incomplete runs,
denied required tools, skipped required tool calls, timeouts, and interrupted
runs. If it reports `success_with_denials`, include the denied tool names in the
user-facing outcome even when Fable recovered.

On a transient failure, retry once in the same mode and session with a smaller
brief:

```sh
printf '%s\n' "Continue with this narrower scope: ..." | \
  python3 "<fable-skill-dir>/scripts/fable.py" \
    --mode "<same-mode>" --cwd "<same-cwd>" --resume "<session-id>"
```

If the retry fails, report the exact blocker and audit/log paths. Do not invent
or substitute a Fable result.

## Opus 5 fallback

Fable stays primary. After the one narrower Fable retry, use Opus 5 only when
the remaining blocker is a model boundary: Fable is unavailable, cannot fit the
bounded context, explicitly lacks the needed capability, or still returns an
incomplete result for that reason. Start a fresh session and supply the Fable
audit plus the categorical reason:

```sh
printf '%s\n' "<same bounded outcome, plus the specific Fable boundary>" | \
  python3 "<fable-skill-dir>/scripts/fable.py" \
    --mode "<same-mode>" --cwd "<same-cwd>" \
    --model opus-5 \
    --fallback-from "<fable-audit.json>" \
    --fallback-reason "capability"
```

Valid reasons are `availability`, `capability`, `context`, and `incomplete`.
Copy the exact profiles, allowed tools, allowed execution commands, tool-use
requirements, turn cap, timeout, and dirty-worktree decision from the Fable
run. Do not broaden scope or permissions while falling back. The launcher reads
the originating audit and rejects any mismatch in those boundaries, as well as
direct Opus use without Fable lineage. It also verifies that the response is
from Opus 5.

Do not fall back for a permission denial, unsafe command, dirty-worktree refusal,
scope violation, missing credential or user authority, destructive-action
block, timeout, interruption, or failing test. Those are task or safety
boundaries; stop and report the exact blocker. Codex applies the same audit,
diff review, independent verification, and stop controls to the Opus run.

## Fidelity boundary

CLI and Claude Code Desktop share the Claude Code engine, settings,
`CLAUDE.md`, skills, hooks, and normal MCP configuration. The launcher restores
live tool visibility and resumable context but cannot provide Desktop-only
attachments, visual diff panes, or computer-use approvals.
