import os
import unittest
from datetime import datetime, timezone
from io import StringIO
from unittest.mock import MagicMock, mock_open, patch

import requests
import yaml

import scripts.grooming_runner as gr


class TestGroomingRunnerHelpers(unittest.TestCase):
    def setUp(self):
        self.rules_path = "copilot_grooming_rules.yml"

    def test_load_rules(self):
        rules = gr.load_rules(self.rules_path)
        self.assertIsInstance(rules, dict)

    def test_grooming_rules_have_needs_work_assignee(self):
        # Ensure the repository grooming rules explicitly set the
        # assignee for needs_work so automation assigns to @copilot
        rules = gr.load_rules(self.rules_path)
        grooming = rules.get("grooming_bot_settings", {})
        self.assertIn("assignee_for_needs_work", grooming)
        self.assertEqual(grooming.get("assignee_for_needs_work"), "copilot")

    def test_load_rules_not_found(self):
        rules = gr.load_rules("nonexistent.yml")
        self.assertIsNone(rules)

    @patch("yaml.safe_load")
    def test_load_rules_invalid_yaml(self, mock_yaml):
        mock_yaml.side_effect = yaml.YAMLError("invalid")
        with self.assertRaises(yaml.YAMLError):
            gr.load_rules(self.rules_path)

    @patch("scripts.grooming_runner.requests.get")
    def test_github_search_issues(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "items": [{"number": 1}],
            "total_count": 1,
        }
        mock_resp.headers = {"X-RateLimit-Remaining": "10"}
        mock_get.return_value = mock_resp

        result = gr.github_search_issues("owner", "repo", "token")
        self.assertEqual(result, [{"number": 1}])
        mock_get.assert_called_once()

    @patch("scripts.grooming_runner.requests.get")
    @patch("scripts.grooming_runner.time.sleep")
    def test_github_search_issues_retry(self, mock_sleep, mock_get):
        mock_resp_fail = MagicMock()
        mock_resp_fail.raise_for_status.side_effect = requests.ConnectionError(
            "fail"
        )
        mock_resp_success = MagicMock()
        mock_resp_success.raise_for_status.return_value = None
        mock_resp_success.json.return_value = {"items": [{"number": 1}]}
        mock_resp_success.headers = {"X-RateLimit-Remaining": "10"}
        mock_get.side_effect = [mock_resp_fail, mock_resp_success]

        result = gr.github_search_issues("owner", "repo", "token")
        self.assertEqual(result, [{"number": 1}])
        self.assertEqual(mock_get.call_count, 2)
        mock_sleep.assert_called_once()

    @patch("scripts.grooming_runner.requests.get")
    def test_github_get_issue(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"number": 1}
        mock_resp.headers = {"X-RateLimit-Remaining": "10"}
        mock_get.return_value = mock_resp

        result = gr.github_get_issue("owner", "repo", 1, "token")
        self.assertEqual(result, {"number": 1})

    @patch("scripts.grooming_runner.requests.get")
    def test_github_get_issue_404(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.headers = {"X-RateLimit-Remaining": "10"}
        mock_get.return_value = mock_resp

        result = gr.github_get_issue("owner", "repo", 1, "token")
        self.assertIsNone(result)

    @patch("scripts.grooming_runner.requests.patch")
    def test_close_issue(self, mock_patch):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.headers = {"X-RateLimit-Remaining": "10"}
        mock_patch.return_value = mock_resp

        gr.close_issue("owner", "repo", 1, "token")
        mock_patch.assert_called_once()

    @patch("scripts.grooming_runner.requests.post")
    def test_post_comment(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.headers = {"X-RateLimit-Remaining": "10"}
        mock_post.return_value = mock_resp

        gr.post_comment("owner", "repo", 1, "comment", "token")
        mock_post.assert_called_once()

    def test_validate_github_token(self):
        self.assertTrue(gr.validate_github_token("gh_1234567890abcdef"))
        self.assertTrue(gr.validate_github_token("github_1234567890abcdef"))
        self.assertTrue(gr.validate_github_token("a" * 40))  # Classic token
        self.assertFalse(gr.validate_github_token("invalid"))
        self.assertFalse(gr.validate_github_token(None))
        self.assertFalse(gr.validate_github_token(""))

    def test_sanitize_log_entry(self):
        entry = {"notes": "My email is user@example.com", "other": "safe"}
        sanitized = gr.sanitize_log_entry(entry)
        self.assertEqual(sanitized["notes"], "[REDACTED: Potential PII]")
        self.assertEqual(sanitized["other"], "safe")

        safe_entry = {"notes": "This is safe", "other": "also safe"}
        sanitized_safe = gr.sanitize_log_entry(safe_entry)
        self.assertEqual(sanitized_safe, safe_entry)

        no_notes_entry = {"other": "safe"}
        sanitized_no_notes = gr.sanitize_log_entry(no_notes_entry)
        self.assertEqual(sanitized_no_notes, no_notes_entry)

    @patch("scripts.grooming_runner.requests.get")
    def test_get_project_columns(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = [{"id": 1}]
        mock_resp.headers = {"X-RateLimit-Remaining": "10"}
        mock_get.return_value = mock_resp

        result = gr.get_project_columns("owner", "repo", 1, "token")
        self.assertEqual(result, [{"id": 1}])

    @patch("scripts.grooming_runner.requests.get")
    def test_get_column_cards(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = [{"id": 1}]
        mock_resp.headers = {"X-RateLimit-Remaining": "10"}
        mock_get.return_value = mock_resp

        result = gr.get_column_cards(1, "token")
        self.assertEqual(result, [{"id": 1}])

    def test_find_card_for_issue(self):
        cards = [{"content_url": "url1"}, {"content_url": "url2"}]
        result = gr.find_card_for_issue(cards, "url1")
        self.assertEqual(result, {"content_url": "url1"})

        result = gr.find_card_for_issue(cards, "url3")
        self.assertIsNone(result)

    @patch("scripts.grooming_runner.requests.post")
    def test_move_card(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.headers = {"X-RateLimit-Remaining": "10"}
        mock_post.return_value = mock_resp

        gr.move_card(1, 2, "token")
        mock_post.assert_called_once()

    @patch("scripts.grooming_runner.get_project_columns")
    @patch("scripts.grooming_runner.get_column_cards")
    @patch("scripts.grooming_runner.find_card_for_issue")
    @patch("scripts.grooming_runner.move_card")
    def test_move_issue_to_column(
        self, mock_move, mock_find, mock_cards, mock_columns
    ):
        mock_columns.return_value = [{"id": 1}]
        mock_cards.return_value = [{"id": 1}]
        mock_find.return_value = {"id": 1}

        gr.move_issue_to_column("owner", "repo", 1, "url", 1, 2, "token")
        mock_move.assert_called_once_with(1, 2, "token")

    @patch("scripts.grooming_runner.get_project_columns")
    @patch("scripts.grooming_runner.get_column_cards")
    @patch("scripts.grooming_runner.find_card_for_issue")
    def test_move_issue_to_column_no_card(
        self, mock_find, mock_cards, mock_columns
    ):
        mock_columns.return_value = [{"id": 1}]
        mock_cards.return_value = []
        mock_find.return_value = None

        gr.move_issue_to_column("owner", "repo", 1, "url", 1, 2, "token")
        # Should not call move_card

    @patch.dict(
        os.environ,
        {
            "GITHUB_REPOSITORY": "owner/repo",
            "GITHUB_TOKEN": "gh_1234567890abcdef",
        },
    )
    @patch("scripts.grooming_runner.load_rules")
    @patch("scripts.grooming_runner.github_search_issues")
    def test_main_dry_run_no_token(self, mock_search, mock_load):
        mock_load.return_value = {
            "project_management": {"enabled": False},
            "grooming_bot_settings": {},
        }
        mock_search.return_value = []

        with patch.dict(os.environ, {"GITHUB_TOKEN": ""}):
            result = gr.main()
            self.assertEqual(result, 0)

    @patch.dict(os.environ, {})
    @patch("scripts.grooming_runner.load_rules")
    def test_main_no_repo(self, mock_load):
        mock_load.return_value = {
            "project_management": {},
            "grooming_bot_settings": {},
        }
        result = gr.main()
        self.assertEqual(result, 0)

    @patch.dict(os.environ, {"GITHUB_REPOSITORY": "owner/repo"})
    @patch("scripts.grooming_runner.load_rules")
    def test_main_triage_rules_none(self, mock_load):
        mock_load.side_effect = [None, {"grooming_bot_settings": {}}]
        result = gr.main()
        self.assertEqual(result, 1)

    @patch.dict(os.environ, {"GITHUB_REPOSITORY": "owner/repo"})
    @patch("scripts.grooming_runner.load_rules")
    def test_main_grooming_rules_none(self, mock_load):
        mock_load.side_effect = [{"project_management": {}}, None]
        result = gr.main()
        self.assertEqual(result, 1)

    @patch.dict(
        os.environ, {"GITHUB_REPOSITORY": "owner/repo", "GITHUB_TOKEN": ""}
    )
    @patch("scripts.grooming_runner.load_rules")
    @patch("scripts.grooming_runner.github_search_issues")
    def test_main_no_token(self, mock_search, mock_load):
        mock_load.return_value = {
            "project_management": {},
            "grooming_bot_settings": {},
        }
        mock_search.return_value = []
        result = gr.main()
        self.assertEqual(result, 0)

    @patch.dict(
        os.environ,
        {
            "GITHUB_REPOSITORY": "owner/repo",
            "GITHUB_TOKEN": "gh_1234567890abcdef",
            "DRY_RUN": "true",
        },
    )
    @patch("scripts.grooming_runner.load_rules")
    @patch("scripts.grooming_runner.github_search_issues")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_main_dry_run_with_issues(
        self, mock_json_dump, mock_open_file, mock_search, mock_load
    ):
        mock_load.side_effect = [
            {
                "project_management": {
                    "enabled": True,
                    "project_id": 1,
                    "columns": {"Backlog": 2},
                }
            },
            {"grooming_bot_settings": {"needs_info_variants": ["needs-info"]}},
        ]
        mock_search.return_value = [
            {
                "number": 1,
                "title": "Test",
                "labels": [{"name": "needs-info"}],
                "url": "url1",
            }
        ]
        result = gr.main()
        self.assertEqual(result, 0)
        mock_json_dump.assert_called()

    @patch.dict(
        os.environ,
        {
            "GITHUB_REPOSITORY": "owner/repo",
            "GITHUB_TOKEN": "gh_1234567890abcdef",
        },
    )
    @patch("scripts.grooming_runner.load_rules")
    @patch("scripts.grooming_runner.github_search_issues")
    @patch("scripts.grooming_runner.assign_issue")
    @patch("scripts.grooming_runner.remove_label")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_main_assign_exception(
        self,
        mock_json_dump,
        mock_open_file,
        mock_remove,
        mock_assign,
        mock_search,
        mock_load,
    ):
        mock_load.side_effect = [
            {"project_management": {}},
            {"grooming_bot_settings": {"needs_info_variants": ["needs-info"]}},
        ]
        mock_search.return_value = [
            {
                "number": 1,
                "title": "Test",
                "labels": [{"name": "needs-info"}],
                "url": "url1",
            }
        ]
        mock_assign.side_effect = Exception("error")
        result = gr.main()
        self.assertEqual(result, 0)

    @patch.dict(
        os.environ,
        {
            "GITHUB_REPOSITORY": "owner/repo",
            "GITHUB_TOKEN": "gh_1234567890abcdef",
        },
    )
    @patch("scripts.grooming_runner.load_rules")
    @patch("scripts.grooming_runner.github_search_issues")
    @patch("scripts.grooming_runner.move_issue_to_column")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_main_move_exception(
        self, mock_json_dump, mock_open_file, mock_move, mock_search, mock_load
    ):
        mock_load.side_effect = [
            {
                "project_management": {
                    "enabled": True,
                    "project_id": 1,
                    "columns": {"Backlog": 2},
                }
            },
            {"grooming_bot_settings": {}},
        ]
        mock_search.return_value = [
            {
                "number": 1,
                "title": "Test",
                "labels": [{"name": "Triaged"}, {"name": "Backlog"}],
                "url": "url1",
            }
        ]
        mock_move.side_effect = Exception("error")
        result = gr.main()
        self.assertEqual(result, 0)

    @patch.dict(
        os.environ,
        {"GITHUB_REPOSITORY": "owner/repo", "GITHUB_TOKEN": "invalid"},
    )
    @patch("scripts.grooming_runner.load_rules")
    def test_main_invalid_token(self, mock_load):
        mock_load.return_value = {
            "project_management": {},
            "grooming_bot_settings": {},
        }
        result = gr.main()
        self.assertEqual(result, 1)

    @patch("scripts.grooming_runner.close_issue")
    @patch("scripts.grooming_runner.post_comment")
    @patch("scripts.grooming_runner.remove_label")
    @patch("scripts.grooming_runner.assign_issue")
    @patch("scripts.grooming_runner.datetime")
    def test_process_issue_stale_close(
        self, mock_datetime, mock_assign, mock_remove, mock_post, mock_close
    ):
        mock_datetime.now.return_value = datetime(
            2025, 11, 25, tzinfo=timezone.utc
        )
        mock_datetime.fromisoformat.return_value = datetime(
            2025, 11, 10, tzinfo=timezone.utc
        )  # 15 days ago

        issue = {
            "number": 1,
            "title": "Stale Issue",
            "labels": [{"name": "needs-info"}],
            "url": "url1",
            "updated_at": "2025-11-10T00:00:00Z",
        }

        result = gr.process_issue(
            issue,
            owner="owner",
            repo="repo",
            gh_token="token",
            dry_run=False,
            needs_info_variants=["needs-info"],
            assignee_for_needs_info="bot",
            remove_triaged_on_needs_info=True,
            assignee_for_needs_work="copilot",
            project_enabled=True,
            project_id=1,
            backlog_column_id=2,
            move_to_backlog_if_triaged_and_backlog=True,
            stale_enabled=True,
            stale_labels=["needs-info"],
            stale_days=14,
            stale_action="close",
            stale_comment="Close comment",
            audit_event_type="grooming",
            workflow_enabled=False,
            transitions=[],
            project_columns={},
        )

        mock_assign.assert_called_once_with("owner", "repo", 1, "bot", "token")
        mock_post.assert_called_once()
        mock_close.assert_called_once()
        self.assertIn("closed as stale", result["changed_fields"])

    @patch("scripts.grooming_runner.post_comment")
    @patch("scripts.grooming_runner.assign_issue")
    @patch("scripts.grooming_runner.datetime")
    def test_process_issue_stale_comment(
        self, mock_datetime, mock_assign, mock_post
    ):
        mock_datetime.now.return_value = datetime(
            2025, 11, 25, tzinfo=timezone.utc
        )
        mock_datetime.fromisoformat.return_value = datetime(
            2025, 11, 10, tzinfo=timezone.utc
        )

        issue = {
            "number": 1,
            "title": "Stale Issue",
            "labels": [{"name": "needs-info"}],
            "url": "url1",
            "updated_at": "2025-11-10T00:00:00Z",
        }

        result = gr.process_issue(
            issue,
            owner="owner",
            repo="repo",
            gh_token="token",
            dry_run=False,
            needs_info_variants=["needs-info"],
            assignee_for_needs_info="bot",
            remove_triaged_on_needs_info=True,
            assignee_for_needs_work="copilot",
            project_enabled=True,
            project_id=1,
            backlog_column_id=2,
            move_to_backlog_if_triaged_and_backlog=True,
            stale_enabled=True,
            stale_labels=["needs-info"],
            stale_days=14,
            stale_action="comment",
            stale_comment="Comment",
            audit_event_type="grooming",
            workflow_enabled=False,
            transitions=[],
            project_columns={},
        )

        mock_assign.assert_called_once_with("owner", "repo", 1, "bot", "token")
        mock_post.assert_called_once()
        self.assertIn("commented as stale", result["changed_fields"])

    @patch("scripts.grooming_runner.remove_label")
    @patch("scripts.grooming_runner.assign_issue")
    @patch("scripts.grooming_runner.datetime")
    def test_process_issue_not_stale(
        self, mock_datetime, mock_assign, mock_remove
    ):
        mock_datetime.now.return_value = datetime(
            2025, 11, 25, tzinfo=timezone.utc
        )
        mock_datetime.fromisoformat.return_value = datetime(
            2025, 11, 20, tzinfo=timezone.utc
        )  # Recent

        issue = {
            "number": 1,
            "title": "Recent Issue",
            "labels": [{"name": "needs-info"}, {"name": "Triaged"}],
            "url": "url1",
            "updated_at": "2025-11-20T00:00:00Z",
        }

        result = gr.process_issue(
            issue,
            owner="owner",
            repo="repo",
            gh_token="token",
            dry_run=False,
            needs_info_variants=["needs-info"],
            assignee_for_needs_info="bot",
            remove_triaged_on_needs_info=True,
            assignee_for_needs_work="copilot",
            project_enabled=True,
            project_id=1,
            backlog_column_id=2,
            move_to_backlog_if_triaged_and_backlog=True,
            stale_enabled=True,
            stale_labels=["needs-info"],
            stale_days=14,
            stale_action="close",
            stale_comment="Close",
            audit_event_type="grooming",
            workflow_enabled=False,
            transitions=[],
            project_columns={},
        )

        mock_assign.assert_called_once_with("owner", "repo", 1, "bot", "token")
        mock_remove.assert_called_once_with(
            "owner", "repo", 1, "Triaged", "token"
        )
        self.assertIn("assigned to bot", result["changed_fields"])
        self.assertIn("removed Triaged", result["changed_fields"])
        self.assertNotIn("closed as stale", result["changed_fields"])
        self.assertNotIn("commented as stale", result["changed_fields"])

    @patch.dict(
        os.environ,
        {
            "GITHUB_REPOSITORY": "owner/repo",
            "GITHUB_TOKEN": "gh_1234567890abcdef",
        },
    )
    @patch("scripts.grooming_runner.load_rules")
    @patch("scripts.grooming_runner.github_search_issues")
    @patch("scripts.grooming_runner.close_issue")
    @patch("scripts.grooming_runner.post_comment")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_main_with_stale_issue(
        self,
        mock_json_dump,
        mock_open_file,
        mock_post,
        mock_close,
        mock_search,
        mock_load,
    ):
        mock_load.side_effect = [
            {"project_management": {}},
            {
                "grooming_bot_settings": {
                    "stale_issue_handling": {
                        "enabled": True,
                        "labels_to_check": ["needs-info"],
                        "days_threshold": 14,
                        "action": "close",
                        "close_comment": "Stale",
                    }
                }
            },
        ]
        mock_search.return_value = [
            {
                "number": 1,
                "title": "Stale",
                "labels": [{"name": "needs-info"}],
                "url": "url1",
                "updated_at": "2025-11-01T00:00:00Z",  # Old
            }
        ]
        result = gr.main()
        self.assertEqual(result, 0)
        mock_post.assert_called_once()
        mock_close.assert_called_once()


class TestAdditionalCoverage(unittest.TestCase):
    @patch("scripts.grooming_runner.requests.patch")
    def test_assign_issue(self, mock_patch):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.headers = {"X-RateLimit-Remaining": "10"}
        mock_patch.return_value = mock_resp

        gr.assign_issue("owner", "repo", 1, "assignee", "token")
        mock_patch.assert_called_once_with(
            "https://api.github.com/repos/owner/repo/issues/1",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer token",
            },
            json={"assignees": ["assignee"]},
        )

    @patch("scripts.grooming_runner.requests.patch")
    @patch("scripts.grooming_runner.requests.post")
    def test_assign_issue_graphql_fallback(self, mock_post, mock_patch):
        # Simulate REST patch failing with 422, then GraphQL calls succeed
        resp_patch = MagicMock()
        resp_patch.raise_for_status.side_effect = requests.HTTPError("422")
        resp_patch.status_code = 422
        resp_patch.headers = {"X-RateLimit-Remaining": "10"}
        mock_patch.return_value = resp_patch

        # GraphQL suggestedActors result
        resp_gql1 = MagicMock()
        resp_gql1.raise_for_status.return_value = None
        resp_gql1.json.return_value = {
            "data": {
                "repository": {
                    "suggestedActors": {
                        "nodes": [
                            {
                                "login": "copilot-swe-agent",
                                "id": "BOT_ID",
                                "__typename": "Bot",
                            }
                        ]
                    }
                }
            }
        }

        # GraphQL issue id response
        resp_gql2 = MagicMock()
        resp_gql2.raise_for_status.return_value = None
        resp_gql2.json.return_value = {
            "data": {"repository": {"issue": {"id": "ISSUE_ID"}}}
        }

        # GraphQL mutation response
        resp_gql3 = MagicMock()
        resp_gql3.raise_for_status.return_value = None
        resp_gql3.json.return_value = {
            "data": {"replaceActorsForAssignable": {}}
        }

        mock_post.side_effect = [resp_gql1, resp_gql2, resp_gql3]

        # Should not raise; fallback path assigns via GraphQL
        gr.assign_issue("owner", "repo", 1, "copilot", "token")
        self.assertGreaterEqual(mock_post.call_count, 2)

    @patch("scripts.grooming_runner.requests.patch")
    def test_assign_issue_graphql_fallback_missing_actor(self, mock_patch):
        # REST returns 422 and GraphQL has no matching actor
        resp_patch = MagicMock()
        resp_patch.raise_for_status.side_effect = requests.HTTPError("422")
        resp_patch.status_code = 422
        mock_patch.return_value = resp_patch

        with patch(
            "scripts.grooming_runner.github_graphql_request"
        ) as mock_gql:
            mock_gql.return_value = {
                "repository": {"suggestedActors": {"nodes": []}}
            }
            with self.assertRaises(RuntimeError):
                gr.assign_issue("owner", "repo", 1, "copilot", "token")

    @patch.dict(
        os.environ,
        {"GITHUB_ACTIONS": "true", "GITHUB_TOKEN": "gh_actions_token"},
    )
    @patch("scripts.grooming_runner.requests.patch")
    def test_assign_issue_in_actions_skips_graphql(self, mock_patch):
        # Simulate REST returning 422; when running in Actions with the
        # default GITHUB_TOKEN we should skip GraphQL fallback and not raise.
        resp_patch = MagicMock()
        resp_patch.raise_for_status.side_effect = requests.HTTPError("422")
        resp_patch.status_code = 422
        mock_patch.return_value = resp_patch

        # Use the same token value as the environment to emulate the
        # Actions runtime token behavior
        token = "gh_actions_token"

        # Ensure this doesn't raise
        gr.assign_issue("owner", "repo", 1, "copilot", token)

    @patch("time.sleep")
    @patch("sys.stderr", new_callable=StringIO)
    @patch("scripts.grooming_runner.requests.patch")
    def test_assign_issue_low_rate_limit(
        self, mock_patch, mock_stderr, mock_sleep
    ):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.headers = MagicMock()
        mock_resp.headers.get.return_value = "4"
        mock_patch.return_value = mock_resp

        gr.assign_issue("owner", "repo", 1, "assignee", "token")
        # Sleep is called to avoid hanging

    @patch("scripts.grooming_runner.requests.delete")
    def test_remove_label(self, mock_delete):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.headers = {"X-RateLimit-Remaining": "10"}
        mock_delete.return_value = mock_resp

        gr.remove_label("owner", "repo", 1, "label", "token")
        mock_delete.assert_called_once_with(
            "https://api.github.com/repos/owner/repo/issues/1/labels/label",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer token",
            },
        )

    @patch("scripts.grooming_runner.time.sleep")
    @patch("sys.stderr", new_callable=StringIO)
    @patch("scripts.grooming_runner.requests.delete")
    def test_remove_label_low_rate_limit(
        self, mock_delete, mock_stderr, mock_sleep
    ):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.headers = {"X-RateLimit-Remaining": "4"}
        mock_delete.return_value = mock_resp

        gr.remove_label("owner", "repo", 1, "label", "token")
        # Sleep is called to avoid hanging

    @patch("scripts.grooming_runner.assign_issue")
    @patch("scripts.grooming_runner.post_comment")
    def test_process_issue_needs_work_assigns(self, mock_post, mock_assign):
        issue = {
            "number": 2,
            "labels": [{"name": "needs_work"}, {"name": "in-review"}],
            "url": "url2",
        }

        gr.process_issue(
            issue,
            owner="owner",
            repo="repo",
            gh_token="token",
            dry_run=False,
            needs_info_variants=[],
            assignee_for_needs_info="",
            remove_triaged_on_needs_info=False,
            assignee_for_needs_work="copilot",
            project_enabled=False,
            project_id=0,
            backlog_column_id=0,
            move_to_backlog_if_triaged_and_backlog=False,
            stale_enabled=False,
            stale_labels=[],
            stale_days=0,
            stale_action="",
            stale_comment="",
            audit_event_type="grooming",
            workflow_enabled=False,
            transitions=[],
            project_columns={},
        )

        mock_assign.assert_called_once_with(
            "owner", "repo", 2, "copilot", "token"
        )
        mock_post.assert_called_once()

    def test_process_issue_needs_work_dry_run(self):
        issue = {
            "number": 3,
            "labels": [{"name": "needs_work"}],
            "url": "url3",
        }

        result = gr.process_issue(
            issue,
            owner="owner",
            repo="repo",
            gh_token="token",
            dry_run=True,
            needs_info_variants=[],
            assignee_for_needs_info="",
            remove_triaged_on_needs_info=False,
            assignee_for_needs_work="copilot",
            project_enabled=False,
            project_id=0,
            backlog_column_id=0,
            move_to_backlog_if_triaged_and_backlog=False,
            stale_enabled=False,
            stale_labels=[],
            stale_days=0,
            stale_action="",
            stale_comment="",
            audit_event_type="grooming",
            workflow_enabled=False,
            transitions=[],
            project_columns={},
        )

        # dry run should not actually call APIs; we check the changed_fields
        self.assertIn(
            "would assign to copilot and comment", result["changed_fields"]
        )

    @patch("scripts.grooming_runner.requests.get")
    def test_github_get_issue_with_token(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"number": 1}
        mock_resp.headers = {"X-RateLimit-Remaining": "10"}
        mock_get.return_value = mock_resp

        result = gr.github_get_issue("owner", "repo", 1, "token")
        self.assertEqual(result, {"number": 1})
        mock_get.assert_called_once_with(
            "https://api.github.com/repos/owner/repo/issues/1",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer token",
            },
        )

    @patch("scripts.grooming_runner.requests.get")
    def test_github_get_issue_without_token(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"number": 1}
        mock_resp.headers = {"X-RateLimit-Remaining": "10"}
        mock_get.return_value = mock_resp

        result = gr.github_get_issue("owner", "repo", 1, None)
        self.assertEqual(result, {"number": 1})
        mock_get.assert_called_once_with(
            "https://api.github.com/repos/owner/repo/issues/1",
            headers={"Accept": "application/vnd.github+json"},
        )

    @patch("scripts.grooming_runner.assign_issue")
    @patch("scripts.grooming_runner.remove_label")
    def test_process_issue_needs_info_exception(self, mock_remove, mock_assign):
        mock_assign.side_effect = Exception("fail")
        issue = {
            "number": 1,
            "labels": [{"name": "needs-info"}, {"name": "Triaged"}],
            "url": "url1",
            "updated_at": "2025-01-01T00:00:00Z",
        }
        with patch("scripts.grooming_runner.logger") as mock_logger:
            gr.process_issue(
                issue,
                owner="owner",
                repo="repo",
                gh_token="token",
                dry_run=False,
                needs_info_variants=["needs-info"],
                assignee_for_needs_info="bot",
                remove_triaged_on_needs_info=True,
                assignee_for_needs_work="copilot",
                project_enabled=False,
                project_id=0,
                backlog_column_id=0,
                move_to_backlog_if_triaged_and_backlog=False,
                stale_enabled=False,
                stale_labels=[],
                stale_days=0,
                stale_action="",
                stale_comment="",
                audit_event_type="grooming",
                workflow_enabled=False,
                transitions=[],
                project_columns={},
            )
            mock_assign.assert_called_once()
            mock_logger.error.assert_called_once()

    @patch("scripts.grooming_runner.post_comment")
    @patch("scripts.grooming_runner.close_issue")
    def test_process_issue_stale_close(self, mock_close, mock_post):
        issue = {
            "number": 1,
            "labels": [{"name": "needs-info"}],
            "url": "url1",
            "updated_at": "2025-11-01T00:00:00Z",  # Old
        }
        result = gr.process_issue(
            issue,
            "owner",
            "repo",
            "token",
            False,
            [],
            "",
            False,
            "",
            False,
            0,
            0,
            False,
            True,
            ["needs-info"],
            14,
            "close",
            "Stale",
            "grooming",
            False,
            [],
            {},
        )
        mock_post.assert_called_once()
        mock_close.assert_called_once()
        self.assertIn("closed as stale", result["changed_fields"])

    @patch("scripts.grooming_runner.post_comment")
    def test_process_issue_stale_comment(self, mock_post):
        issue = {
            "number": 1,
            "labels": [{"name": "needs-info"}],
            "url": "url1",
            "updated_at": "2025-11-01T00:00:00Z",  # Old
        }
        result = gr.process_issue(
            issue,
            "owner",
            "repo",
            "token",
            False,
            [],
            "",
            False,
            "",
            False,
            0,
            0,
            False,
            True,
            ["needs-info"],
            14,
            "comment",
            "Stale",
            "grooming",
            False,
            [],
            {},
        )
        mock_post.assert_called_once()
        self.assertIn("commented as stale", result["changed_fields"])

    @patch("scripts.grooming_runner.requests.get")
    def test_get_project_columns(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = [{"id": 1}]
        mock_resp.headers = {"X-RateLimit-Remaining": "10"}
        mock_get.return_value = mock_resp

        result = gr.get_project_columns("owner", "repo", 1, "token")
        self.assertEqual(result, [{"id": 1}])
        mock_get.assert_called_once()

    @patch("scripts.grooming_runner.requests.get")
    @patch("scripts.grooming_runner.time.sleep")
    def test_retry_on_failure_exhaust_retries(self, mock_sleep, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.ConnectionError(
            "fail"
        )
        mock_get.return_value = mock_resp

        with patch("scripts.grooming_runner.logger") as mock_logger:
            with self.assertRaises(requests.ConnectionError):
                gr.github_search_issues("owner", "repo", "token")
            mock_logger.error.assert_called_with("All 4 attempts failed.")

    @patch.dict(os.environ, {}, clear=True)
    @patch("scripts.grooming_runner.load_rules")
    def test_main_no_github_repo(self, mock_load):
        mock_load.return_value = {}
        result = gr.main()
        self.assertEqual(result, 0)

    @patch.dict(
        os.environ,
        {
            "GITHUB_REPOSITORY": "owner/repo",
            "GITHUB_TOKEN": "gh_1234567890abcdef",
        },
    )
    @patch("scripts.grooming_runner.load_rules")
    @patch("scripts.grooming_runner.github_search_issues")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_main_log_writing(
        self, mock_json_dump, mock_open_file, mock_search, mock_load
    ):
        mock_load.side_effect = [
            {"project_management": {}},
            {"grooming_bot_settings": {}},
        ]
        mock_search.return_value = [
            {
                "number": 1,
                "labels": [],
                "url": "url1",
                "updated_at": "2025-01-01T00:00:00Z",
            }
        ]
        with patch(
            "scripts.grooming_runner.sanitize_log_entry"
        ) as mock_sanitize:
            mock_sanitize.return_value = {"test": "entry"}
            result = gr.main()
            self.assertEqual(result, 0)
            mock_json_dump.assert_called_once()


if __name__ == "__main__":
    unittest.main()
