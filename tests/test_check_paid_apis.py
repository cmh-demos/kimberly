"""Tests for the paid API checker script."""

import os
import tempfile
import unittest
from pathlib import Path

from scripts.check_paid_apis import (
    ALLOWED_FILES,
    DEFAULT_EXCLUDES,
    PAID_API_PATTERNS,
    Violation,
    format_violations,
    is_allowed_file,
    main,
    scan_directory,
    scan_file,
    should_exclude,
)


class TestShouldExclude(unittest.TestCase):
    """Tests for the should_exclude function."""

    def test_excludes_pyc_files(self):
        """Should exclude .pyc files."""
        path = Path("test.pyc")
        self.assertTrue(should_exclude(path, DEFAULT_EXCLUDES))

    def test_excludes_pycache(self):
        """Should exclude __pycache__ directories."""
        path = Path("__pycache__")
        self.assertTrue(should_exclude(path, DEFAULT_EXCLUDES))

    def test_excludes_venv(self):
        """Should exclude venv directories."""
        path = Path("venv")
        self.assertTrue(should_exclude(path, DEFAULT_EXCLUDES))

    def test_excludes_git(self):
        """Should exclude .git directories."""
        path = Path(".git")
        self.assertTrue(should_exclude(path, DEFAULT_EXCLUDES))

    def test_does_not_exclude_python_files(self):
        """Should not exclude regular Python files."""
        path = Path("main.py")
        self.assertFalse(should_exclude(path, DEFAULT_EXCLUDES))

    def test_custom_exclude_pattern(self):
        """Should support custom exclude patterns."""
        path = Path("custom_file.txt")
        self.assertTrue(should_exclude(path, ["*.txt"]))


class TestIsAllowedFile(unittest.TestCase):
    """Tests for the is_allowed_file function."""

    def test_allows_readme(self):
        """Should allow README.md."""
        path = Path("README.md")
        self.assertTrue(is_allowed_file(path, ALLOWED_FILES))

    def test_allows_free_runbook(self):
        """Should allow FREE_RUNBOOK.md."""
        path = Path("FREE_RUNBOOK.md")
        self.assertTrue(is_allowed_file(path, ALLOWED_FILES))

    def test_allows_yaml_files(self):
        """Should allow YAML files."""
        path = Path("config.yml")
        self.assertTrue(is_allowed_file(path, ALLOWED_FILES))

    def test_allows_requirements(self):
        """Should allow requirements files."""
        path = Path("requirements.txt")
        self.assertTrue(is_allowed_file(path, ALLOWED_FILES))
        path = Path("requirements-dev.txt")
        self.assertTrue(is_allowed_file(path, ALLOWED_FILES))

    def test_does_not_allow_regular_python(self):
        """Should not allow regular Python files."""
        path = Path("main.py")
        self.assertFalse(is_allowed_file(path, ALLOWED_FILES))


