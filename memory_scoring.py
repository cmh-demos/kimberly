"""
Memory scoring and meditation logic for Kimberly.

This module implements the scoring formula and nightly meditation process
for memory retention and pruning.
"""

import logging
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Default scoring weights
DEFAULT_WEIGHTS = {
    "relevance_to_goals": 0.40,
    "emotional_weight": 0.30,
    "predictive_value": 0.20,
    "recency_freq": 0.10,
}

# Preset weight profiles
WEIGHT_PRESETS = {
    "balanced": {
        "relevance_to_goals": 0.40,
        "emotional_weight": 0.30,
        "predictive_value": 0.20,
        "recency_freq": 0.10,
    },
    "task-focused": {
        "relevance_to_goals": 0.55,
        "emotional_weight": 0.15,
        "predictive_value": 0.20,
        "recency_freq": 0.10,
    },
    "feedback-driven": {
        "relevance_to_goals": 0.25,
        "emotional_weight": 0.50,
        "predictive_value": 0.15,
        "recency_freq": 0.10,
    },
    "fresh-context": {
        "relevance_to_goals": 0.30,
        "emotional_weight": 0.20,
        "predictive_value": 0.15,
        "recency_freq": 0.35,
    },
    "archival": {
        "relevance_to_goals": 0.45,
        "emotional_weight": 0.25,
        "predictive_value": 0.25,
        "recency_freq": 0.05,
    },
}

# For backwards compatibility
WEIGHTS = DEFAULT_WEIGHTS


def load_weights_from_yaml(path: Path) -> Optional[Dict[str, float]]:
    """
    Load scoring weights from a YAML config file.

    Args:
        path: Path to the YAML config file

    Returns:
        Dict of weights if valid, None otherwise
    """
    try:
        import yaml

        if not path.exists():
            return None

        with open(path, "r") as f:
            config = yaml.safe_load(f)

        if not config or "scoring_weights" not in config:
            return None

        weights_config = config["scoring_weights"]

        # Check for preset
        if isinstance(weights_config, dict) and "preset" in weights_config:
            preset_name = weights_config["preset"]
            if preset_name in WEIGHT_PRESETS:
                return WEIGHT_PRESETS[preset_name].copy()
            logger.warning(f"Unknown preset '{preset_name}', using defaults")
            return None

        # Parse individual weights
        if isinstance(weights_config, dict):
            weights = {}
            for key in DEFAULT_WEIGHTS:
                if key in weights_config:
                    weights[key] = float(weights_config[key])
                else:
                    weights[key] = DEFAULT_WEIGHTS[key]
            return weights

        return None
    except ImportError:
        logger.debug("PyYAML not installed, skipping YAML config")
        return None
    except Exception as e:
        logger.warning(f"Error loading weights from {path}: {e}")
        return None


def load_weights_from_env() -> Optional[Dict[str, float]]:
    """
    Load scoring weights from environment variables.

    Environment variables:
        KIMBERLY_WEIGHT_RELEVANCE
        KIMBERLY_WEIGHT_EMOTIONAL
        KIMBERLY_WEIGHT_PREDICTIVE
        KIMBERLY_WEIGHT_RECENCY

    Returns:
        Dict of weights if any env vars are set, None otherwise
    """
    env_mapping = {
        "relevance_to_goals": "KIMBERLY_WEIGHT_RELEVANCE",
        "emotional_weight": "KIMBERLY_WEIGHT_EMOTIONAL",
        "predictive_value": "KIMBERLY_WEIGHT_PREDICTIVE",
        "recency_freq": "KIMBERLY_WEIGHT_RECENCY",
    }

    weights = {}
    any_set = False

    for key, env_var in env_mapping.items():
        value = os.environ.get(env_var)
        if value is not None:
            try:
                weights[key] = float(value)
                any_set = True
            except ValueError:
                logger.warning(f"Invalid value for {env_var}: {value}")
                weights[key] = DEFAULT_WEIGHTS[key]
        else:
            weights[key] = DEFAULT_WEIGHTS[key]

    return weights if any_set else None


