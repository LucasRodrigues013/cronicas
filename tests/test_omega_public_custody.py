"""OMEGA-006: synthetic public-path custody regressions; no archive material."""
import contextlib
import importlib
import io
import json
import re
import unittest
from pathlib import Path
from unittest.mock import patch


def guard():
    return importlib.import_module("worldroot.public_custody")


class PublicCustodyTests(unittest.TestCase):
    def test_legacy_filter_has_real_namespace_gap(self):
        # The old workflow regex would allow these synthetic JSON/Markdown paths.
        legacy = re.compile(r"(^|/)(private|runtime)/|\.(db|sqlite|sqlite-wal|sqlite-shm|zip|txt)$|\.env")
        samples = ["episodes/fixture/draft/story.md", "inbox/fixture.json",
                   "canon/HEAD.json", "production/fixture/segments/01.md"]
        self.assertTrue(all(not legacy.search(x) for x in samples))
        self.assertEqual(guard().scan_paths(samples)["blocked_count"], len(samples))

    def test_reserved_paths_and_sensitive_basenames(self):
        paths = ["requests/fixture.json", "preparations/fixture.json",
                 "choices/fixture.json", "receipts/fixture.json",
                 "nested/editorial/fixture.json", "nested/archive/fixture.md",
                 "nested/held_out/fixture.json", "nested/gold/fixture.json",
                 "docs/narrativa_integral.md", "docs/manifesto_imutavel.json",
                 "docs/engine_publishing_policy.json", "docs/fixture.SQLITE",
                 "docs/.env.example", "docs/fixture.TXT"]
        result = guard().scan_paths(paths)
        self.assertEqual(result["blocked_count"], len(paths))
        self.assertFalse(result["public_path_check_passed"])

    def test_disguised_paths(self):
        paths = ["EpIsOdEs/fixture.md", "ｅｐｉｓｏｄｅｓ/fixture.md",
                 "nested\\inbox\\fixture.json", "docs/fi\nxture.json",
                 "nested/../fixture.md", "/fixture.md"]
        self.assertEqual(guard().scan_paths(paths)["blocked_count"], len(paths))

    def test_current_public_code_names_remain_allowed(self):
        paths = [".github/workflows/tests.yml", "worldroot/editorial_policy.json",
                 "tests/test_omega_editorial_production.py", "docs/r35-longform-restoration.md",
                 "audit/omega-cycle-1-rule-trace.json", "recovery/README.md",
                 "README.md", "pyproject.toml"]
        self.assertTrue(guard().scan_paths(paths)["public_path_check_passed"])

    def test_cli_nul_delimited_and_aggregate_only(self):
        output = io.StringIO()
        with patch("subprocess.check_output", return_value=b"README.md\0inbox/fixture-hidden-name.json\0") as command, contextlib.redirect_stdout(output):
            status = guard().main()
        self.assertEqual(status, 1)
        command.assert_called_once_with(["git", "ls-files", "-z"])
        self.assertNotIn("fixture-hidden-name", output.getvalue())
        report = json.loads(output.getvalue())
        self.assertEqual(report["blocked_count"], 1)
        self.assertFalse(report["confidentiality_certified"])

    def test_empty_or_unterminated_index_fails_closed(self):
        for raw in (b"", b"README.md"):
            with self.subTest(raw=raw), patch("subprocess.check_output", return_value=raw), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(guard().main(), 1)

    def test_workflows_guard_before_regression_execution(self):
        root = Path(__file__).resolve().parents[1]
        for name in ("tests.yml", "worldroot-orchestrator.yml"):
            text = (root/".github/workflows"/name).read_text()
            self.assertIn("python -m worldroot.public_custody", text)
            self.assertLess(text.index("python -m worldroot.public_custody"),
                            text.index("python -", text.index("python -m worldroot.public_custody")+1))
            self.assertLess(text.index("python -m worldroot.public_custody"), text.index("unittest discover"))
