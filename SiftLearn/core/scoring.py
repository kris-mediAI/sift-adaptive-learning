"""Canonical, dependency-free scoring helpers used by Sift."""


def clamp_score(value):
    """Return a finite numeric score constrained to 0..100."""
    try:
        score = float(value)
    except (TypeError, ValueError):
        raise ValueError("Score must be numeric.")
    if score != score or score in (float("inf"), float("-inf")):
        raise ValueError("Score must be finite.")
    return max(0.0, min(100.0, score))


def update_mastery(old_mastery, new_score, learning_rate=0.40):
    """Apply Sift's existing evidence update without changing its behavior."""
    old = clamp_score(old_mastery)
    score = clamp_score(new_score)
    rate = float(learning_rate)
    if not 0.0 < rate <= 1.0:
        raise ValueError("learning_rate must be in (0, 1].")
    return clamp_score(old * (1.0 - rate) + score * rate)
