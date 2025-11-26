import os
import time
import unittest
from unittest.mock import MagicMock, mock_open, patch

import yaml

from scripts import triage_runner as tr


class TestTriageRunnerHelpers(unittest.TestCase):
    def setUp(self):
        self.rules_path = "copilot_triage_rules.yml"

    def test_load_rules(self):
        rules = tr.load_rules(self.rules_path)
        self.assertIsInstance(rules, dict)

    def test_load_rules_not_found(self):
        rules = tr.load_rules("nonexistent.yml")
        self.assertIsNone(rules)

    def test_read_rules_version(self):
        version = tr.read_rules_version(self.rules_path)
        self.assertIsInstance(version, str)

    def test_read_rules_version_not_found(self):
        version = tr.read_rules_version("nonexistent.yml")
        self.assertIsNone(version)

    @patch("yaml.safe_load")
    def test_read_rules_version_invalid_data(self, mock_yaml):
        mock_yaml.return_value = "not a dict"
        version = tr.read_rules_version(self.rules_path)
        self.assertIsNone(version)

    @patch("scripts.triage_runner.load_rules")
    def test_read_rules_version_load_fails(self, mock_load):
        mock_load.side_effect = FileNotFoundError
        version = tr.read_rules_version(self.rules_path)
        self.assertIsNone(version)

    @patch("yaml.safe_load")
    def test_load_rules_invalid_yaml(self, mock_yaml):
        mock_yaml.side_effect = yaml.YAMLError("invalid")
        with self.assertRaises(yaml.YAMLError):
            tr.load_rules(self.rules_path)

    def test_detect_pii_builtin(self):
        s = "We found an apikey: secret123"
        self.assertTrue(tr.detect_pii(s))

    def test_detect_pii_negative(self):
        s = "No secrets here, just a description of a bug."
        self.assertFalse(tr.detect_pii(s))

    @patch("scripts.triage_runner.requests.get")
    def test_github_search_issues(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {"items": [{"number": 1}]}
        issues = tr.github_search_issues("owner", "repo", "token")
        self.assertEqual(len(issues), 1)
        mock_get.assert_called_once()

    @patch("scripts.triage_runner.requests.get")
    def test_github_get_issue(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {"number": 1}
        issue = tr.github_get_issue("owner", "repo", 1, "token")
        self.assertEqual(issue["number"], 1)

    @patch("scripts.triage_runner.requests.post")
    def test_post_label(self, mock_post):
        tr.post_label("owner", "repo", 1, "label", "token")
        mock_post.assert_called_once()

    @patch("scripts.triage_runner.requests.post")
    def test_post_comment(self, mock_post):
        tr.post_comment("owner", "repo", 1, "comment", "token")
        mock_post.assert_called_once()

    @patch("scripts.triage_runner.requests.get")
    def test_fetch_related_docs(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.ok = True
        mock_response.json.return_value = {"items": [{"html_url": "url"}]}
        docs = tr.fetch_related_docs("owner", "repo", "token", "body", "title")
        self.assertEqual(len(docs), 1)

    @patch("scripts.triage_runner.requests.post")
    def test_move_card(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.headers = {"X-RateLimit-Remaining": "10"}
        mock_post.return_value = mock_resp
        # Stub function, just check it doesn't error
        tr.move_card(1, 2, "token")
        mock_post.assert_called_once()

    @patch("scripts.triage_runner.requests.get")
    def test_github_search_issues_failure(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.raise_for_status.side_effect = Exception("API error")
        with self.assertRaises(Exception):
            tr.github_search_issues("owner", "repo", "token")

    @patch("scripts.triage_runner.requests.get")
    def test_github_get_issue_404(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404")
        issue = tr.github_get_issue("owner", "repo", 1, "token")
        self.assertIsNone(issue)

    @patch("scripts.triage_runner.requests.post")
    def test_post_label_failure(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.raise_for_status.side_effect = Exception("API error")
        with self.assertRaises(Exception):
            tr.post_label("owner", "repo", 1, "label", "token")

    @patch("scripts.triage_runner.requests.post")
    def test_post_comment_failure(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.raise_for_status.side_effect = Exception("API error")
        with self.assertRaises(Exception):
            tr.post_comment("owner", "repo", 1, "comment", "token")

    @patch("scripts.triage_runner.requests.get")
    def test_fetch_related_docs_failure(self, mock_get):
        mock_get.side_effect = Exception("API error")
        docs = tr.fetch_related_docs("owner", "repo", "token", "body", "title")
        self.assertEqual(docs, [])

    @patch("scripts.triage_runner.requests.patch")
    def test_assign_triage_owner_failure(self, mock_patch):
        mock_response = mock_patch.return_value
        mock_response.raise_for_status.side_effect = Exception("API error")
        with self.assertRaises(Exception):
            tr.assign_triage_owner("owner", "repo", 1, "assignee", "token")

    @patch("scripts.triage_runner.requests.get")
    @patch("scripts.triage_runner.time.sleep")
    def test_github_search_issues_rate_limit(self, mock_sleep, mock_get):
        # Simulate rate limit response then success
        mock_resp_rate = MagicMock()
        mock_resp_rate.raise_for_status.return_value = None
        mock_resp_rate.json.return_value = {"items": [{"number": 1}]}
        mock_resp_rate.headers = {
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(int(time.time()) + 2),
        }
        mock_resp_success = MagicMock()
        mock_resp_success.raise_for_status.return_value = None
        mock_resp_success.json.return_value = {"items": [{"number": 2}]}
        mock_resp_success.headers = {"X-RateLimit-Remaining": "10"}
        mock_get.side_effect = [mock_resp_rate, mock_resp_success]

        result = tr.github_search_issues("owner", "repo", "token")
        self.assertEqual(result, [{"number": 2}])
        self.assertEqual(mock_get.call_count, 2)
        mock_sleep.assert_called()
        sleep_args = mock_sleep.call_args[0][0]
        self.assertGreaterEqual(sleep_args, 60)


class TestSmokeRunner(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_smoke_local_dry_run_no_repo(self):
        # When no GITHUB_REPOSITORY set, main exits gracefully (0)
        rv = tr.main()
        self.assertEqual(rv, 0)

    @patch("scripts.triage_runner.load_rules")
    def test_main_version_invalid(self, mock_load):
        mock_load.side_effect = [
            {"triage_audit_schema": {"version": "1.0"}},
            "not dict",
        ]
        rv = tr.main()
        self.assertEqual(rv, 1)

    @patch("scripts.triage_runner.load_rules")
    def test_main_invalid_regex(self, mock_load):
        mock_load.return_value = {"pii_handling": {"detect_patterns": ["["]}}
        rv = tr.main()
        self.assertEqual(rv, 0)  # Should continue despite invalid regex

    @patch.dict(
        os.environ,
        {
            "GITHUB_REPOSITORY": "owner/repo",
            "GITHUB_TOKEN": "token",
            "GITHUB_REF": "refs/heads/feature",
        },
    )
    @patch("scripts.triage_runner.github_search_issues")
    @patch("builtins.open", new_callable=mock_open)
    @patch("scripts.triage_runner.json.dump")
    def test_main_dry_run_with_token(self, mock_dump, mock_file, mock_search):
        mock_search.return_value = [
            {"number": 1, "title": "Test", "body": "body", "labels": []}
        ]
        rv = tr.main()
        self.assertEqual(rv, 0)

    @patch.dict(
        os.environ,
        {
            "GITHUB_REPOSITORY": "owner/repo",
            "GITHUB_TOKEN": "token",
            "ISSUE_NUMBER": "1",
        },
    )
    @patch("scripts.triage_runner.github_get_issue")
    @patch("scripts.triage_runner.post_label")
    @patch("scripts.triage_runner.post_comment")
    @patch("scripts.triage_runner.assign_triage_owner")
    @patch("builtins.open", new_callable=mock_open)
    @patch("scripts.triage_runner.json.dump")
    def test_main_with_issue_number(
        self,
        mock_dump,
        mock_file,
        mock_assign,
        mock_comment,
        mock_label,
        mock_get_issue,
    ):
        mock_get_issue.return_value = {
            "number": 1,
            "title": "Test",
            "body": "body",
            "labels": [],
        }
        rv = tr.main()
        self.assertEqual(rv, 0)

    @patch.dict(
        os.environ,
        {
            "GITHUB_REPOSITORY": "owner/repo",
            "GITHUB_TOKEN": "token",
            "ISSUE_NUMBER": "1",
        },
    )
    @patch("scripts.triage_runner.github_get_issue")
    def test_main_issue_not_found(self, mock_get_issue):
        mock_get_issue.return_value = None
        rv = tr.main()
        self.assertEqual(rv, 0)

    @patch.dict(
        os.environ, {"GITHUB_REPOSITORY": "owner/repo", "GITHUB_TOKEN": "token"}
    )
    @patch("scripts.triage_runner.github_search_issues")
    def test_main_github_search_fails(self, mock_search):
        mock_search.side_effect = Exception("API error")
        rv = tr.main()
        self.assertEqual(rv, 1)

    @patch.dict(
        os.environ, {"GITHUB_REPOSITORY": "owner/repo", "GITHUB_TOKEN": "token"}
    )
    @patch("scripts.triage_runner.github_search_issues")
    def test_main_no_issues_found(self, mock_search):
        mock_search.return_value = []
        rv = tr.main()
        self.assertEqual(rv, 0)

    @patch.dict(
        os.environ, {"GITHUB_REPOSITORY": "owner/repo", "GITHUB_TOKEN": "token"}
    )
    @patch("scripts.triage_runner.github_search_issues")
    @patch("scripts.triage_runner.post_label")
    @patch("scripts.triage_runner.post_comment")
    @patch("scripts.triage_runner.assign_triage_owner")
    @patch("builtins.open", new_callable=mock_open)
    @patch("scripts.triage_runner.json.dump")
    def test_main_with_low_severity(
        self,
        mock_dump,
        mock_file,
        mock_assign,
        mock_comment,
        mock_label,
        mock_search,
    ):
        mock_search.return_value = [
            {"number": 1, "title": "minor bug", "body": "body", "labels": []}
        ]
        rv = tr.main()
        self.assertEqual(rv, 0)

    @patch.dict(
        os.environ, {"GITHUB_REPOSITORY": "owner/repo", "GITHUB_TOKEN": "token"}
    )
    @patch("scripts.triage_runner.github_search_issues")
    @patch("scripts.triage_runner.post_label")
    @patch("scripts.triage_runner.post_comment")
    @patch("scripts.triage_runner.assign_triage_owner")
    @patch("builtins.open", new_callable=mock_open)
    @patch("scripts.triage_runner.json.dump")
    def test_main_with_typo_severity(
        self,
        mock_dump,
        mock_file,
        mock_assign,
        mock_comment,
        mock_label,
        mock_search,
    ):
        mock_search.return_value = [
            {"number": 1, "title": "typo in code", "body": "body", "labels": []}
        ]
        rv = tr.main()
        self.assertEqual(rv, 0)

    @patch.dict(
        os.environ, {"GITHUB_REPOSITORY": "owner/repo", "GITHUB_TOKEN": "token"}
    )
    @patch("scripts.triage_runner.github_search_issues")
    @patch("scripts.triage_runner.post_label")
    @patch("scripts.triage_runner.post_comment")
    @patch("scripts.triage_runner.assign_triage_owner")
    @patch("builtins.open", new_callable=mock_open)
    @patch("scripts.triage_runner.json.dump")
    @patch("scripts.triage_runner.requests.patch")
    def test_main_with_title_sanitization(
        self,
        mock_patch,
        mock_dump,
        mock_file,
        mock_assign,
        mock_comment,
        mock_label,
        mock_search,
    ):
        mock_search.return_value = [
            {
                "number": 1,
                "title": "[High Priority] Test issue",
                "body": "body",
                "labels": [],
            }
        ]
        rv = tr.main()
        self.assertEqual(rv, 0)

    @patch.dict(
        os.environ, {"GITHUB_REPOSITORY": "owner/repo", "GITHUB_TOKEN": "token"}
    )
    @patch("scripts.triage_runner.github_search_issues")
    @patch("scripts.triage_runner.post_label")
    @patch("scripts.triage_runner.post_comment")
    @patch("scripts.triage_runner.assign_triage_owner")
    @patch("builtins.open", new_callable=mock_open)
    @patch("scripts.triage_runner.json.dump")
    def test_main_with_missing_fields(
        self,
        mock_dump,
        mock_file,
        mock_assign,
        mock_comment,
        mock_label,
        mock_search,
    ):
        mock_search.return_value = [
            {
                "number": 1,
                "title": "Test",
                "body": "description: test",
                "labels": [],
            }
        ]
        rv = tr.main()
        self.assertEqual(rv, 0)

    @patch.dict(
        os.environ, {"GITHUB_REPOSITORY": "owner/repo", "GITHUB_TOKEN": "token"}
    )
    @patch("scripts.triage_runner.github_search_issues")
    @patch("scripts.triage_runner.post_label")
    @patch("scripts.triage_runner.post_comment")
    @patch("scripts.triage_runner.assign_triage_owner")
    @patch("builtins.open", new_callable=mock_open)
    @patch("scripts.triage_runner.json.dump")
    def test_main_backlog_added(
        self,
        mock_dump,
        mock_file,
        mock_assign,
        mock_comment,
        mock_label,
        mock_search,
    ):
        body = (
            "summary: test\nrepro_steps: steps\nexpected_behavior: expected\n"
            "actual_behavior: actual\nsize_estimate: small"
        )
        mock_search.return_value = [
            {"number": 1, "title": "Test", "body": body, "labels": []}
        ]
        rv = tr.main()
        self.assertEqual(rv, 0)

    @patch.dict(
        os.environ, {"GITHUB_REPOSITORY": "owner/repo", "GITHUB_TOKEN": "token"}
    )
    @patch("scripts.triage_runner.github_search_issues")
    @patch("scripts.triage_runner.post_label")
    @patch("scripts.triage_runner.post_comment")
    @patch("scripts.triage_runner.assign_triage_owner")
    @patch("builtins.open", new_callable=mock_open)
    @patch("scripts.triage_runner.json.dump")
    def test_main_with_critical_issue(
        self,
        mock_dump,
        mock_file,
        mock_assign,
        mock_comment,
        mock_label,
        mock_search,
    ):
        mock_search.return_value = [
            {
                "number": 1,
                "title": "Data loss bug",
                "body": "body",
                "labels": [],
            }
        ]
        rv = tr.main()
        self.assertEqual(rv, 0)

    @patch.dict(
        os.environ, {"GITHUB_REPOSITORY": "owner/repo", "GITHUB_TOKEN": "token"}
    )
    @patch("scripts.triage_runner.github_search_issues")
    @patch("scripts.triage_runner.post_label")
    @patch("scripts.triage_runner.post_comment")
    @patch("scripts.triage_runner.assign_triage_owner")
    @patch("builtins.open", new_callable=mock_open)
    @patch("scripts.triage_runner.json.dump")
    @patch("scripts.triage_runner.requests.delete")
    def test_main_with_complete_triage(
        self,
        mock_delete,
        mock_dump,
        mock_file,
        mock_assign,
        mock_comment,
        mock_label,
        mock_search,
    ):
        body = (
            "summary: test\nrepro_steps: steps\nexpected_behavior: expected\n"
            "actual_behavior: actual\nsize_estimate: small"
        )
        mock_search.return_value = [
            {
                "number": 1,
                "title": "Test",
                "body": body,
                "labels": [{"name": "Needs Triage"}],
            }
        ]
        rv = tr.main()
        self.assertEqual(rv, 0)

    @patch.dict(
        os.environ, {"GITHUB_REPOSITORY": "owner/repo", "GITHUB_TOKEN": "token"}
    )
    @patch("scripts.triage_runner.github_search_issues")
    @patch("scripts.triage_runner.post_label")
    @patch("scripts.triage_runner.post_comment")
    @patch("scripts.triage_runner.assign_triage_owner")
    @patch("builtins.open", new_callable=mock_open)
    @patch("scripts.triage_runner.json.dump")
    @patch("scripts.triage_runner.requests.get")
    def test_main_with_pair_enforcement_add_backlog(
        self,
        mock_get,
        mock_dump,
        mock_file,
        mock_assign,
        mock_comment,
        mock_label,
        mock_search,
    ):
        mock_search.return_value = [
            {
                "number": 1,
                "title": "Test",
                "body": "body",
                "labels": [{"name": "Triaged"}],
            }
        ]
        # Mock label refresh
        mock_resp = mock_get.return_value
        mock_resp.ok = True
        mock_resp.json.return_value = {"labels": [{"name": "Triaged"}]}
        rv = tr.main()
        self.assertEqual(rv, 0)

    @patch.dict(
        os.environ, {"GITHUB_REPOSITORY": "owner/repo", "GITHUB_TOKEN": "token"}
    )
    @patch("scripts.triage_runner.github_search_issues")
    @patch("scripts.triage_runner.post_label")
    @patch("scripts.triage_runner.post_comment")
    @patch("scripts.triage_runner.assign_triage_owner")
    @patch("builtins.open", new_callable=mock_open)
    @patch("scripts.triage_runner.json.dump")
    @patch("scripts.triage_runner.requests.get")
    def test_main_with_backlog_gate_blocked(
        self,
        mock_get,
        mock_dump,
        mock_file,
        mock_assign,
        mock_comment,
        mock_label,
        mock_search,
    ):
        mock_search.return_value = [
            {
                "number": 1,
                "title": "Test",
                "body": "body",
                "labels": [{"name": "enhancement"}],
            }
        ]
        # Mock label refresh
        mock_resp = mock_get.return_value
        mock_resp.ok = True
        mock_resp.json.return_value = {"labels": [{"name": "enhancement"}]}
        rv = tr.main()
        self.assertEqual(rv, 0)

    @patch.dict(
        os.environ, {"GITHUB_REPOSITORY": "owner/repo", "GITHUB_TOKEN": "token"}
    )
    @patch("scripts.triage_runner.github_search_issues")
    @patch("scripts.triage_runner.post_label")
    @patch("scripts.triage_runner.post_comment")
    @patch("scripts.triage_runner.assign_triage_owner")
    @patch("builtins.open", new_callable=mock_open)
    @patch("scripts.triage_runner.json.dump")
    def test_main_live_action_failure(
        self,
        mock_dump,
        mock_file,
        mock_assign,
        mock_comment,
        mock_label,
        mock_search,
    ):
        mock_search.return_value = [
            {"number": 1, "title": "Test", "body": "body", "labels": []}
        ]
        mock_label.side_effect = Exception("API error")
        rv = tr.main()
        self.assertEqual(rv, 0)  # Should not crash, just log error


if __name__ == "__main__":
    unittest.main()
