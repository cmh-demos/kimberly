"""
Memory scoring and meditation logic for Kimberly.

This module implements the scoring formula and nightly meditation process
for memory retention and pruning.
"""

import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

# Scoring weights (configurable)
WEIGHTS = {
    "relevance_to_goals": 0.40,
    "emotional_weight": 0.30,
    "predictive_value": 0.20,
    "recency_freq": 0.10,
}


class MemoryScorer:
    """Handles scoring of memory items."""

    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or WEIGHTS

    def score_memory(self, memory_item: Dict[str, Any]) -> float:
        """
        Calculate score for a memory item.

        Args:
            memory_item: MemoryItem dict with metadata

        Returns:
            Normalized score between 0 and 1
        """
        components = self._calculate_components(memory_item)

        score = sum(self.weights[comp] * value for comp, value in components.items())

        # Normalize to 0-1 range
        return min(max(score, 0.0), 1.0)

    def _calculate_components(self, memory_item: Dict[str, Any]) -> Dict[str, float]:
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
            rating = int(feedback.split(":")[1])
            emotion = rating / 5.0
        else:
            emotion = 0.5

        # Predictive value: Based on access frequency
        days_since_created = (now - created_at).days
        days_since_seen = (now - last_seen).days
        access_freq = 1.0 / (days_since_seen + 1)  # Higher if recently accessed
        predictive = min(access_freq, 1.0)

        # Recency and frequency: Combined metric
        recency = math.exp(-days_since_seen / 30.0)  # Decay over 30 days
        frequency = min(
            days_since_created / 7.0, 1.0
        )  # Increase with age (up to 1 week)
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
                tier_items.sort(key=lambda x: x["score"])
                cumulative_size = 0
                for item in tier_items:
                    if cumulative_size + item["size_bytes"] > quota:
                        to_prune.append(item["id"])
                    else:
                        cumulative_size += item["size_bytes"]

            tier_usage[tier] = current_usage

        return {
            "scored_items": scored_items,
            "to_prune": to_prune,
            "tier_usage": tier_usage,
            "summary": f"Scored {len(scored_items)} items, pruning {len(to_prune)}",
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
