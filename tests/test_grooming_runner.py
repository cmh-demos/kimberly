import os
import unittest
from unittest.mock import mock_open, patch, MagicMock
import json
import yaml

import scripts.grooming_runner as gr


class TestGroomingRunnerHelpers(unittest.TestCase):
    def setUp(self):
        self.rules_path = "copilot_grooming_rules.yml"

    def test_load_rules(self):
        rules = gr.load_rules(self.rules_path)
        self.assertIsInstance(rules, dict)

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
        mock_resp.json.return_value = {"items": [{"number": 1}]}
        mock_get.return_value = mock_resp

        result = gr.github_search_issues("owner", "repo", "token")
        self.assertEqual(result, [{"number": 1}])
        mock_get.assert_called_once()

    @patch("scripts.grooming_runner.requests.get")
    def test_github_get_issue(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"number": 1}
        mock_get.return_value = mock_resp

        result = gr.github_get_issue("owner", "repo", 1, "token")
        self.assertEqual(result, {"number": 1})

    @patch("scripts.grooming_runner.requests.get")
    def test_github_get_issue_404(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        result = gr.github_get_issue("owner", "repo", 1, "token")
        self.assertIsNone(result)

    @patch("scripts.grooming_runner.requests.patch")
    def test_assign_issue(self, mock_patch):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_patch.return_value = mock_resp

        gr.assign_issue("owner", "repo", 1, "assignee", "token")
        mock_patch.assert_called_once()

    @patch("scripts.grooming_runner.requests.delete")
    def test_remove_label(self, mock_delete):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_delete.return_value = mock_resp

        gr.remove_label("owner", "repo", 1, "label", "token")
        mock_delete.assert_called_once()

    @patch("scripts.grooming_runner.requests.get")
    def test_get_project_columns(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = [{"id": 1}]
        mock_get.return_value = mock_resp

        result = gr.get_project_columns("owner", "repo", 1, "token")
        self.assertEqual(result, [{"id": 1}])

    @patch("scripts.grooming_runner.requests.get")
    def test_get_column_cards(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = [{"id": 1}]
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
        mock_post.return_value = mock_resp

        gr.move_card(1, 2, "token")
        mock_post.assert_called_once()

    @patch("scripts.grooming_runner.get_project_columns")
    @patch("scripts.grooming_runner.get_column_cards")
    @patch("scripts.grooming_runner.find_card_for_issue")
    @patch("scripts.grooming_runner.move_card")
    def test_move_issue_to_backlog_column(self, mock_move, mock_find, mock_cards, mock_columns):
        mock_columns.return_value = [{"id": 1}]
        mock_cards.return_value = [{"id": 1}]
        mock_find.return_value = {"id": 1}

        gr.move_issue_to_backlog_column("owner", "repo", 1, "url", 1, 2, "token")
        mock_move.assert_called_once_with(1, 2, "token")

    @patch("scripts.grooming_runner.get_project_columns")
    @patch("scripts.grooming_runner.get_column_cards")
    @patch("scripts.grooming_runner.find_card_for_issue")
    def test_move_issue_to_backlog_column_no_card(self, mock_find, mock_cards, mock_columns):
        mock_columns.return_value = [{"id": 1}]
        mock_cards.return_value = []
        mock_find.return_value = None

        gr.move_issue_to_backlog_column("owner", "repo", 1, "url", 1, 2, "token")
        # Should not call move_card

    @patch.dict(os.environ, {"GITHUB_REPOSITORY": "owner/repo", "GITHUB_TOKEN": "token"})
    @patch("scripts.grooming_runner.load_rules")
    @patch("scripts.grooming_runner.github_search_issues")
    def test_main_dry_run_no_token(self, mock_search, mock_load):
        mock_load.return_value = {"project_management": {"enabled": False}, "grooming_bot_settings": {}}
        mock_search.return_value = []

        with patch.dict(os.environ, {"GITHUB_TOKEN": ""}):
            result = gr.main()
            self.assertEqual(result, 0)

    @patch.dict(os.environ, {})
    @patch("scripts.grooming_runner.load_rules")
    def test_main_no_repo(self, mock_load):
        mock_load.return_value = {"project_management": {}, "grooming_bot_settings": {}}
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

    @patch.dict(os.environ, {"GITHUB_REPOSITORY": "owner/repo", "GITHUB_TOKEN": ""})
    @patch("scripts.grooming_runner.load_rules")
    @patch("scripts.grooming_runner.github_search_issues")
    def test_main_no_token(self, mock_search, mock_load):
        mock_load.return_value = {"project_management": {}, "grooming_bot_settings": {}}
        mock_search.return_value = []
        result = gr.main()
        self.assertEqual(result, 0)

    @patch.dict(os.environ, {"GITHUB_REPOSITORY": "owner/repo", "GITHUB_TOKEN": "token", "DRY_RUN": "true"})
    @patch("scripts.grooming_runner.load_rules")
    @patch("scripts.grooming_runner.github_search_issues")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_main_dry_run_with_issues(self, mock_json_dump, mock_open_file, mock_search, mock_load):
        mock_load.side_effect = [
            {"project_management": {"enabled": True, "project_id": 1, "columns": {"Backlog": 2}}},
            {"grooming_bot_settings": {"needs_info_variants": ["needs-info"]}}
        ]
        mock_search.return_value = [
            {"number": 1, "title": "Test", "labels": [{"name": "needs-info"}], "url": "url1"}
        ]
        result = gr.main()
        self.assertEqual(result, 0)
        mock_json_dump.assert_called()

    @patch.dict(os.environ, {"GITHUB_REPOSITORY": "owner/repo", "GITHUB_TOKEN": "token"})
    @patch("scripts.grooming_runner.load_rules")
    @patch("scripts.grooming_runner.github_search_issues")
    @patch("scripts.grooming_runner.assign_issue")
    @patch("scripts.grooming_runner.remove_label")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_main_assign_exception(self, mock_json_dump, mock_open_file, mock_remove, mock_assign, mock_search, mock_load):
        mock_load.side_effect = [
            {"project_management": {}},
            {"grooming_bot_settings": {"needs_info_variants": ["needs-info"]}}
        ]
        mock_search.return_value = [
            {"number": 1, "title": "Test", "labels": [{"name": "needs-info"}], "url": "url1"}
        ]
        mock_assign.side_effect = Exception("error")
        result = gr.main()
        self.assertEqual(result, 0)

    @patch.dict(os.environ, {"GITHUB_REPOSITORY": "owner/repo", "GITHUB_TOKEN": "token"})
    @patch("scripts.grooming_runner.load_rules")
    @patch("scripts.grooming_runner.github_search_issues")
    @patch("scripts.grooming_runner.move_issue_to_backlog_column")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_main_move_exception(self, mock_json_dump, mock_open_file, mock_move, mock_search, mock_load):
        mock_load.side_effect = [
            {"project_management": {"enabled": True, "project_id": 1, "columns": {"Backlog": 2}}},
            {"grooming_bot_settings": {}}
        ]
        mock_search.return_value = [
            {"number": 1, "title": "Test", "labels": [{"name": "Triaged"}, {"name": "Backlog"}], "url": "url1"}
        ]
        mock_move.side_effect = Exception("error")
        result = gr.main()
        self.assertEqual(result, 0)

    @patch.dict(os.environ, {"GITHUB_REPOSITORY": "owner/repo", "GITHUB_TOKEN": "token"})
    @patch("scripts.grooming_runner.load_rules")
    @patch("scripts.grooming_runner.github_search_issues")
    def test_main_search_exception(self, mock_search, mock_load):
        mock_load.return_value = {"project_management": {}, "grooming_bot_settings": {}}
        mock_search.side_effect = Exception("error")
        result = gr.main()
        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()