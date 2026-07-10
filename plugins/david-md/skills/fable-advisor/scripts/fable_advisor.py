#!/usr/bin/env python3
"""Run Fable as a verified, read-only Claude Code advisor."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from datetime import datetime, timezone
from typing import Any, Iterable
from uuid import uuid4


ADVISOR_SYSTEM_PROMPT = """You are an advisor inside Claude Code. Inspect relevant evidence and return planning or review advice only. Do not edit files, mutate git state, invoke write-capable external tools, send messages, deploy, or change external state. Prefer the available read-only tools over asking the caller to paste evidence. Clearly separate verified facts, inferences, and blockers."""

BASE_READ_TOOLS = (
    "Read",
    "Glob",
    "Grep",
    "WebSearch",
    "WebFetch",
)

BUILTIN_READ_TOOLS = ("Read", "Glob", "Grep", "WebSearch", "WebFetch", "Bash")

DISALLOWED_TOOLS = (
    "Edit",
    "Write",
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

def unique(items: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(items))


def effective_read_tools(args: argparse.Namespace) -> list[str]:
    return unique(BASE_READ_TOOLS)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"cannot validate invalid Claude settings JSON at {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"Claude settings must contain an object: {path}")
    return value


def validate_settings(args: argparse.Namespace, cwd: Path) -> None:
    safe_rules = set(effective_read_tools(args))
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
            "unsafe Claude permission environment for a read-only advisor; "
            f"remove or narrow these rules before retrying: {details}"
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Claude Fable as a streamed, verified read-only advisor."
    )
    parser.add_argument("prompt", nargs="?", help="Prompt text; stdin is preferred")
    parser.add_argument("--prompt-file", type=Path, help="Read the prompt from a file")
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--add-dir", action="append", type=Path, default=[])
    parser.add_argument("--resume", help="Resume a prior Claude Code session ID")
    parser.add_argument(
        "--max-turns",
        type=int,
        help="Optional agent-turn cap; omitted by default so long reviews can finish",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=Path.home() / ".codex" / "fable-advisor" / "runs",
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
    tools = effective_read_tools(args)

    command = [
        claude_bin,
        "-p",
        "--model",
        "fable",
        "--effort",
        "high",
        "--permission-mode",
        "dontAsk",
        "--tools",
        ",".join(BUILTIN_READ_TOOLS),
        "--disallowedTools",
        ",".join(DISALLOWED_TOOLS),
        "--output-format",
        "stream-json",
        "--verbose",
        "--append-system-prompt",
        ADVISOR_SYSTEM_PROMPT,
        "--allowedTools",
        ",".join(tools),
    ]
    if args.max_turns is not None:
        command.extend(["--max-turns", str(args.max_turns)])
    for directory in args.add_dir:
        command.extend(["--add-dir", str(directory.expanduser().resolve())])
    if args.resume:
        command.extend(["--resume", args.resume])
    else:
        command.extend(["--session-id", session_id])
    return command


def emit_progress(event: dict[str, Any]) -> None:
    if event.get("type") == "system" and event.get("subtype") == "init":
        print(
            "[fable-advisor] "
            f"session={event.get('session_id')} model={event.get('model')} "
            f"tools={len(event.get('tools', []))}",
            file=sys.stderr,
            flush=True,
        )
    if event.get("type") == "assistant":
        for block in event.get("message", {}).get("content", []):
            if block.get("type") == "tool_use":
                print(
                    f"[fable-advisor] tool={block.get('name')}",
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
        )

        def drain_stderr() -> None:
            assert process.stderr is not None
            for line in process.stderr:
                raw_stderr.write(line)
                raw_stderr.flush()
                print(f"[fable-advisor:claude] {line.rstrip()}", file=sys.stderr, flush=True)

        stderr_thread = threading.Thread(target=drain_stderr, daemon=True)
        stderr_thread.start()
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
                print(f"[fable-advisor:raw] {line.rstrip()}", file=sys.stderr, flush=True)
                continue
            emit_progress(event)
            if event.get("type") == "system" and event.get("subtype") == "init":
                init_model = event.get("model")
                requested_session = event.get("session_id") or requested_session
            elif event.get("type") == "assistant":
                model = event.get("message", {}).get("model")
                if model:
                    assistant_models.add(model)
            elif event.get("type") == "result":
                result = event
                requested_session = event.get("session_id") or requested_session

        return_code = process.wait()
        stderr_thread.join()

    status_prefix = (
        f"session={requested_session} log={log_path} stderr={stderr_path}"
    )
    models = ({init_model} if init_model else set()) | assistant_models
    wrong_models = sorted(model for model in models if not model.startswith("claude-fable"))
    if wrong_models:
        print(
            f"[fable-advisor] status=wrong_model models={','.join(wrong_models)} {status_prefix}",
            file=sys.stderr,
        )
        return 4
    if result is None:
        print(
            f"[fable-advisor] status=no_result exit={return_code} {status_prefix}",
            file=sys.stderr,
        )
        return 2

    denials = result.get("permission_denials") or []
    required_read_tools = set(effective_read_tools(args))
    critical_denials = [
        denial
        for denial in denials
        if denial.get("tool_name") in required_read_tools
    ]
    if critical_denials:
        print(
            "[fable-advisor] status=required_read_denied "
            f"denials={json.dumps(critical_denials)} {status_prefix}",
            file=sys.stderr,
        )
        return 3

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
            f"[fable-advisor] status=incomplete exit={return_code} diagnostic={json.dumps(diagnostic)} {status_prefix}",
            file=sys.stderr,
        )
        return 2

    final_text = result.get("result")
    if not isinstance(final_text, str) or not final_text.strip():
        print(
            f"[fable-advisor] status=empty_result {status_prefix}", file=sys.stderr
        )
        return 2

    print(final_text)
    denial_status = "success_with_denials" if denials else "success"
    print(
        "[fable-advisor] "
        f"status={denial_status} model={init_model or 'claude-fable'} "
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
        print(f"[fable-advisor] status=launcher_error error={error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
