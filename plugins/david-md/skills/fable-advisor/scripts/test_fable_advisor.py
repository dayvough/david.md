#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("fable_advisor.py")


class FableAdvisorTests(unittest.TestCase):
    def run_case(self, events: list[dict], expected_code: int) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake = root / "fake-claude"
            fake.write_text(
                "#!/usr/bin/env python3\n"
                "import json, os, sys\n"
                "open(os.environ['CAPTURE_ARGS'], 'w').write(json.dumps(sys.argv[1:]))\n"
                "sys.stdin.read()\n"
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
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--cwd",
                    str(root),
                    "--log-dir",
                    str(root / "logs"),
                    "--profile",
                    "linear-read",
                ],
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
            self.assertNotIn("--max-turns", args)
            builtin_tools = args[args.index("--tools") + 1]
            self.assertIn("Read", builtin_tools)
            self.assertIn("Bash", builtin_tools)
            self.assertNotIn("Edit", builtin_tools)
            disallowed = args[args.index("--disallowedTools") + 1]
            self.assertIn("Edit", disallowed)
            self.assertIn("Write", disallowed)
            allowed = args[args.index("--allowedTools") + 1]
            self.assertIn("ToolSearch", allowed)
            self.assertIn("mcp__claude_ai_Linear__get_issue", allowed)
            self.assertNotIn("Bash(", allowed)
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
        self.assertIn("status=required_read_denied", completed.stderr)

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
