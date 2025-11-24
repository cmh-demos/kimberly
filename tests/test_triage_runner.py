import os
import tempfile
import json
import unittest

from scripts import triage_runner as tr


class TestTriageRunnerHelpers(unittest.TestCase):
    def setUp(self):
        self.rules_path = "copilot_triage_rules.yml"

    def test_load_rules(self):
        rules = tr.load_rules(self.rules_path)
        self.assertIsInstance(rules, dict)

    def test_detect_pii_builtin(self):
        s = "We found an api key!"
        self.assertTrue(tr.detect_pii(s))

    def test_detect_pii_negative(self):
        s = "No secrets here, just a description of a bug."
        self.assertFalse(tr.detect_pii(s))


class TestSmokeRunner(unittest.TestCase):
    def test_smoke_local_dry_run_no_repo(self):
        # When no GITHUB_REPOSITORY set, main exits gracefully (0)
        env = os.environ.copy()
        env.pop("GITHUB_REPOSITORY", None)
        rv = tr.main()
        self.assertEqual(rv, 0)


if __name__ == "__main__":
    unittest.main()