def validate_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """
    Validate and normalize scoring weights.

    Ensures:
    - All required weight keys are present
    - Each weight is between 0.0 and 1.0
    - At least one weight is non-zero
    - Weights are normalized to sum to 1.0

    Args:
        weights: Dict of weight values

    Returns:
        Validated and normalized weights

    Raises:
        ValueError: If weights are invalid
    """
    required_keys = set(DEFAULT_WEIGHTS.keys())
    provided_keys = set(weights.keys())

    # Check for missing keys
    missing = required_keys - provided_keys
    if missing:
        raise ValueError(f"Missing weight keys: {missing}")

    # Validate each weight is in range
    validated = {}
    for key in required_keys:
        value = weights[key]
        if not isinstance(value, (int, float)):
            raise ValueError(
                f"Weight '{key}' must be numeric, got {type(value)}"
            )
        if value < 0.0 or value > 1.0:
            raise ValueError(f"Weight '{key}' must be between 0.0 and 1.0")
        validated[key] = float(value)

    # Check at least one weight is non-zero
    total = sum(validated.values())
    if total == 0:
        raise ValueError("At least one weight must be non-zero")

    # Normalize to sum to 1.0
    if abs(total - 1.0) > 0.001:
        logger.info(f"Normalizing weights (sum={total:.3f}) to 1.0")
        validated = {k: v / total for k, v in validated.items()}

    return validated


def load_weights(user_id: Optional[str] = None) -> Dict[str, float]:
    """
    Load scoring weights from configuration sources.

    Priority order (highest to lowest):
    1. Per-user config file (~/.kimberly/scoring_weights.yaml)
    2. Environment variables
    3. System config file (/etc/kimberly/scoring_weights.yaml)
    4. Default weights

    Args:
        user_id: Optional user identifier for per-user config

    Returns:
        Validated and normalized weights
    """
    weights = None

    # Try per-user config
    if user_id:
        user_config = Path.home() / ".kimberly" / "scoring_weights.yaml"
        weights = load_weights_from_yaml(user_config)
        if weights:
            logger.debug(f"Loaded weights from user config: {user_config}")

    # Try environment variables
    if not weights:
        weights = load_weights_from_env()
        if weights:
            logger.debug("Loaded weights from environment variables")

    # Try system config
    if not weights:
        system_config = Path("/etc/kimberly/scoring_weights.yaml")
        weights = load_weights_from_yaml(system_config)
        if weights:
            logger.debug(f"Loaded weights from system config: {system_config}")

    # Fall back to defaults
    if not weights:
        weights = DEFAULT_WEIGHTS.copy()
        logger.debug("Using default weights")

    # Validate and normalize
    try:
        return validate_weights(weights)
    except ValueError as e:
        logger.warning(f"Invalid weights configuration: {e}, using defaults")
        return DEFAULT_WEIGHTS.copy()


