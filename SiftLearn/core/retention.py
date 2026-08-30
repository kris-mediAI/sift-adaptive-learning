import math
from datetime import datetime, timezone


class RetentionEngine:
    """
    Estimates retention risk and decides when a concept
    should be reviewed.

    This is intentionally lightweight and explainable.
    """

    def __init__(self, review_threshold=65):
        self.review_threshold = review_threshold

    def days_since_seen(self, concept, now=None):
        if concept.last_seen is None:
            return None

        if now is None:
            now = datetime.now(timezone.utc)

        last_seen = datetime.fromisoformat(
            concept.last_seen
        )

        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(
                tzinfo=timezone.utc
            )

        elapsed = now - last_seen

        return max(
            0.0,
            elapsed.total_seconds() / 86400
        )

    def stability_days(self, concept):
        """
        Estimate how stable the memory currently is.

        Higher mastery + successful reviews increase
        the estimated stability.
        """

        mastery_factor = max(
            concept.mastery / 100,
            0.10
        )

        review_bonus = (
            concept.successful_reviews * 1.5
        )

        evidence_bonus = min(
            concept.attempts * 0.35,
            2.0
        )

        return max(
            1.0,
            1.0
            + mastery_factor * 4
            + review_bonus
            + evidence_bonus
        )

    def predicted_retention(
        self,
        concept,
        now=None
    ):
        """
        Exponential forgetting approximation.

        Returns a value from 0 to 100.
        """

        days = self.days_since_seen(
            concept,
            now
        )

        if days is None:
            return 0.0

        stability = self.stability_days(
            concept
        )

        retention = math.exp(
            -days / stability
        )

        return round(
            retention * 100,
            2
        )

    def review_priority(
        self,
        concept,
        now=None
    ):
        """
        Combine predicted forgetting with concept mastery.

        Higher result = stronger reason to review.
        """

        retention = self.predicted_retention(
            concept,
            now
        )

        forgetting_risk = (
            100 - retention
        )

        mastery_risk = (
            100 - concept.mastery
        )

        priority = (
            forgetting_risk * 0.65
            + mastery_risk * 0.35
        )

        return round(priority, 2)

    def needs_review(
        self,
        concept,
        now=None
    ):
        if concept.last_seen is None:
            return False

        retention = self.predicted_retention(
            concept,
            now
        )

        return (
            retention < self.review_threshold
            and concept.mastery >= 50
        )

    def explain(
        self,
        concept,
        now=None
    ):
        retention = self.predicted_retention(
            concept,
            now
        )

        days = self.days_since_seen(
            concept,
            now
        )

        return {
            "concept": concept.name,
            "mastery": round(
                concept.mastery,
                2
            ),
            "confidence": round(
                concept.confidence,
                2
            ),
            "days_since_seen": (
                round(days, 2)
                if days is not None
                else None
            ),
            "predicted_retention": retention,
            "review_priority": self.review_priority(
                concept,
                now
            ),
            "needs_review": self.needs_review(
                concept,
                now
            )
        }