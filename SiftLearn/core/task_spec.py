from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TaskSpec:
    """
    Structured specification for one Sift learning task.

    The Adaptive Engine decides WHAT the learner needs.
    TaskSpec describes that need precisely.
    The ContentEngine later turns it into actual content.
    """

    concept: str

    action: str

    strategy: str

    difficulty: str = "medium"

    objective: str = ""

    target_skill: str = ""

    question_type: str = "short_answer"

    misconception: Optional[str] = None

    target_concept: Optional[str] = None

    diagnosis: Optional[str] = None

    learner_goal: str = ""

    learner_level: str = "Beginner"

    mastery: float = 0.0

    confidence: float = 0.0

    novelty: str = "normal"

    context: str = ""

    constraints: List[str] = field(
        default_factory=list
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self):
        return {
            "concept": self.concept,

            "action": self.action,

            "strategy": self.strategy,

            "difficulty": self.difficulty,

            "objective": self.objective,

            "target_skill": self.target_skill,

            "question_type": self.question_type,

            "misconception": self.misconception,

            "target_concept": self.target_concept,

            "diagnosis": self.diagnosis,

            "learner_goal": self.learner_goal,

            "learner_level": self.learner_level,

            "mastery": round(
                self.mastery,
                2
            ),

            "confidence": round(
                self.confidence,
                2
            ),

            "novelty": self.novelty,

            "context": self.context,

            "constraints": list(
                self.constraints
            ),

            "metadata": dict(
                self.metadata
            )
        }

    @classmethod
    def from_dict(cls, data):
        if not isinstance(
            data,
            dict
        ):
            raise TypeError(
                "TaskSpec.from_dict() "
                "requires a dictionary."
            )

        return cls(
            concept=data.get(
                "concept",
                ""
            ),

            action=data.get(
                "action",
                "practice"
            ),

            strategy=data.get(
                "strategy",
                "worked_example"
            ),

            difficulty=data.get(
                "difficulty",
                "medium"
            ),

            objective=data.get(
                "objective",
                ""
            ),

            target_skill=data.get(
                "target_skill",
                ""
            ),

            question_type=data.get(
                "question_type",
                "short_answer"
            ),

            misconception=data.get(
                "misconception"
            ),

            target_concept=data.get(
                "target_concept"
            ),

            diagnosis=data.get(
                "diagnosis"
            ),

            learner_goal=data.get(
                "learner_goal",
                ""
            ),

            learner_level=data.get(
                "learner_level",
                "Beginner"
            ),

            mastery=float(
                data.get(
                    "mastery",
                    0
                )
            ),

            confidence=float(
                data.get(
                    "confidence",
                    0
                )
            ),

            novelty=data.get(
                "novelty",
                "normal"
            ),

            context=data.get(
                "context",
                ""
            ),

            constraints=list(
                data.get(
                    "constraints",
                    []
                )
            ),

            metadata=dict(
                data.get(
                    "metadata",
                    {}
                )
            )
        )