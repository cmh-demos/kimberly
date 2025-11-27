"""Tests for memory_scoring module."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import memory_scoring as ms


class TestWeightValidation(unittest.TestCase):
    """Tests for weight validation."""

    def test_validate_weights_valid(self):
        weights = {
            "relevance_to_goals": 0.40,
            "emotional_weight": 0.30,
            "predictive_value": 0.20,
            "recency_freq": 0.10,
        }
        result = ms.validate_weights(weights)
        self.assertEqual(result, weights)

    def test_validate_weights_normalizes(self):
        weights = {
            "relevance_to_goals": 0.80,
            "emotional_weight": 0.60,
            "predictive_value": 0.40,
            "recency_freq": 0.20,
        }
        result = ms.validate_weights(weights)
        total = sum(result.values())
        self.assertAlmostEqual(total, 1.0, places=5)

    def test_validate_weights_missing_keys(self):
        weights = {
            "relevance_to_goals": 0.40,
            "emotional_weight": 0.30,
        }
        with self.assertRaises(ValueError) as ctx:
            ms.validate_weights(weights)
        self.assertIn("Missing weight keys", str(ctx.exception))

    def test_validate_weights_out_of_range(self):
        weights = {
            "relevance_to_goals": 1.5,
            "emotional_weight": 0.30,
            "predictive_value": 0.20,
            "recency_freq": 0.10,
        }
        with self.assertRaises(ValueError) as ctx:
            ms.validate_weights(weights)
        self.assertIn("between 0.0 and 1.0", str(ctx.exception))

    def test_validate_weights_negative(self):
        weights = {
            "relevance_to_goals": -0.40,
            "emotional_weight": 0.30,
            "predictive_value": 0.20,
            "recency_freq": 0.10,
        }
        with self.assertRaises(ValueError) as ctx:
            ms.validate_weights(weights)
        self.assertIn("between 0.0 and 1.0", str(ctx.exception))

    def test_validate_weights_all_zero(self):
        weights = {
            "relevance_to_goals": 0.0,
            "emotional_weight": 0.0,
            "predictive_value": 0.0,
            "recency_freq": 0.0,
        }
        with self.assertRaises(ValueError) as ctx:
            ms.validate_weights(weights)
        self.assertIn(
            "At least one weight must be non-zero",
            str(ctx.exception),
        )

    def test_validate_weights_non_numeric(self):
        weights = {
            "relevance_to_goals": "invalid",
            "emotional_weight": 0.30,
            "predictive_value": 0.20,
            "recency_freq": 0.10,
        }
        with self.assertRaises(ValueError) as ctx:
            ms.validate_weights(weights)
        self.assertIn("must be numeric", str(ctx.exception))


class TestWeightPresets(unittest.TestCase):
    """Tests for weight presets."""

    def test_all_presets_sum_to_one(self):
        for name, weights in ms.WEIGHT_PRESETS.items():
            total = sum(weights.values())
            self.assertAlmostEqual(
                total,
                1.0,
                places=5,
                msg=f"Preset '{name}' weights don't sum to 1.0",
            )

    def test_all_presets_have_required_keys(self):
        required_keys = set(ms.DEFAULT_WEIGHTS.keys())
        for name, weights in ms.WEIGHT_PRESETS.items():
            self.assertEqual(
                set(weights.keys()),
                required_keys,
                msg=f"Preset '{name}' missing keys",
            )


class TestLoadWeightsFromEnv(unittest.TestCase):
    """Tests for loading weights from environment variables."""

    @patch.dict(os.environ, {}, clear=True)
    def test_load_weights_from_env_none_set(self):
        result = ms.load_weights_from_env()
        self.assertIsNone(result)

    @patch.dict(
        os.environ,
        {
            "KIMBERLY_WEIGHT_RELEVANCE": "0.50",
            "KIMBERLY_WEIGHT_EMOTIONAL": "0.25",
            "KIMBERLY_WEIGHT_PREDICTIVE": "0.15",
            "KIMBERLY_WEIGHT_RECENCY": "0.10",
        },
    )
    def test_load_weights_from_env_all_set(self):
        result = ms.load_weights_from_env()
        self.assertIsNotNone(result)
        self.assertEqual(result["relevance_to_goals"], 0.50)
        self.assertEqual(result["emotional_weight"], 0.25)
        self.assertEqual(result["predictive_value"], 0.15)
        self.assertEqual(result["recency_freq"], 0.10)

    @patch.dict(
        os.environ,
        {"KIMBERLY_WEIGHT_RELEVANCE": "0.60"},
        clear=True,
    )
    def test_load_weights_from_env_partial_set(self):
        result = ms.load_weights_from_env()
        self.assertIsNotNone(result)
        self.assertEqual(result["relevance_to_goals"], 0.60)
        # Other values should be defaults
        self.assertEqual(
            result["emotional_weight"],
            ms.DEFAULT_WEIGHTS["emotional_weight"],
        )

    @patch.dict(
        os.environ,
        {"KIMBERLY_WEIGHT_RELEVANCE": "invalid"},
        clear=True,
    )
    def test_load_weights_from_env_invalid_value(self):
        # When only one env var is set with an invalid value, we still
        # return a result (with defaults) because the env var was present
        # But the function returns None if the only set env var is invalid
        # because any_set only becomes True if we successfully parse a value
        result = ms.load_weights_from_env()
        # With only an invalid value, any_set is False, so None is returned
        self.assertIsNone(result)


class TestLoadWeightsFromYaml(unittest.TestCase):
    """Tests for loading weights from YAML files."""

    def test_load_weights_from_yaml_nonexistent(self):
        result = ms.load_weights_from_yaml(Path("/nonexistent/path.yaml"))
        self.assertIsNone(result)

    def test_load_weights_from_yaml_valid(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(
                """
