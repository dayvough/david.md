#!/usr/bin/env python3
"""Run Fable as a verified Claude Code advisor or bounded implementer."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import threading
from datetime import datetime, timezone
from typing import Any, Iterable
from uuid import uuid4


ADVISE_SYSTEM_PROMPT = """You are an advisor inside Claude Code. Inspect relevant evidence and return planning or review advice only. Do not edit files, mutate git state, invoke write-capable external tools, send messages, deploy, or change external state. Use the available read-only tools whenever the brief points to files, repositories, the web, or an external source of truth; never claim to have inspected evidence without a corresponding tool call. Clearly separate verified facts, inferences, and blockers."""

IMPLEMENT_SYSTEM_PROMPT = """You are an implementation agent inside Claude Code. Complete the bounded request by inspecting and editing files only inside the current working directory. Run only the exact Bash commands the caller pre-approved. Do not access or modify paths outside the working directory, change git branches or history, stage or commit changes, push, deploy, publish, send messages, invoke write-capable external tools, or expose secrets. Finish with the files changed, commands run and their results, and any blockers. Do not claim verification you did not run."""

BASE_READ_TOOLS = (
    "Read",
    "Glob",
    "Grep",
    "ToolSearch",
    "WebSearch",
    "WebFetch",
)

BUILTIN_READ_TOOLS = (
    "Read",
    "Glob",
    "Grep",
    "ToolSearch",
    "WebSearch",
    "WebFetch",
    "Bash",
)

BUILTIN_WRITE_TOOLS = ("Edit", "Write")

ALWAYS_DISALLOWED_TOOLS = (
    "NotebookEdit",
    "Task",
    "Skill",
    "Workflow",
    "DesignSync",
    "EnterWorktree",
    "ExitWorktree",
    "CronCreate",
    "CronDelete",
    "PushNotification",
    "RemoteTrigger",
    "SendMessage",
    "TaskCreate",
    "TaskUpdate",
    "TaskStop",
)

FORBIDDEN_EXEC_FRAGMENTS = (
    "\n",
    "\r",
    "&&",
    "||",
    ";",
    "|",
    ">",
    "<",
    "`",
    "$(",
    "${",
    "*",
    "?",
)

FORBIDDEN_EXEC_PREFIXES = (
    ("rm",),
    ("rmdir",),
    ("shred",),
    ("dd",),
    ("mkfs",),
    ("git", "add"),
    ("git", "commit"),
    ("git", "push"),
    ("git", "reset"),
    ("git", "clean"),
    ("git", "checkout"),
    ("git", "switch"),
    ("git", "merge"),
    ("git", "rebase"),
    ("git", "cherry-pick"),
    ("gh", "pr", "merge"),
    ("npm", "publish"),
    ("pnpm", "publish"),
    ("yarn", "publish"),
    ("railway", "up"),
    ("railway", "deploy"),
    ("bash",),
    ("sh",),
    ("zsh",),
    ("fish",),
    ("python", "-c"),
    ("python3", "-c"),
    ("node", "-e"),
    ("ruby", "-e"),
    ("perl", "-e"),
    ("sudo",),
    ("brew",),
    ("launchctl",),
    ("defaults",),
    ("kill",),
    ("pkill",),
    ("chmod",),
    ("chown",),
    ("curl",),
    ("wget",),
    ("ssh",),
    ("scp",),
    ("sftp",),
    ("rsync",),
    ("nc",),
    ("netcat",),
    ("osascript",),
    ("open",),
)

PROFILE_TOOLS = {
    "linear-read": (
        "mcp__claude_ai_Linear__get_issue",
        "mcp__claude_ai_Linear__get_issue_status",
        "mcp__claude_ai_Linear__list_issue_statuses",
        "mcp__claude_ai_Linear__list_issue_labels",
        "mcp__claude_ai_Linear__get_document",
        "mcp__claude_ai_Linear__get_diff",
        "mcp__claude_ai_Linear__get_diff_threads",
    ),
    "railway-read": (
        "mcp__railway__environment_status",
        "mcp__railway__get_service_config",
        "mcp__railway__domain_status",
        "mcp__railway__private_network_status",
    ),
}

MODEL_CONFIG = {
    "fable": ("fable", "claude-fable-5"),
    "opus-5": ("opus", "claude-opus-5"),
}

FALLBACK_REASONS = (
    "availability",
    "capability",
    "context",
    "incomplete",
)


def unique(items: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(items))


def tool_name(rule: str) -> str:
    """Return the callable tool name from a Claude permission rule."""
    return rule.split("(", 1)[0]


def effective_read_tools(args: argparse.Namespace) -> list[str]:
    tools = list(BASE_READ_TOOLS)
    for profile in args.profile:
        tools.extend(PROFILE_TOOLS[profile])
    tools.extend(args.allow_tool)
    return unique(tools)


def builtin_tools(args: argparse.Namespace) -> list[str]:
    tools = list(BUILTIN_READ_TOOLS)
    if args.mode == "implement":
        tools.extend(BUILTIN_WRITE_TOOLS)
    return unique(tools)


def disallowed_tools(args: argparse.Namespace) -> list[str]:
    tools = list(ALWAYS_DISALLOWED_TOOLS)
    if args.mode == "advise":
        tools.extend(BUILTIN_WRITE_TOOLS)
    return unique(tools)


def exec_permission_rules(args: argparse.Namespace) -> list[str]:
    return [f"Bash({command})" for command in args.allow_exec]


def effective_allowed_tools(args: argparse.Namespace) -> list[str]:
    tools = effective_read_tools(args)
    if args.mode == "implement":
        tools.extend(BUILTIN_WRITE_TOOLS)
        tools.extend(exec_permission_rules(args))
    return unique(tools)


def validate_exec_permissions(args: argparse.Namespace) -> None:
    if args.allow_exec and args.mode != "implement":
        raise ValueError("--allow-exec requires --mode implement")
    if args.allow_dirty and args.mode != "implement":
        raise ValueError("--allow-dirty requires --mode implement")
    if args.mode == "implement" and any(
        tool_name(rule) == "Bash" for rule in args.allow_tool
    ):
        raise ValueError("use --allow-exec, not --allow-tool, for implement-mode Bash")
    for command in args.allow_exec:
        if not command or command != command.strip():
            raise ValueError("--allow-exec commands must be non-empty and trimmed")
        forbidden = next(
            (fragment for fragment in FORBIDDEN_EXEC_FRAGMENTS if fragment in command),
            None,
        )
        if forbidden:
            raise ValueError(
                f"unsafe --allow-exec command contains {forbidden!r}: {command}"
            )
        try:
            words = tuple(shlex.split(command))
        except ValueError as error:
            raise ValueError(f"invalid --allow-exec command {command!r}: {error}") from error
        if not words:
            raise ValueError("--allow-exec commands must contain an executable")
        if any(words[: len(prefix)] == prefix for prefix in FORBIDDEN_EXEC_PREFIXES):
            raise ValueError(f"destructive or release command is not allowed: {command}")


def scope_manifest(args: argparse.Namespace, cwd: Path) -> dict[str, Any]:
    return {
        "mode": args.mode,
        "cwd": str(cwd),
        "profiles": args.profile,
        "allowed_tools": effective_allowed_tools(args),
        "allowed_exec": args.allow_exec,
        "allow_dirty": args.allow_dirty,
        "require_tool_use": args.require_tool_use,
        "required_tools": args.require_tool,
        "add_dirs": [str(path.expanduser().resolve()) for path in args.add_dir],
        "max_turns": effective_max_turns(args),
        "timeout_minutes": effective_timeout_minutes(args),
    }


def validate_model_selection(args: argparse.Namespace, cwd: Path) -> None:
    if args.model == "opus-5":
        if not args.fallback_from or not args.fallback_reason:
            raise ValueError(
                "Opus 5 is fallback-only; provide --fallback-from <fable-audit.json> "
                "and --fallback-reason"
            )
        if args.resume:
            raise ValueError(
                "Opus 5 fallback starts a fresh audited session; use --fallback-from, "
                "not --resume"
            )
        source_path = args.fallback_from.expanduser().resolve()
        source = load_json(source_path)
        source_models = source.get("observed_models") or []
        if (
            source.get("requested_model") != "fable"
            or not source.get("session_id")
            or not source_models
            or any(not model.startswith("claude-fable-5") for model in source_models)
        ):
            raise ValueError(
                "--fallback-from must be an audit from a verified Fable run"
            )
        source_scope = source.get("scope")
        current_scope = scope_manifest(args, cwd)
        if source_scope != current_scope:
            changed = sorted(
                key
                for key in set((source_scope or {}).keys()) | set(current_scope.keys())
                if (source_scope or {}).get(key) != current_scope.get(key)
            )
            raise ValueError(
                "Opus 5 fallback must preserve the Fable scope; mismatched fields: "
                + ", ".join(changed)
            )
        args.fallback_from = source_path
        args.fallback_session_id = source["session_id"]
    elif args.fallback_from or args.fallback_reason:
        raise ValueError("fallback lineage is only valid with --model opus-5")
    else:
        args.fallback_session_id = None


def git_worktree(cwd: Path) -> tuple[Path, list[str]] | None:
    top = subprocess.run(
        ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
        check=False,
    )
    if top.returncode != 0:
        return None
    root = Path(top.stdout.strip()).resolve()
    status = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=all"],
        text=True,
        capture_output=True,
        check=False,
    )
    if status.returncode != 0:
        raise ValueError(f"cannot inspect git worktree status: {status.stderr.strip()}")
    return root, status.stdout.splitlines()


def git_patch(root: Path) -> str:
    diff = subprocess.run(
        ["git", "-C", str(root), "diff", "HEAD", "--no-ext-diff", "--binary", "--", "."],
        text=True,
        capture_output=True,
        check=False,
    )
    if diff.returncode not in (0, 128):
        raise ValueError(f"cannot capture git audit patch: {diff.stderr.strip()}")
    return diff.stdout if diff.returncode == 0 else ""


def effective_max_turns(args: argparse.Namespace) -> int | None:
    if args.max_turns is not None:
        return args.max_turns
    return 20 if args.mode == "implement" else None


def effective_timeout_minutes(args: argparse.Namespace) -> float | None:
    if args.timeout_minutes is not None:
        return args.timeout_minutes
    return 30.0 if args.mode == "implement" else None


def audit_tool_call(block: dict[str, Any]) -> dict[str, Any]:
    name = block.get("name")
    tool_input = block.get("input") if isinstance(block.get("input"), dict) else {}
    entry: dict[str, Any] = {"name": name}
    if name == "Bash" and isinstance(tool_input.get("command"), str):
        entry["command"] = tool_input["command"]
    elif name in {"Read", "Edit", "Write"}:
        path = tool_input.get("file_path") or tool_input.get("path")
        if isinstance(path, str):
            entry["path"] = path
    elif name in {"Glob", "Grep"}:
        for key in ("path", "pattern", "glob"):
            if isinstance(tool_input.get(key), str):
                entry[key] = tool_input[key]
    return entry


def stop_process_group(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def write_audit_bundle(
    *,
    args: argparse.Namespace,
    cwd: Path,
    log_path: Path,
    session_id: str,
    tool_calls: list[dict[str, Any]],
    result: dict[str, Any] | None,
    initial_worktree: tuple[Path, list[str]] | None,
    initial_patch: str,
    interrupted: bool,
    timed_out: bool,
    child_pid: int,
    observed_models: list[str],
    api_errors: list[dict[str, Any]],
) -> tuple[Path, Path | None, Path | None]:
    final_worktree = git_worktree(cwd)
    before_patch_path: Path | None = None
    after_patch_path: Path | None = None
    final_patch = ""
    if initial_worktree:
        before_patch_path = log_path.with_suffix(".before.patch")
        before_patch_path.write_text(initial_patch, encoding="utf-8")
    if final_worktree:
        final_patch = git_patch(final_worktree[0])
        after_patch_path = log_path.with_suffix(".after.patch")
        after_patch_path.write_text(final_patch, encoding="utf-8")
    audit_path = log_path.with_suffix(".audit.json")
    audit = {
        "session_id": session_id,
        "mode": args.mode,
        "requested_model": args.model,
        "observed_models": observed_models,
        "fallback_from": (
            {
                "session_id": args.fallback_session_id,
                "audit": str(args.fallback_from),
            }
            if args.fallback_from
            else None
        ),
        "fallback_reason": args.fallback_reason,
        "scope": scope_manifest(args, cwd),
        "cwd": str(cwd),
        "launcher_pid": os.getpid(),
        "child_pid": child_pid,
        "allowed_exec": args.allow_exec,
        "max_turns": effective_max_turns(args),
        "timeout_minutes": effective_timeout_minutes(args),
        "interrupted": interrupted,
        "timed_out": timed_out,
        "tool_calls": tool_calls,
        "permission_denials": (result or {}).get("permission_denials") or [],
        "api_errors": api_errors,
        "result": {
            key: (result or {}).get(key)
            for key in ("subtype", "is_error", "stop_reason", "terminal_reason")
        },
        "git": {
            "initial_status": initial_worktree[1] if initial_worktree else None,
            "final_status": final_worktree[1] if final_worktree else None,
            "before_patch": str(before_patch_path) if before_patch_path else None,
            "after_patch": str(after_patch_path) if after_patch_path else None,
        },
    }
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    return audit_path, before_patch_path, after_patch_path


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"cannot validate invalid Claude settings JSON at {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"Claude settings must contain an object: {path}")
    return value


def validate_settings(args: argparse.Namespace, cwd: Path) -> None:
    safe_rules = set(effective_allowed_tools(args))
    settings_paths = [
        Path.home() / ".claude" / "settings.json",
        cwd / ".claude" / "settings.json",
        cwd / ".claude" / "settings.local.json",
        Path("/Library/Application Support/ClaudeCode/managed-settings.json"),
        Path("/etc/claude-code/managed-settings.json"),
    ]
    unsafe: list[str] = []
    for path in settings_paths:
        if not path.is_file():
            continue
        settings = load_json(path)
        for rule in settings.get("permissions", {}).get("allow", []):
            if rule not in safe_rules:
                unsafe.append(f"{path}: permissions.allow {rule!r}")
        if settings.get("hooks"):
            unsafe.append(f"{path}: hooks are active")
        enabled_plugins = settings.get("enabledPlugins", {})
        if any(enabled_plugins.values()):
            unsafe.append(f"{path}: enabled plugins may install hooks")

    global_config_path = Path.home() / ".claude.json"
    if global_config_path.is_file():
        global_config = load_json(global_config_path)
        scoped_configs = [("global", global_config)]
        project_config = global_config.get("projects", {}).get(str(cwd), {})
        if isinstance(project_config, dict):
            scoped_configs.append((str(cwd), project_config))
        for scope, config in scoped_configs:
            for rule in config.get("allowedTools", []):
                if rule not in safe_rules:
                    unsafe.append(f"{global_config_path} [{scope}]: allowedTools {rule!r}")

    if unsafe:
        details = "; ".join(unsafe)
        raise ValueError(
            "unsafe Claude permission environment for the requested Fable mode; "
            f"remove or narrow these rules before retrying: {details}"
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Claude Fable as a streamed, verified advisor or implementer."
    )
    parser.add_argument("prompt", nargs="?", help="Prompt text; stdin is preferred")
    parser.add_argument("--prompt-file", type=Path, help="Read the prompt from a file")
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument(
        "--mode", choices=("advise", "implement"), required=True
    )
    parser.add_argument(
        "--model",
        choices=tuple(MODEL_CONFIG),
        default="fable",
        help="Use Fable by default; Opus 5 is available only as an audited fallback",
    )
    parser.add_argument(
        "--fallback-from",
        type=Path,
        help="Originating Fable audit JSON required for an Opus 5 fallback",
    )
    parser.add_argument(
        "--fallback-reason",
        choices=FALLBACK_REASONS,
        help="Recorded Fable model boundary that justifies an Opus 5 fallback",
    )
    parser.add_argument(
        "--profile", action="append", choices=sorted(PROFILE_TOOLS), default=[]
    )
    parser.add_argument(
        "--allow-tool",
        action="append",
        default=[],
        help="Pre-approve one exact additional trusted tool name",
    )
    parser.add_argument(
        "--allow-exec",
        action="append",
        default=[],
        help="In implement mode, pre-approve one exact non-destructive Bash command",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="In implement mode, acknowledge and preserve an existing dirty worktree",
    )
    parser.add_argument(
        "--require-tool-use",
        action="store_true",
        help="Fail unless Fable calls at least one available tool",
    )
    parser.add_argument(
        "--require-tool",
        action="append",
        default=[],
        help="Fail unless Fable calls this exact tool; repeat as needed",
    )
    parser.add_argument("--add-dir", action="append", type=Path, default=[])
    parser.add_argument("--resume", help="Resume a prior Claude Code session ID")
    parser.add_argument(
        "--max-turns",
        type=int,
        help="Agent-turn cap; implement mode defaults to 20",
    )
    parser.add_argument(
        "--timeout-minutes",
        type=float,
        help="Wall-clock cap; implement mode defaults to 30 minutes",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=Path.home() / ".codex" / "fable" / "runs",
    )
    return parser.parse_args(argv)


def read_prompt(args: argparse.Namespace) -> str:
    if args.prompt and args.prompt_file:
        raise ValueError("provide one prompt source: prompt text or --prompt-file")
    if args.prompt_file:
        prompt = args.prompt_file.read_text(encoding="utf-8")
    elif args.prompt:
        prompt = args.prompt
    else:
        if sys.stdin.isatty():
            raise ValueError("provide a prompt through stdin, prompt text, or --prompt-file")
        prompt = sys.stdin.read()
    if not prompt.strip():
        raise ValueError("prompt is empty")
    return prompt


def build_command(args: argparse.Namespace, session_id: str) -> list[str]:
    claude_bin = os.environ.get("FABLE_CLAUDE_BIN", "claude")
    tools = effective_allowed_tools(args)
    system_prompt = (
        IMPLEMENT_SYSTEM_PROMPT if args.mode == "implement" else ADVISE_SYSTEM_PROMPT
    )

    command = [
        claude_bin,
        "-p",
        "--model",
        MODEL_CONFIG[args.model][0],
        "--effort",
        "high",
        "--permission-mode",
        "dontAsk",
        "--tools",
        ",".join(builtin_tools(args)),
        "--disallowedTools",
        ",".join(disallowed_tools(args)),
        "--output-format",
        "stream-json",
        "--verbose",
        "--append-system-prompt",
        system_prompt,
        "--allowedTools",
        ",".join(tools),
    ]
    max_turns = effective_max_turns(args)
    if max_turns is not None:
        command.extend(["--max-turns", str(max_turns)])
    for directory in args.add_dir:
        command.extend(["--add-dir", str(directory.expanduser().resolve())])
    if args.resume:
        command.extend(["--resume", args.resume])
    else:
        command.extend(["--session-id", session_id])
    return command


def emit_progress(event: dict[str, Any]) -> None:
    if event.get("type") == "system" and event.get("subtype") == "init":
        servers = ",".join(
            f"{server.get('name')}:{server.get('status')}"
            for server in event.get("mcp_servers", [])
        ) or "none"
        print(
            "[fable] "
            f"session={event.get('session_id')} model={event.get('model')} "
            f"tools={len(event.get('tools', []))} mcp={servers}",
            file=sys.stderr,
            flush=True,
        )
    if event.get("type") == "assistant":
        for block in event.get("message", {}).get("content", []):
            if block.get("type") == "tool_use":
                print(
                    f"[fable] tool={block.get('name')}",
                    file=sys.stderr,
                    flush=True,
                )


def run(args: argparse.Namespace, prompt: str) -> int:
    cwd = args.cwd.expanduser().resolve()
    if not cwd.is_dir():
        raise ValueError(f"cwd is not a directory: {cwd}")
    for directory in args.add_dir:
        if not directory.expanduser().resolve().is_dir():
            raise ValueError(f"add-dir is not a directory: {directory}")
    validate_exec_permissions(args)
    if args.max_turns is not None and args.max_turns <= 0:
        raise ValueError("--max-turns must be positive")
    if args.timeout_minutes is not None and args.timeout_minutes <= 0:
        raise ValueError("--timeout-minutes must be positive")
    validate_model_selection(args, cwd)
    initial_worktree = git_worktree(cwd)
    initial_patch = git_patch(initial_worktree[0]) if initial_worktree else ""
    if args.mode == "implement":
        if cwd in (Path("/"), Path.home().resolve()):
            raise ValueError("implement mode requires a bounded project/worktree cwd")
        if args.add_dir:
            raise ValueError("implement mode does not allow additional writable directories")
        if initial_worktree:
            root, existing_changes = initial_worktree
            if root != cwd:
                raise ValueError(
                    f"implement mode cwd must be the git worktree root: {root}"
                )
            if existing_changes and not args.allow_dirty:
                raise ValueError(
                    "implement mode refuses a dirty worktree without --allow-dirty: "
                    + json.dumps(existing_changes)
                )
    available_tool_names = {
        tool_name(rule) for rule in (*builtin_tools(args), *effective_allowed_tools(args))
    }
    unsafe_requirements = sorted(
        required
        for required in args.require_tool
        if required not in available_tool_names
    )
    if unsafe_requirements:
        raise ValueError(
            "required tools are not in the selected mode inventory; add an exact "
            "--allow-tool rule first: " + ", ".join(unsafe_requirements)
        )
    validate_settings(args, cwd)

    requested_session = args.resume or str(uuid4())
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    args.log_dir.expanduser().mkdir(parents=True, exist_ok=True)
    log_path = args.log_dir.expanduser() / f"{timestamp}-{requested_session}.jsonl"
    stderr_path = log_path.with_suffix(".stderr")
    command = build_command(args, requested_session)

    result: dict[str, Any] | None = None
    init_model: str | None = None
    assistant_models: set[str] = set()
    api_errors: list[dict[str, Any]] = []
    called_tools: list[str] = []
    tool_calls: list[dict[str, Any]] = []
    interrupted = False
    timed_out = threading.Event()

    with log_path.open("w", encoding="utf-8") as raw_log, stderr_path.open(
        "w", encoding="utf-8"
    ) as raw_stderr:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            start_new_session=True,
        )
        print(
            "[fable] "
            f"control launcher_pid={os.getpid()} child_pid={process.pid} mode={args.mode}",
            file=sys.stderr,
            flush=True,
        )

        previous_sigterm = signal.getsignal(signal.SIGTERM)

        def terminate_launcher(signum: int, frame: Any) -> None:
            nonlocal interrupted
            interrupted = True
            stop_process_group(process)
            raise KeyboardInterrupt

        signal.signal(signal.SIGTERM, terminate_launcher)

        timeout_minutes = effective_timeout_minutes(args)
        timeout_timer: threading.Timer | None = None
        if timeout_minutes is not None:
            def timeout_process() -> None:
                timed_out.set()
                stop_process_group(process)

            timeout_timer = threading.Timer(timeout_minutes * 60, timeout_process)
            timeout_timer.daemon = True
            timeout_timer.start()

        def drain_stderr() -> None:
            assert process.stderr is not None
            for line in process.stderr:
                raw_stderr.write(line)
                raw_stderr.flush()
                print(f"[fable:claude] {line.rstrip()}", file=sys.stderr, flush=True)

        stderr_thread = threading.Thread(target=drain_stderr, daemon=True)
        stderr_thread.start()
        try:
            assert process.stdin is not None
            process.stdin.write(prompt)
            process.stdin.close()
            assert process.stdout is not None
            for line in process.stdout:
                raw_log.write(line)
                raw_log.flush()
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    print(
                        f"[fable:raw] {line.rstrip()}",
                        file=sys.stderr,
                        flush=True,
                    )
                    continue
                emit_progress(event)
                if event.get("type") == "system" and event.get("subtype") == "init":
                    init_model = event.get("model")
                    requested_session = event.get("session_id") or requested_session
                elif event.get("type") == "assistant":
                    model = event.get("message", {}).get("model")
                    if model:
                        assistant_models.add(model)
                    if event.get("is_api_error_message") or event.get("error"):
                        api_errors.append(
                            {
                                "error": event.get("error") or "api_error",
                            }
                        )
                    blocks = event.get("message", {}).get("content", [])
                    called_tools.extend(
                        block.get("name")
                        for block in blocks
                        if block.get("type") == "tool_use" and block.get("name")
                    )
                    tool_calls.extend(
                        audit_tool_call(block)
                        for block in blocks
                        if block.get("type") == "tool_use" and block.get("name")
                    )
                elif event.get("type") == "result":
                    result = event
                    requested_session = event.get("session_id") or requested_session
        except KeyboardInterrupt:
            interrupted = True
            stop_process_group(process)
        finally:
            if timeout_timer:
                timeout_timer.cancel()
            signal.signal(signal.SIGTERM, previous_sigterm)

        return_code = process.wait()
        stderr_thread.join()

    models = ({init_model} if init_model else set()) | assistant_models
    audit_path, _, after_patch_path = write_audit_bundle(
        args=args,
        cwd=cwd,
        log_path=log_path,
        session_id=requested_session,
        tool_calls=tool_calls,
        result=result,
        initial_worktree=initial_worktree,
        initial_patch=initial_patch,
        interrupted=interrupted,
        timed_out=timed_out.is_set(),
        child_pid=process.pid,
        observed_models=sorted(models),
        api_errors=api_errors,
    )

    status_prefix = (
        f"session={requested_session} log={log_path} stderr={stderr_path} "
        f"audit={audit_path} patch={after_patch_path or 'none'}"
    )
    if interrupted:
        print(f"[fable] status=interrupted {status_prefix}", file=sys.stderr)
        return 130
    if timed_out.is_set():
        print(f"[fable] status=timed_out {status_prefix}", file=sys.stderr)
        return 124
    if api_errors:
        error_names = sorted(
            {
                error.get("error") or "api_error"
                for error in api_errors
            }
        )
        guidance = (
            " retry_with_network_and_keychain_access_before_login=true"
            if "authentication_failed" in error_names
            else ""
        )
        print(
            "[fable] status=api_error "
            f"errors={json.dumps(error_names)}{guidance} {status_prefix}",
            file=sys.stderr,
        )
        return 2
    if not models:
        print(f"[fable] status=model_unreported {status_prefix}", file=sys.stderr)
        return 4
    expected_model_prefix = MODEL_CONFIG[args.model][1]
    wrong_models = sorted(
        model for model in models if not model.startswith(expected_model_prefix)
    )
    if wrong_models:
        print(
            f"[fable] status=wrong_model models={','.join(wrong_models)} {status_prefix}",
            file=sys.stderr,
        )
        return 4
    if result is None:
        print(
            f"[fable] status=no_result exit={return_code} {status_prefix}",
            file=sys.stderr,
        )
        return 2

    denials = result.get("permission_denials") or []
    required_tools = {
        tool_name(rule) for rule in (*effective_allowed_tools(args), *args.require_tool)
    }
    critical_denials = [
        denial
        for denial in denials
        if denial.get("tool_name") in required_tools
    ]
    if critical_denials:
        print(
            "[fable] status=required_tool_denied "
            f"denials={json.dumps(critical_denials)} {status_prefix}",
            file=sys.stderr,
        )
        return 3

    denied_tool_names = {
        denial.get("tool_name") for denial in denials if denial.get("tool_name")
    }
    called_available_tools = [
        name
        for name in called_tools
        if name in available_tool_names and name not in denied_tool_names
    ]
    missing_required_tools = sorted(
        set(args.require_tool) - set(called_available_tools)
    )
    if (args.require_tool_use and not called_available_tools) or missing_required_tools:
        print(
            "[fable] status=required_tool_not_used "
            f"called={json.dumps(called_tools)} "
            f"missing={json.dumps(missing_required_tools)} {status_prefix}",
            file=sys.stderr,
        )
        return 5

    if (
        return_code != 0
        or result.get("subtype") != "success"
        or result.get("is_error")
        or result.get("stop_reason") != "end_turn"
        or result.get("terminal_reason") != "completed"
    ):
        diagnostic = {
            key: result.get(key)
            for key in (
                "subtype",
                "is_error",
                "api_error_status",
                "stop_reason",
                "terminal_reason",
                "result",
            )
        }
        print(
            f"[fable] status=incomplete exit={return_code} diagnostic={json.dumps(diagnostic)} {status_prefix}",
            file=sys.stderr,
        )
        return 2

    final_text = result.get("result")
    if not isinstance(final_text, str) or not final_text.strip():
        print(
            f"[fable] status=empty_result {status_prefix}", file=sys.stderr
        )
        return 2

    print(final_text)
    denial_status = "success_with_denials" if denials else "success"
    print(
        "[fable] "
        f"status={denial_status} mode={args.mode} requested_model={args.model} "
        f"model={init_model or 'unreported'} "
        f"turns={result.get('num_turns')} duration_ms={result.get('duration_ms')} "
        f"cost_usd={result.get('total_cost_usd')} denials={json.dumps(denials)} "
        f"{status_prefix}",
        file=sys.stderr,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        prompt = read_prompt(args)
        return run(args, prompt)
    except (OSError, ValueError) as error:
        print(f"[fable] status=launcher_error error={error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