class MemoryScorer:
    """Handles scoring of memory items."""

    def __init__(
        self,
        weights: Dict[str, float] = None,
        user_id: Optional[str] = None,
    ):
        """
        Initialize the scorer with custom or loaded weights.

        Args:
            weights: Optional custom weights dict. If not provided,
                     weights are loaded from configuration.
            user_id: Optional user ID for per-user weight configuration.
        """
        if weights is not None:
            self.weights = validate_weights(weights)
        else:
            self.weights = load_weights(user_id)

    def score_memory(self, memory_item: Dict[str, Any]) -> float:
        """
        Calculate score for a memory item.

        Args:
            memory_item: MemoryItem dict with metadata

        Returns:
            Normalized score between 0 and 1
        """
        components = self._calculate_components(memory_item)

        score = sum(
            self.weights[comp] * value for comp, value in components.items()
        )

        # Normalize to 0-1 range
        return min(max(score, 0.0), 1.0)

    def _calculate_components(
        self, memory_item: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate individual scoring components."""
        metadata = memory_item.get("metadata", {})
        created_at = datetime.fromisoformat(
            memory_item["created_at"].replace("Z", "+00:00")
        )
        last_seen = datetime.fromisoformat(
            memory_item["last_seen_at"].replace("Z", "+00:00")
        )
        now = datetime.now(timezone.utc)

        # Relevance to goals: Simple tag matching (placeholder)
        tags = metadata.get("tags", [])
        goal_tags = ["goal", "project", "task"]  # Configurable
        relevance = 1.0 if any(tag in goal_tags for tag in tags) else 0.5

        # Emotional weight: Based on user feedback
        feedback = metadata.get("user_feedback", "")
        if "thumbs_up" in feedback:
            emotion = 0.8
        elif "thumbs_down" in feedback:
            emotion = 0.2
        elif "rating:" in feedback:
            try:
                rating_str = feedback.split(":")[1]
                rating = int(rating_str)
                emotion = rating / 5.0
            except (ValueError, IndexError):
                emotion = 0.5
        else:
            emotion = 0.5

        # Predictive value: Based on recency
        days_since_created = (now - created_at).days
        days_since_seen = (now - last_seen).days
        recency_score = 1.0 / (
            days_since_seen + 1
        )  # Higher if recently accessed
        predictive = min(recency_score, 1.0)

        # Recency and frequency: Combined metric
        recency = math.exp(-days_since_seen / 30.0)  # Decay over 30 days
        frequency = min(
            days_since_created / 7.0, 1.0
        )  # Increases with age, reaches max at 1 week and remains constant
        recency_freq = (recency + frequency) / 2.0

        return {
            "relevance_to_goals": relevance,
            "emotional_weight": emotion,
            "predictive_value": predictive,
            "recency_freq": recency_freq,
        }


class MeditationEngine:
    """Handles the nightly meditation process."""

    def __init__(self, scorer: MemoryScorer = None):
        self.scorer = scorer or MemoryScorer()

    def run_meditation(
        self, memory_items: List[Dict[str, Any]], quotas: Dict[str, int]
    ) -> Dict[str, Any]:
        """
        Run meditation: score items and determine pruning.

        Args:
            memory_items: List of MemoryItem dicts
            quotas: Quota limits by tier (e.g., {'short-term': 512*1024})

        Returns:
            Dict with scores, to_prune list, and summary
        """
        # Score all items
        scored_items = []
        for item in memory_items:
            score = self.scorer.score_memory(item)
            item_copy = item.copy()
            item_copy["score"] = score
            scored_items.append(item_copy)

        # Sort by score descending
        scored_items.sort(key=lambda x: x["score"], reverse=True)

        # Determine pruning per tier
        to_prune = []
        tier_usage = {}

        for tier in ["short-term", "long-term", "permanent"]:
            tier_items = [item for item in scored_items if item["type"] == tier]
            quota = quotas.get(tier, 0)
            current_usage = sum(item["size_bytes"] for item in tier_items)

            if current_usage > quota:
                # Prune lowest scored items until under quota
                # Sort by score descending to keep highest-scored items first
                tier_items.sort(key=lambda x: x["score"], reverse=True)
                cumulative_size = 0
                for item in tier_items:
                    if cumulative_size + item["size_bytes"] <= quota:
                        cumulative_size += item["size_bytes"]
                    else:
                        to_prune.append(item["id"])

            tier_usage[tier] = current_usage

        return {
            "scored_items": scored_items,
            "to_prune": to_prune,
            "tier_usage": tier_usage,
            "summary": (
                f"Scored {len(scored_items)} items, pruning {len(to_prune)}"
            ),
        }


# Example usage
if __name__ == "__main__":
    scorer = MemoryScorer()
    engine = MeditationEngine(scorer)

    # Sample memory item
    sample_item = {
        "id": "mem_123",
        "user_id": "user_1",
        "type": "long-term",
        "content": "User prefers dark mode",
        "size_bytes": 1024,
        "metadata": {
            "tags": ["preference"],
            "source": "chat",
            "user_feedback": "thumbs_up",
        },
        "created_at": "2025-11-20T10:00:00Z",
        "last_seen_at": "2025-11-22T10:00:00Z",
    }

    score = scorer.score_memory(sample_item)
    print(f"Score: {score}")

    # Sample meditation
    items = [sample_item]
    quotas = {
        "short-term": 512 * 1024,
        "long-term": 2 * 1024 * 1024,
        "permanent": 10 * 1024 * 1024,
    }
    result = engine.run_meditation(items, quotas)
    print(result["summary"])