scoring_weights:
  relevance_to_goals: 0.50
  emotional_weight: 0.25
  predictive_value: 0.15
  recency_freq: 0.10
"""
            )
            f.flush()
            try:
                result = ms.load_weights_from_yaml(Path(f.name))
                self.assertIsNotNone(result)
                self.assertEqual(result["relevance_to_goals"], 0.50)
            finally:
                os.unlink(f.name)

    def test_load_weights_from_yaml_preset(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(
                """
scoring_weights:
  preset: task-focused
"""
            )
            f.flush()
            try:
                result = ms.load_weights_from_yaml(Path(f.name))
                self.assertIsNotNone(result)
                self.assertEqual(
                    result,
                    ms.WEIGHT_PRESETS["task-focused"],
                )
            finally:
                os.unlink(f.name)

    def test_load_weights_from_yaml_unknown_preset(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(
                """
scoring_weights:
  preset: unknown-preset
"""
            )
            f.flush()
            try:
                result = ms.load_weights_from_yaml(Path(f.name))
                self.assertIsNone(result)
            finally:
                os.unlink(f.name)

    def test_load_weights_from_yaml_no_scoring_weights(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(
                """
other_config: value
"""
            )
            f.flush()
            try:
                result = ms.load_weights_from_yaml(Path(f.name))
                self.assertIsNone(result)
            finally:
                os.unlink(f.name)


class TestLoadWeights(unittest.TestCase):
    """Tests for the main load_weights function."""

    @patch.dict(os.environ, {}, clear=True)
    def test_load_weights_defaults(self):
        result = ms.load_weights()
        self.assertEqual(result, ms.DEFAULT_WEIGHTS)

    @patch.dict(
        os.environ,
        {"KIMBERLY_WEIGHT_RELEVANCE": "0.60"},
        clear=True,
    )
    def test_load_weights_from_env_priority(self):
        result = ms.load_weights()
        # Env vars should be used and normalized
        self.assertGreater(result["relevance_to_goals"], 0.40)


class TestMemoryScorer(unittest.TestCase):
    """Tests for MemoryScorer class."""

    def test_scorer_default_weights(self):
        scorer = ms.MemoryScorer()
        self.assertEqual(scorer.weights, ms.DEFAULT_WEIGHTS)

    def test_scorer_custom_weights(self):
        custom_weights = {
            "relevance_to_goals": 0.50,
            "emotional_weight": 0.25,
            "predictive_value": 0.15,
            "recency_freq": 0.10,
        }
        scorer = ms.MemoryScorer(weights=custom_weights)
        self.assertEqual(scorer.weights, custom_weights)

    def test_scorer_validates_custom_weights(self):
        invalid_weights = {
            "relevance_to_goals": 1.5,
            "emotional_weight": 0.25,
            "predictive_value": 0.15,
            "recency_freq": 0.10,
        }
        with self.assertRaises(ValueError):
            ms.MemoryScorer(weights=invalid_weights)

    def test_score_memory(self):
        scorer = ms.MemoryScorer()
        sample_item = {
            "id": "mem_123",
            "user_id": "user_1",
            "type": "long-term",
            "content": "Test",
            "size_bytes": 1024,
            "metadata": {
                "tags": ["preference"],
                "user_feedback": "thumbs_up",
            },
            "created_at": "2025-11-20T10:00:00Z",
            "last_seen_at": "2025-11-22T10:00:00Z",
        }
        score = scorer.score_memory(sample_item)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


class TestMeditationEngine(unittest.TestCase):
    """Tests for MeditationEngine class."""

    def test_meditation_engine_default_scorer(self):
        engine = ms.MeditationEngine()
        self.assertIsInstance(engine.scorer, ms.MemoryScorer)

    def test_meditation_engine_custom_scorer(self):
        custom_weights = {
            "relevance_to_goals": 0.50,
            "emotional_weight": 0.25,
            "predictive_value": 0.15,
            "recency_freq": 0.10,
        }
        scorer = ms.MemoryScorer(weights=custom_weights)
        engine = ms.MeditationEngine(scorer=scorer)
        self.assertEqual(engine.scorer.weights, custom_weights)

    def test_run_meditation(self):
        engine = ms.MeditationEngine()
        items = [
            {
                "id": "mem_1",
                "type": "long-term",
                "size_bytes": 1024,
                "metadata": {},
                "created_at": "2025-11-20T10:00:00Z",
                "last_seen_at": "2025-11-22T10:00:00Z",
            }
        ]
        quotas = {
            "short-term": 512 * 1024,
            "long-term": 2 * 1024 * 1024,
            "permanent": 10 * 1024 * 1024,
        }
        result = engine.run_meditation(items, quotas)
        self.assertIn("scored_items", result)
        self.assertIn("to_prune", result)
        self.assertIn("summary", result)


if __name__ == "__main__":
    unittest.main()
