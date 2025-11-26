import json
import unittest
from unittest.mock import mock_open, patch

import scripts.validate_copilot_tracking as vct


class TestValidateCopilotTracking(unittest.TestCase):
    """Tests for the validate_copilot_tracking script."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "request_start_time": {"type": "string"},
                    "request_end_time": {"type": "string"},
                    "tokens_used_estimate": {"type": "integer", "minimum": 0},
                    "note": {"type": "string"},
                    "processing_time_microseconds": {
                        "type": "integer",
                        "minimum": 0,
                    },
                    "processing_time_seconds": {"type": "number", "minimum": 0},
                },
                "required": [
                    "request_start_time",
                    "request_end_time",
                    "tokens_used_estimate",
                    "note",
                ],
                "oneOf": [
                    {"required": ["processing_time_microseconds"]},
                    {"required": ["processing_time_seconds"]},
                ],
            },
        }

        self.valid_entry = {
            "request_start_time": "2025-11-26T10:00:00.000000Z",
            "request_end_time": "2025-11-26T10:01:00.000000Z",
            "tokens_used_estimate": 100,
            "note": "Test entry",
            "processing_time_microseconds": 60000000,
        }

    @patch("builtins.open", new_callable=mock_open)
    def test_valid_empty_file(self, mock_file):
        """Test validation with an empty file (should return empty array)."""
        # Set up mock to return different content for different files
        mock_file.side_effect = [
            mock_open(read_data=json.dumps(self.valid_schema))(),
            mock_open(read_data="")(),
        ]

        result = vct.main()
        self.assertEqual(result, 0)

    @patch("builtins.open", new_callable=mock_open)
    def test_valid_whitespace_only_file(self, mock_file):
        """Test validation with whitespace-only file."""
        mock_file.side_effect = [
            mock_open(read_data=json.dumps(self.valid_schema))(),
            mock_open(read_data="   \n\t  ")(),
        ]

        result = vct.main()
        self.assertEqual(result, 0)

    @patch("builtins.open", new_callable=mock_open)
    def test_valid_data_single_entry(self, mock_file):
        """Test validation with a single valid entry."""
        mock_file.side_effect = [
            mock_open(read_data=json.dumps(self.valid_schema))(),
            mock_open(read_data=json.dumps([self.valid_entry]))(),
        ]

        result = vct.main()
        self.assertEqual(result, 0)

    @patch("builtins.open", new_callable=mock_open)
    def test_valid_data_multiple_entries(self, mock_file):
        """Test validation with multiple valid entries."""
        entries = [
            self.valid_entry,
            {
                "request_start_time": "2025-11-26T11:00:00.000000Z",
                "request_end_time": "2025-11-26T11:02:00.000000Z",
                "tokens_used_estimate": 200,
                "note": "Second test entry",
                "processing_time_seconds": 120.5,
            },
        ]
        mock_file.side_effect = [
            mock_open(read_data=json.dumps(self.valid_schema))(),
            mock_open(read_data=json.dumps(entries))(),
        ]

        result = vct.main()
        self.assertEqual(result, 0)

    @patch("builtins.open", new_callable=mock_open)
    def test_invalid_data_missing_required_field(self, mock_file):
        """Test validation fails when required field is missing."""
        invalid_entry = {
            "request_start_time": "2025-11-26T10:00:00.000000Z",
            "request_end_time": "2025-11-26T10:01:00.000000Z",
            # Missing tokens_used_estimate
            "note": "Test entry",
            "processing_time_microseconds": 60000000,
        }
        mock_file.side_effect = [
            mock_open(read_data=json.dumps(self.valid_schema))(),
            mock_open(read_data=json.dumps([invalid_entry]))(),
        ]

        result = vct.main()
        self.assertEqual(result, 1)

    @patch("builtins.open", new_callable=mock_open)
    def test_invalid_data_wrong_type(self, mock_file):
        """Test validation fails when field has wrong type."""
        invalid_entry = {
            "request_start_time": "2025-11-26T10:00:00.000000Z",
            "request_end_time": "2025-11-26T10:01:00.000000Z",
            "tokens_used_estimate": "not_a_number",  # Should be integer
            "note": "Test entry",
            "processing_time_microseconds": 60000000,
        }
        mock_file.side_effect = [
            mock_open(read_data=json.dumps(self.valid_schema))(),
            mock_open(read_data=json.dumps([invalid_entry]))(),
        ]

        result = vct.main()
        self.assertEqual(result, 1)

    @patch("builtins.open", new_callable=mock_open)
    def test_invalid_data_not_array(self, mock_file):
        """Test validation fails when data is not an array."""
        mock_file.side_effect = [
            mock_open(read_data=json.dumps(self.valid_schema))(),
            mock_open(read_data=json.dumps({"not": "an array"}))(),
        ]

        result = vct.main()
        self.assertEqual(result, 1)

    @patch("builtins.open", new_callable=mock_open)
    def test_invalid_json_syntax(self, mock_file):
        """Test handling of malformed JSON."""
        mock_file.side_effect = [
            mock_open(read_data=json.dumps(self.valid_schema))(),
            mock_open(read_data="{ invalid json }")(),
        ]

        with self.assertRaises(json.JSONDecodeError):
            vct.main()

    @patch("builtins.open", new_callable=mock_open)
    def test_valid_empty_array(self, mock_file):
        """Test validation with an empty array."""
        mock_file.side_effect = [
            mock_open(read_data=json.dumps(self.valid_schema))(),
            mock_open(read_data="[]")(),
        ]

        result = vct.main()
        self.assertEqual(result, 0)

    @patch("builtins.open", new_callable=mock_open)
    def test_invalid_negative_tokens(self, mock_file):
        """Test validation fails with negative token count."""
        invalid_entry = {
            "request_start_time": "2025-11-26T10:00:00.000000Z",
            "request_end_time": "2025-11-26T10:01:00.000000Z",
            "tokens_used_estimate": -100,  # Should be >= 0
            "note": "Test entry",
            "processing_time_microseconds": 60000000,
        }
        mock_file.side_effect = [
            mock_open(read_data=json.dumps(self.valid_schema))(),
            mock_open(read_data=json.dumps([invalid_entry]))(),
        ]

        result = vct.main()
        self.assertEqual(result, 1)


class TestMainOutput(unittest.TestCase):
    """Test output messages from the validation script."""

    @patch("builtins.print")
    @patch("builtins.open", new_callable=mock_open)
    def test_success_message(self, mock_file, mock_print):
        """Test success message is printed for valid data."""
        schema = {"type": "array", "items": {"type": "object"}}
        mock_file.side_effect = [
            mock_open(read_data=json.dumps(schema))(),
            mock_open(read_data="[]")(),
        ]

        vct.main()
        mock_print.assert_called_with("copilot_tracking.json is valid")

    @patch("builtins.print")
    @patch("builtins.open", new_callable=mock_open)
    def test_error_message_contains_path(self, mock_file, mock_print):
        """Test error message contains file path."""
        schema = {"type": "array", "items": {"type": "string"}}
        mock_file.side_effect = [
            mock_open(read_data=json.dumps(schema))(),
            mock_open(read_data="[123]")(),  # Invalid: number instead of string
        ]

        result = vct.main()
        self.assertEqual(result, 1)
        # Verify print was called and contains the filename
        call_args = mock_print.call_args[0][0]
        self.assertIn("misc/copilot_tracking.json", call_args)


if __name__ == "__main__":
    unittest.main()
