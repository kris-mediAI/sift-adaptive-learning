"""Compatibility import for the canonical LearningRecord.

The project keeps one LearningRecord implementation in core.learner_model.
This module preserves the historical import path without creating a second
subclass/type that can diverge from the canonical model.
"""

from core.learner_model import LearningRecord

__all__ = ["LearningRecord"]
