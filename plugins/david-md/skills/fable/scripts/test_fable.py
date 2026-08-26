#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import time
import unittest


SCRIPT = Path(__file__).with_name("fable.py")
SKILL = SCRIPT.parent.parent / "SKILL.md"


class FableTests(unittest.TestCase):
    def test_skill_persists_codex_execution_profile(self) -> None:
        skill = SKILL.read_text(encoding="utf-8")
        self.assertIn("## Required Codex launcher settings", skill)
        self.assertIn('sandbox_permissions: "require_escalated"', skill)
        self.assertIn(
            '["python3", "<fable-skill-dir>/scripts/fable.py"]',
            skill,
        )
        self.assertNotIn("/Users/", skill)
        self.assertIn("Do not try a sandboxed live call first", skill)

    @staticmethod
    def advice_scope(root: Path) -> dict:
        return {
            "mode": "advise",
            "cwd": str(root.resolve()),
            "profiles": ["linear-read"],
            "allowed_tools": [
                "Read",
                "Glob",
                "Grep",
                "ToolSearch",
                "WebSearch",
                "WebFetch",
                "mcp__claude_ai_Linear__get_issue",
                "mcp__claude_ai_Linear__get_issue_status",
                "mcp__claude_ai_Linear__list_issue_statuses",
                "mcp__claude_ai_Linear__list_issue_labels",
                "mcp__claude_ai_Linear__get_document",
                "mcp__claude_ai_Linear__get_diff",
                "mcp__claude_ai_Linear__get_diff_threads",
            ],
            "allowed_exec": [],
            "allow_dirty": False,
            "require_tool_use": False,
            "required_tools": [],
            "add_dirs": [],
            "max_turns": None,
            "timeout_minutes": None,
        }

    def run_case(
        self,
        events: list[dict],
        expected_code: int,
        extra_args: list[str] | None = None,
        fake_delay: float = 0,
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case_args = list(extra_args or [])
            requested_model = "opus-5" if "opus-5" in case_args else "fable"
            if requested_model == "opus-5":
                source_path = root / "fable-source.audit.json"
                source_path.write_text(
                    json.dumps(
                        {
                            "session_id": "fable-session",
                            "requested_model": "fable",
                            "observed_models": ["claude-fable-5"],
                            "scope": self.advice_scope(root),
                        }
                    ),
                    encoding="utf-8",
                )
                fallback_index = case_args.index("--fallback-from") + 1
                case_args[fallback_index] = str(source_path)
            fake = root / "fake-claude"
            fake.write_text(
                "#!/usr/bin/env python3\n"
                "import json, os, sys, time\n"
                "open(os.environ['CAPTURE_ARGS'], 'w').write(json.dumps(sys.argv[1:]))\n"
                "sys.stdin.read()\n"
                "time.sleep(float(os.environ.get('FAKE_DELAY', '0')))\n"
                "for event in json.loads(os.environ['FAKE_EVENTS']): print(json.dumps(event), flush=True)\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            capture = root / "args.json"
            env = os.environ.copy()
            env.update(
                FABLE_CLAUDE_BIN=str(fake),
                FAKE_EVENTS=json.dumps(events),
                CAPTURE_ARGS=str(capture),
                FAKE_DELAY=str(fake_delay),
            )
            command = [
                sys.executable,
                str(SCRIPT),
                "--cwd",
                str(root),
                "--mode",
                "advise",
                "--log-dir",
                str(root / "logs"),
                "--profile",
                "linear-read",
            ]
            command.extend(case_args)
            completed = subprocess.run(
                command,
                input="Review this read-only change.",
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(completed.returncode, expected_code, completed.stderr)
            args = json.loads(capture.read_text(encoding="utf-8"))
            self.assertIn("stream-json", args)
            self.assertIn("--verbose", args)
            self.assertIn("dontAsk", args)
            self.assertEqual(
                args[args.index("--model") + 1],
                "opus" if requested_model == "opus-5" else "fable",
            )
            builtin_tools = args[args.index("--tools") + 1]
            self.assertIn("Read", builtin_tools)
            self.assertIn("Bash", builtin_tools)
            disallowed = args[args.index("--disallowedTools") + 1]
            disallowed_names = set(disallowed.split(","))
            allowed = args[args.index("--allowedTools") + 1]
            self.assertIn("ToolSearch", allowed)
            self.assertIn("mcp__claude_ai_Linear__get_issue", allowed)
            if "implement" in (extra_args or []):
                self.assertIn("Edit", builtin_tools)
                self.assertIn("Write", builtin_tools)
                self.assertNotIn("Edit", disallowed_names)
                self.assertNotIn("Write", disallowed_names)
                self.assertIn("Edit", allowed)
                self.assertIn("Write", allowed)
                self.assertIn("--max-turns", args)
                self.assertEqual(args[args.index("--max-turns") + 1], "20")
            else:
                self.assertNotIn("Edit", builtin_tools)
                self.assertIn("Edit", disallowed_names)
                self.assertIn("Write", disallowed_names)
                self.assertNotIn("Bash(", allowed)
                self.assertNotIn("--max-turns", args)
            audit_paths = list((root / "logs").glob("*.audit.json"))
            self.assertEqual(len(audit_paths), 1)
            audit = json.loads(audit_paths[0].read_text(encoding="utf-8"))
            self.assertEqual(
                audit["mode"], "implement" if "implement" in (extra_args or []) else "advise"
            )
            self.assertEqual(audit["requested_model"], requested_model)
            if requested_model == "opus-5":
                self.assertEqual(
                    audit["fallback_from"]["session_id"], "fable-session"
                )
                self.assertIn(audit["fallback_reason"], ("availability", "capability"))
            expected_tool_names = [
                block["name"]
                for event in events
                if event.get("type") == "assistant"
                for block in event.get("message", {}).get("content", [])
                if block.get("type") == "tool_use" and block.get("name")
            ]
            self.assertEqual(
                [entry["name"] for entry in audit["tool_calls"]],
                expected_tool_names,
            )
            return completed

    def test_success_returns_only_fable_result_on_stdout(self) -> None:
        completed = self.run_case(
            [
                {
                    "type": "system",
                    "subtype": "init",
                    "session_id": "session-1",
                    "model": "claude-fable-5",
                    "tools": ["Read", "ToolSearch"],
                    "mcp_servers": [],
                },
                {
                    "type": "assistant",
                    "message": {"model": "claude-fable-5", "content": []},
                },
                {
                    "type": "result",
                    "subtype": "success",
                    "is_error": False,
                    "session_id": "session-1",
                    "stop_reason": "end_turn",
                    "terminal_reason": "completed",
                    "permission_denials": [],
                    "result": "Actual Fable advice",
                    "num_turns": 1,
                },
            ],
            0,
        )
        self.assertEqual(completed.stdout.strip(), "Actual Fable advice")
        self.assertIn("status=success", completed.stderr)

    def test_requires_explicit_mode_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--cwd", temporary],
                input="Do the bounded task.",
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 2, completed.stderr)
            self.assertIn("--mode", completed.stderr)
            self.assertIn("required", completed.stderr)

    def test_rejects_non_fable_response(self) -> None:
        completed = self.run_case(
            [
                {
                    "type": "system",
                    "subtype": "init",
                    "session_id": "session-2",
                    "model": "claude-fable-5",
                    "tools": [],
                    "mcp_servers": [],
                },
                {
                    "type": "assistant",
                    "message": {"model": "claude-opus-4-8", "content": []},
                },
                {
                    "type": "result",
                    "subtype": "success",
                    "is_error": False,
                    "session_id": "session-2",
                    "stop_reason": "end_turn",
                    "terminal_reason": "completed",
                    "permission_denials": [],
                    "result": "Fallback output",
                },
            ],
            4,
        )
        self.assertEqual(completed.stdout, "")
        self.assertIn("status=wrong_model", completed.stderr)

    def test_reports_synthetic_authentication_failure_before_wrong_model(self) -> None:
        completed = self.run_case(
            [
                {
                    "type": "system",
                    "subtype": "init",
                    "session_id": "session-auth",
                    "model": "claude-fable-5",
                    "tools": [],
                    "mcp_servers": [],
                },
                {
                    "type": "assistant",
                    "message": {
                        "model": "<synthetic>",
                        "content": [
                            {
                                "type": "text",
                                "text": "Not logged in - Please run /login",
                            }
                        ],
                    },
                    "error": "authentication_failed",
                    "is_api_error_message": True,
                },
                {
                    "type": "result",
                    "subtype": "success",
                    "is_error": True,
                    "session_id": "session-auth",
                    "stop_reason": "stop_sequence",
                    "terminal_reason": "api_error",
                    "permission_denials": [],
                    "result": "Not logged in - Please run /login",
                },
            ],
            2,
        )
        self.assertEqual(completed.stdout, "")
        self.assertIn("status=api_error", completed.stderr)
        self.assertIn("authentication_failed", completed.stderr)
        self.assertIn(
            "retry_with_network_and_keychain_access_before_login=true",
            completed.stderr,
        )
        self.assertNotIn("status=wrong_model", completed.stderr)

    def test_opus_5_fallback_requires_audited_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--cwd",
                    temporary,
                    "--mode",
                    "advise",
                    "--model",
                    "opus-5",
                ],
                input="Continue the bounded task.",
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn("Opus 5 is fallback-only", completed.stderr)

    def test_opus_5_fallback_rejects_scope_broadening(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "fable-source.audit.json"
            source.write_text(
                json.dumps(
                    {
                        "session_id": "fable-session",
                        "requested_model": "fable",
                        "observed_models": ["claude-fable-5"],
                        "scope": self.advice_scope(root),
                    }
                ),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--cwd",
                    str(root),
                    "--mode",
                    "advise",
                    "--profile",
                    "linear-read",
                    "--model",
                    "opus-5",
                    "--fallback-from",
                    str(source),
                    "--fallback-reason",
                    "capability",
                    "--allow-tool",
                    "UnexpectedWriteTool",
                ],
                input="Continue with broader access.",
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn("must preserve the Fable scope", completed.stderr)
            self.assertIn("allowed_tools", completed.stderr)

    def test_opus_5_fallback_is_verified_and_audited(self) -> None:
        completed = self.run_case(
            [
                {
                    "type": "system",
                    "subtype": "init",
                    "session_id": "opus-session",
                    "model": "claude-opus-5",
                    "tools": ["Read"],
                    "mcp_servers": [],
                },
                {
                    "type": "assistant",
                    "message": {"model": "claude-opus-5", "content": []},
                },
                {
                    "type": "result",
                    "subtype": "success",
                    "is_error": False,
                    "session_id": "opus-session",
                    "stop_reason": "end_turn",
                    "terminal_reason": "completed",
                    "permission_denials": [],
                    "result": "Bounded Opus fallback result",
                },
            ],
            0,
            [
                "--model",
                "opus-5",
                "--fallback-from",
                "fable-session",
                "--fallback-reason",
                "capability",
            ],
        )
        self.assertEqual(completed.stdout.strip(), "Bounded Opus fallback result")
        self.assertIn("requested_model=opus-5", completed.stderr)

    def test_opus_fallback_rejects_non_opus_5_response(self) -> None:
        completed = self.run_case(
            [
                {
                    "type": "system",
                    "subtype": "init",
                    "session_id": "old-opus-session",
                    "model": "claude-opus-4-8",
                    "tools": [],
                    "mcp_servers": [],
                },
                {
                    "type": "result",
                    "subtype": "success",
                    "is_error": False,
                    "session_id": "old-opus-session",
                    "stop_reason": "end_turn",
                    "terminal_reason": "completed",
                    "permission_denials": [],
                    "result": "Wrong Opus generation",
                },
            ],
            4,
            [
                "--model",
                "opus-5",
                "--fallback-from",
                "fable-session",
                "--fallback-reason",
                "availability",
            ],
        )
        self.assertEqual(completed.stdout, "")
        self.assertIn("status=wrong_model", completed.stderr)

    def test_allows_blocked_mutation_when_fable_still_completes(self) -> None:
        completed = self.run_case(
            [
                {
                    "type": "system",
                    "subtype": "init",
                    "session_id": "session-3",
                    "model": "claude-fable-5",
                    "tools": [],
                    "mcp_servers": [],
                },
                {
                    "type": "result",
                    "subtype": "success",
                    "is_error": False,
                    "session_id": "session-3",
                    "stop_reason": "end_turn",
                    "terminal_reason": "completed",
                    "permission_denials": [{"tool_name": "Edit"}],
                    "result": "Recovered read-only answer",
                },
            ],
            0,
        )
        self.assertEqual(completed.stdout.strip(), "Recovered read-only answer")
        self.assertIn("status=success_with_denials", completed.stderr)

    def test_rejects_denied_required_read_tool(self) -> None:
        completed = self.run_case(
            [
                {
                    "type": "system",
                    "subtype": "init",
                    "session_id": "session-read-denial",
                    "model": "claude-fable-5",
                    "tools": ["Read"],
                    "mcp_servers": [],
                },
                {
                    "type": "result",
                    "subtype": "success",
                    "is_error": False,
                    "session_id": "session-read-denial",
                    "stop_reason": "end_turn",
                    "terminal_reason": "completed",
                    "permission_denials": [{"tool_name": "Read"}],
                    "result": "Answer without required evidence",
                },
            ],
            3,
        )
        self.assertEqual(completed.stdout, "")
        self.assertIn("status=required_tool_denied", completed.stderr)

    def test_rejects_missing_result_event(self) -> None:
        completed = self.run_case(
            [
                {
                    "type": "system",
                    "subtype": "init",
                    "session_id": "session-4",
                    "model": "claude-fable-5",
                    "tools": [],
                    "mcp_servers": [],
                }
            ],
            2,
        )
        self.assertEqual(completed.stdout, "")
        self.assertIn("status=no_result", completed.stderr)

    def test_rejects_success_without_reported_model(self) -> None:
        completed = self.run_case(
            [
                {
                    "type": "result",
                    "subtype": "success",
                    "is_error": False,
                    "session_id": "session-no-model",
                    "stop_reason": "end_turn",
                    "terminal_reason": "completed",
                    "permission_denials": [],
                    "result": "Unverified model output",
                }
            ],
            4,
        )
        self.assertEqual(completed.stdout, "")
        self.assertIn("status=model_unreported", completed.stderr)

    def test_requires_any_safe_tool_use_when_requested(self) -> None:
        completed = self.run_case(
            [
                {
                    "type": "system",
                    "subtype": "init",
                    "session_id": "session-no-tool",
                    "model": "claude-fable-5",
                    "tools": ["Read"],
                    "mcp_servers": [],
                },
                {
                    "type": "result",
                    "subtype": "success",
                    "is_error": False,
                    "session_id": "session-no-tool",
                    "stop_reason": "end_turn",
                    "terminal_reason": "completed",
                    "permission_denials": [],
                    "result": "Unsupported answer",
                },
            ],
            5,
            ["--require-tool-use"],
        )
        self.assertEqual(completed.stdout, "")
        self.assertIn("status=required_tool_not_used", completed.stderr)

    def test_requires_specific_safe_tools_when_requested(self) -> None:
        completed = self.run_case(
            [
                {
                    "type": "system",
                    "subtype": "init",
                    "session_id": "session-tools",
                    "model": "claude-fable-5",
                    "tools": ["Glob", "Read"],
                    "mcp_servers": [],
                },
                {
                    "type": "assistant",
                    "message": {
                        "model": "claude-fable-5",
                        "content": [
                            {"type": "tool_use", "name": "Glob"},
                            {"type": "tool_use", "name": "Read"},
                        ],
                    },
                },
                {
                    "type": "result",
                    "subtype": "success",
                    "is_error": False,
                    "session_id": "session-tools",
                    "stop_reason": "end_turn",
                    "terminal_reason": "completed",
                    "permission_denials": [],
                    "result": "Evidence-backed answer",
                },
            ],
            0,
            ["--require-tool", "Glob", "--require-tool", "Read"],
        )
        self.assertEqual(completed.stdout.strip(), "Evidence-backed answer")

    def test_rejects_unsafe_required_tool_before_launch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--cwd",
                    temporary,
                    "--mode",
                    "advise",
                    "--log-dir",
                    str(Path(temporary) / "logs"),
                    "--require-tool",
                    "Edit",
                ],
                input="Edit a file.",
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn(
                "required tools are not in the selected mode inventory", completed.stderr
            )

    def test_implement_mode_allows_edits_and_exact_exec(self) -> None:
        completed = self.run_case(
            [
                {
                    "type": "system",
                    "subtype": "init",
                    "session_id": "session-implement",
                    "model": "claude-fable-5",
                    "tools": ["Read", "Edit", "Write", "Bash"],
                    "mcp_servers": [],
                },
                {
                    "type": "assistant",
                    "message": {
                        "model": "claude-fable-5",
                        "content": [
                            {
                                "type": "tool_use",
                                "name": "Edit",
                                "input": {"file_path": "/tmp/project/example.py"},
                            },
                            {
                                "type": "tool_use",
                                "name": "Bash",
                                "input": {"command": "python3 -m unittest -v"},
                            },
                        ],
                    },
                },
                {
                    "type": "result",
                    "subtype": "success",
                    "is_error": False,
                    "session_id": "session-implement",
                    "stop_reason": "end_turn",
                    "terminal_reason": "completed",
                    "permission_denials": [],
                    "result": "Implemented and verified",
                },
            ],
            0,
            [
                "--mode",
                "implement",
                "--allow-exec",
                "python3 -m unittest -v",
                "--require-tool",
                "Edit",
            ],
        )
        self.assertEqual(completed.stdout.strip(), "Implemented and verified")
        self.assertIn("mode=implement", completed.stderr)
        self.assertIn("audit=", completed.stderr)

    def test_rejects_exec_permission_outside_implement_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--cwd",
                    temporary,
                    "--mode",
                    "advise",
                    "--log-dir",
                    str(Path(temporary) / "logs"),
                    "--allow-exec",
                    "python3 -m unittest -v",
                ],
                input="Run tests.",
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn("--allow-exec requires --mode implement", completed.stderr)

    def test_rejects_bash_permission_bypass_in_implement_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--cwd",
                    temporary,
                    "--mode",
                    "implement",
                    "--log-dir",
                    str(Path(temporary) / "logs"),
                    "--allow-tool",
                    "Bash(python3 -m unittest -v)",
                ],
                input="Run tests.",
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn("use --allow-exec", completed.stderr)

    def test_rejects_destructive_or_chained_exec_permissions(self) -> None:
        for command in (
            "rm example.py",
            "git commit -m test",
            "pytest && git status",
            "bash -c pytest",
            "python3 -c print(1)",
            "curl https://example.com",
            "sudo make install",
        ):
            with self.subTest(command=command), tempfile.TemporaryDirectory() as temporary:
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(SCRIPT),
                        "--cwd",
                        temporary,
                        "--mode",
                        "implement",
                        "--log-dir",
                        str(Path(temporary) / "logs"),
                        "--allow-exec",
                        command,
                    ],
                    input="Run the command.",
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(completed.returncode, 1, completed.stderr)
                self.assertTrue(
                    "not allowed" in completed.stderr or "unsafe" in completed.stderr
                )

    def test_implement_mode_refuses_dirty_git_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
            (root / "existing.txt").write_text("user change\n", encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--cwd",
                    str(root),
                    "--mode",
                    "implement",
                    "--log-dir",
                    str(root / "logs"),
                ],
                input="Change the file.",
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn("refuses a dirty worktree", completed.stderr)

    def test_timeout_stops_the_fable_process(self) -> None:
        completed = self.run_case(
            [],
            124,
            ["--mode", "implement", "--timeout-minutes", "0.01"],
            fake_delay=5,
        )
        self.assertEqual(completed.stdout, "")
        self.assertIn("status=timed_out", completed.stderr)

    def test_sigterm_stops_and_reaps_the_fable_process(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake = root / "fake-claude"
            ready = root / "ready"
            fake.write_text(
                "#!/usr/bin/env python3\n"
                "import os, sys, time\n"
                "open(os.environ['READY_FILE'], 'w').write(str(os.getpid()))\n"
                "sys.stdin.read()\n"
                "time.sleep(30)\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            env = os.environ.copy()
            env.update(FABLE_CLAUDE_BIN=str(fake), READY_FILE=str(ready))
            process = subprocess.Popen(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--cwd",
                    str(root),
                    "--mode",
                    "implement",
                    "--log-dir",
                    str(root / "logs"),
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )
            assert process.stdin is not None
            process.stdin.write("Implement the bounded task.")
            process.stdin.close()
            deadline = time.monotonic() + 3
            while not ready.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(ready.exists(), "fake Fable process did not start")
            child_pid = int(ready.read_text(encoding="utf-8"))
            process.terminate()
            self.assertEqual(process.wait(timeout=7), 130)
            assert process.stdout is not None
            process.stdout.read()
            process.stdout.close()
            assert process.stderr is not None
            stderr = process.stderr.read()
            process.stderr.close()
            self.assertIn("status=interrupted", stderr)
            with self.assertRaises(ProcessLookupError):
                os.kill(child_pid, 0)

    def test_rejects_unsafe_project_permission_rule_before_launch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            settings_dir = root / ".claude"
            settings_dir.mkdir()
            (settings_dir / "settings.json").write_text(
                json.dumps({"permissions": {"allow": ["Edit"]}}),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--cwd",
                    str(root),
                    "--mode",
                    "advise",
                    "--log-dir",
                    str(root / "logs"),
                ],
                input="Review this read-only change.",
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn("unsafe Claude permission environment", completed.stderr)


if __name__ == "__main__":
    unittest.main()
