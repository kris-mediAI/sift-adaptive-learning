"""Learning progression helpers shared by Sift's adaptive engine and UI.

The progression layer deliberately stays small: it turns evidence already
stored by Sift into learner-facing journey state. It does not invent a second
mastery model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProgressionPolicy:
    """Evidence thresholds for completing a concept."""

    completion_mastery: float = 85.0
    completion_confidence: float = 60.0
    minimum_attempts: int = 3
    passing_score: float = 70.0


DEFAULT_POLICY = ProgressionPolicy()


def concept_is_complete(concept, records=None, policy: ProgressionPolicy = DEFAULT_POLICY) -> bool:
    """Return whether there is enough evidence to advance from a concept."""
    if concept is None:
        return False

    mastery = float(getattr(concept, "mastery", 0.0) or 0.0)
    confidence = float(getattr(concept, "confidence", 0.0) or 0.0)
    attempts = int(getattr(concept, "attempts", 0) or 0)
    last_score = getattr(concept, "last_score", None)

    if not (
        mastery >= policy.completion_mastery
        and confidence >= policy.completion_confidence
        and attempts >= policy.minimum_attempts
        and last_score is not None
        and float(last_score) >= policy.passing_score
    ):
        return False

    # When learning records are available, require at least one successful
    # challenge/application turn before calling a concept complete. This gives
    # the learner a meaningful "boss" without forcing a fixed number of tasks.
    if records is not None:
        concept_name = getattr(concept, "name", None)
        challenge_seen = any(
            getattr(record, "concept", None) == concept_name
            and str(getattr(record, "intervention_type", "")).lower() == "challenge"
            and bool(getattr(record, "completed", False))
            for record in records
        )
        if not challenge_seen:
            return False

    return True


def concept_level(concept, records=None, policy: ProgressionPolicy = DEFAULT_POLICY) -> int:
    """Map evidence to a compact five-stage learner-facing level."""
    mastery = float(getattr(concept, "mastery", 0.0) or 0.0)
    attempts = int(getattr(concept, "attempts", 0) or 0)
    if concept_is_complete(concept, records, policy):
        return 5
    if mastery >= 75:
        return 4
    if mastery >= 55:
        return 3
    if mastery >= 30:
        return 2
    if attempts > 0:
        return 1
    return 0


def concept_stage(concept, records=None, policy: ProgressionPolicy = DEFAULT_POLICY) -> str:
    level = concept_level(concept, records, policy)
    return {
        0: "unstarted",
        1: "foundation",
        2: "practice",
        3: "application",
        4: "challenge",
        5: "complete",
    }[level]


def track_progress(graph, concepts, records=None, policy: ProgressionPolicy = DEFAULT_POLICY) -> dict:
    """Build progress for every syllabus node, including unstarted concepts."""
    concept_lookup = {getattr(c, "name", ""): c for c in concepts or []}
    rows = []
    completed = 0
    mastered_values = []

    for name, prerequisites in graph.items():
        concept = concept_lookup.get(name)
        mastery = float(getattr(concept, "mastery", 0.0) or 0.0) if concept else 0.0
        is_complete = concept_is_complete(concept, records, policy)
        if is_complete:
            completed += 1
        if concept is not None and int(getattr(concept, "attempts", 0) or 0) > 0:
            mastered_values.append(mastery)
        rows.append({
            "concept": name,
            "mastery": round(mastery, 2),
            "level": concept_level(concept, records, policy),
            "stage": concept_stage(concept, records, policy),
            "completed": is_complete,
            "attempts": int(getattr(concept, "attempts", 0) or 0) if concept else 0,
            "confidence": round(float(getattr(concept, "confidence", 0.0) or 0.0), 2) if concept else 0.0,
            "prerequisites": list(prerequisites or []),
        })

    return {
        "total_concepts": len(graph),
        "completed_concepts": completed,
        "completion_percent": round((completed / len(graph)) * 100, 1) if graph else 0.0,
        "average_observed_mastery": round(sum(mastered_values) / len(mastered_values), 1) if mastered_values else 0.0,
        "concepts": rows,
    }
