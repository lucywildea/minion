"""Tests for the Minion Hermes web search provider."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class _WebSearchProvider:
    pass


agent_package = types.ModuleType("agent")
provider_module = types.ModuleType("agent.web_search_provider")
setattr(provider_module, "WebSearchProvider", _WebSearchProvider)
sys.modules.setdefault("agent", agent_package)
sys.modules.setdefault("agent.web_search_provider", provider_module)

PROVIDER_PATH = Path(__file__).parents[1] / "provider.py"
SPEC = importlib.util.spec_from_file_location("minion_hermes_provider", PROVIDER_PATH)
assert SPEC and SPEC.loader
provider = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(provider)


class MinionWebSearchProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.search = provider.MinionWebSearchProvider()

    @patch.object(provider.shutil, "which", return_value="/usr/local/bin/minion")
    @patch.object(provider.subprocess, "run")
    def test_search_normalizes_yaml_and_uses_argument_list(self, run, _which) -> None:
        run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=(
                "url: https://example.com/one\n"
                "text: First result text.\n"
                "timestamp: now\n"
                "---\n"
                "title: Second page\n"
                "url: https://example.org/two\n"
                "summary: Second result.\n"
                "timestamp: now\n"
            ),
            stderr="",
        )

        result = self.search.search('robots "private"', limit=2)

        self.assertTrue(result["success"])
        self.assertEqual(
            result["data"]["web"],
            [
                {
                    "title": "example.com",
                    "url": "https://example.com/one",
                    "description": "First result text.",
                    "position": 1,
                },
                {
                    "title": "Second page",
                    "url": "https://example.org/two",
                    "description": "Second result.",
                    "position": 2,
                },
            ],
        )
        command = run.call_args.args[0]
        self.assertEqual(command[0], "/usr/local/bin/minion")
        self.assertIn('from.search=robots "private"', command)
        self.assertNotIsInstance(command, str)

    @patch.object(provider.shutil, "which", return_value="/usr/local/bin/minion")
    @patch.object(provider.subprocess, "run")
    def test_partial_results_survive_nonzero_exit(self, run, _which) -> None:
        run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="url: https://example.com\ntext: useful result\ntimestamp: now\n",
            stderr="one source failed",
        )

        result = self.search.search("query", limit=5)

        self.assertTrue(result["success"])
        self.assertEqual(len(result["data"]["web"]), 1)

    @patch.object(provider.shutil, "which", return_value=None)
    def test_missing_binary_is_reported(self, _which) -> None:
        result = self.search.search("query")
        self.assertFalse(result["success"])
        self.assertIn("not installed", result["error"])

    @patch.object(provider.shutil, "which", return_value="/usr/local/bin/minion")
    @patch.object(provider.subprocess, "run", side_effect=subprocess.TimeoutExpired("minion", 180))
    def test_timeout_is_reported(self, _run, _which) -> None:
        result = self.search.search("query")
        self.assertFalse(result["success"])
        self.assertIn("timed out", result["error"])

    def test_subprocess_environment_does_not_forward_unrelated_values(self) -> None:
        with patch.dict(
            os.environ,
            {"HOME": "/test-home", "PATH": "/bin", "PRIVATE_TOKEN": "secret"},
            clear=True,
        ):
            environment = provider._subprocess_environment()

        self.assertEqual(environment, {"HOME": "/test-home", "PATH": "/bin"})
        self.assertNotIn("PRIVATE_TOKEN", environment)


if __name__ == "__main__":
    unittest.main()