class TestScanFile(unittest.TestCase):
    """Tests for the scan_file function."""

    def test_detects_openai_import(self):
        """Should detect OpenAI imports."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("import openai\n")
            f.write("client = openai.Client()\n")
            f.flush()

            try:
                violations = scan_file(Path(f.name), PAID_API_PATTERNS)
                self.assertEqual(len(violations), 2)
                self.assertTrue(
                    any("OpenAI" in v.description for v in violations)
                )
            finally:
                os.unlink(f.name)

    def test_detects_anthropic(self):
        """Should detect Anthropic references."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("from anthropic import Client\n")
            f.flush()

            try:
                violations = scan_file(Path(f.name), PAID_API_PATTERNS)
                self.assertEqual(len(violations), 1)
                self.assertIn("Anthropic", violations[0].description)
            finally:
                os.unlink(f.name)

    def test_detects_pinecone(self):
        """Should detect Pinecone references."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("import pinecone\n")
            f.flush()

            try:
                violations = scan_file(Path(f.name), PAID_API_PATTERNS)
                self.assertEqual(len(violations), 1)
                self.assertIn("Pinecone", violations[0].description)
            finally:
                os.unlink(f.name)

    def test_ignores_comments(self):
        """Should ignore comment lines."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("# import openai\n")
            f.write("# This uses anthropic\n")
            f.flush()

            try:
                violations = scan_file(Path(f.name), PAID_API_PATTERNS)
                self.assertEqual(len(violations), 0)
            finally:
                os.unlink(f.name)

    def test_no_violations_clean_file(self):
        """Should return empty list for clean files."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("import os\n")
            f.write("import sys\n")
            f.write("print('Hello, world!')\n")
            f.flush()

            try:
                violations = scan_file(Path(f.name), PAID_API_PATTERNS)
                self.assertEqual(len(violations), 0)
            finally:
                os.unlink(f.name)


class TestScanDirectory(unittest.TestCase):
    """Tests for the scan_directory function."""

    def test_scans_python_files(self):
        """Should scan Python files in directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a Python file with violations
            py_file = Path(tmpdir) / "test.py"
            py_file.write_text("import openai\n")

            violations = scan_directory(
                Path(tmpdir),
                PAID_API_PATTERNS,
                DEFAULT_EXCLUDES,
                ALLOWED_FILES,
            )

            self.assertEqual(len(violations), 1)

    def test_excludes_venv(self):
        """Should exclude venv directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a venv directory with violations
            venv_dir = Path(tmpdir) / "venv"
            venv_dir.mkdir()
            (venv_dir / "test.py").write_text("import openai\n")

            violations = scan_directory(
                Path(tmpdir),
                PAID_API_PATTERNS,
                DEFAULT_EXCLUDES,
                ALLOWED_FILES,
            )

            self.assertEqual(len(violations), 0)

    def test_allows_documentation(self):
        """Should skip allowed documentation files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a README with paid API references
            readme = Path(tmpdir) / "README.md"
            readme.write_text("We don't use openai or anthropic\n")

            violations = scan_directory(
                Path(tmpdir),
                PAID_API_PATTERNS,
                DEFAULT_EXCLUDES,
                ALLOWED_FILES,
                [".md"],
            )

            self.assertEqual(len(violations), 0)


class TestFormatViolations(unittest.TestCase):
    """Tests for the format_violations function."""

    def test_no_violations_message(self):
        """Should show success message when no violations."""
        result = format_violations([])
        self.assertIn("No paid API usage detected", result)
        self.assertIn("passed", result)

    def test_formats_violations(self):
        """Should format violations correctly."""
        violations = [
            Violation(
                file_path="test.py",
                line_number=1,
                line_content="import openai",
                pattern_matched=r"\bopenai\b",
                description="OpenAI API",
            )
        ]
        result = format_violations(violations)
        self.assertIn("PAID API USAGE DETECTED", result)
        self.assertIn("test.py", result)
        self.assertIn("Line 1", result)
        self.assertIn("OpenAI API", result)
        self.assertIn("Total violations: 1", result)


class TestMain(unittest.TestCase):
    """Tests for the main function."""

    def test_returns_zero_for_clean_directory(self):
        """Should return 0 when no violations found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a clean Python file
            (Path(tmpdir) / "clean.py").write_text("print('hello')\n")

            result = main(["--path", tmpdir, "--quiet"])
            self.assertEqual(result, 0)

    def test_returns_one_for_violations(self):
        """Should return 1 when violations found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file with violations
            (Path(tmpdir) / "bad.py").write_text("import openai\n")

            result = main(["--path", tmpdir])
            self.assertEqual(result, 1)

    def test_returns_two_for_invalid_path(self):
        """Should return 2 for invalid path."""
        result = main(["--path", "/nonexistent/path/12345"])
        self.assertEqual(result, 2)

    def test_respects_exclude_flag(self):
        """Should respect --exclude flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file with violations
            (Path(tmpdir) / "vendor.py").write_text("import openai\n")

            result = main(["--path", tmpdir, "--exclude", "vendor.py"])
            self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
