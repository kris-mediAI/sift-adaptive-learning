from datetime import datetime, timezone

from core.scoring import clamp_score, update_mastery


class Concept:
    """
    Sift's estimate of a learner's knowledge of one concept.

    Tracks:

        mastery
        evidence
        mistakes
        confidence
        retention/review state

    Important distinction:

        mastery
            = estimated knowledge level

        confidence
            = how certain Sift is about that estimate

    Neither is simply the latest assessment score.
    """

    def __init__(
        self,
        name,
        mastery=0.0
    ):
        self.name = name

        self.mastery = max(
            0.0,
            min(
                100.0,
                float(mastery)
            )
        )

        self.attempts = 0
        self.correct_attempts = 0

        self.mistakes = []
        self.mistake_types = {}

        self.last_seen = None
        self.last_score = None

        # Confidence in Sift's mastery estimate.
        self.confidence = 0.0

        self.review_count = 0
        self.successful_reviews = 0

    # ============================================================
    # UPDATE
    # ============================================================

    def update(
        self,
        score,
        mistake=None,
        mistake_type=None
    ):
        """
        Update the concept using new evidence.

        The latest score influences mastery,
        but does not replace the accumulated estimate.

        Correct answers:

            increase evidence

        Incorrect answers:

            add mistake evidence

        A correct answer never creates a mistake.
        """

        score = clamp_score(score)

        self.attempts += 1

        self.last_score = score

        if score >= 70:
            self.correct_attempts += 1

        # --------------------------------------------------------
        # Mastery
        # --------------------------------------------------------

        if self.attempts == 1:

            self.mastery = score

        else:

            # Recent evidence matters, but historical
            # evidence remains important.

            learning_rate = 0.40

            self.mastery = update_mastery(
                self.mastery,
                score,
                learning_rate=learning_rate,
            )

        self.mastery = max(
            0.0,
            min(
                100.0,
                self.mastery
            )
        )

        # --------------------------------------------------------
        # Mistake evidence
        # --------------------------------------------------------

        normalized_type = (
            str(
                mistake_type
            ).strip().lower()
            if mistake_type
            else "none"
        )

        # Only record a misconception when the
        # assessment actually says there is one.

        if (
            normalized_type != "none"
            and mistake
        ):
            mistake = str(
                mistake
            ).strip()

            if mistake:
                self.mistakes.append(
                    mistake
                )

                self.mistake_types[
                    normalized_type
                ] = (
                    self.mistake_types.get(
                        normalized_type,
                        0
                    )
                    + 1
                )

        # --------------------------------------------------------
        # Timestamp
        # --------------------------------------------------------

        self.last_seen = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )

        # --------------------------------------------------------
        # Confidence
        # --------------------------------------------------------

        self._update_confidence()

    # ============================================================
    # RETRIEVAL REVIEW
    # ============================================================

    def record_review(
        self,
        score
    ):
        """
        Record retrieval-practice evidence.

        A successful retrieval is evidence that the
        learner can recall the concept without fresh teaching.
        """

        self.review_count += 1

        if score >= 70:
            self.successful_reviews += 1

            self.update(
                score=score,
                mistake=None,
                mistake_type="none"
            )

        else:

            self.update(
                score=score,
                mistake="Retrieval failure",
                mistake_type="retrieval"
            )

    # ============================================================
    # CONFIDENCE
    # ============================================================

    def _update_confidence(self):
        """
        Estimate how much evidence Sift has for
        the current mastery estimate.

        Confidence is deliberately NOT student confidence.

        It increases with:

            repeated attempts
            successful retrieval reviews
        """

        attempt_evidence = min(
            self.attempts / 5,
            1.0
        )

        review_evidence = min(
            self.review_count / 3,
            1.0
        )

        self.confidence = (
            attempt_evidence * 70
            + review_evidence * 30
        )

        self.confidence = max(
            0.0,
            min(
                100.0,
                self.confidence
            )
        )

    # ============================================================
    # SERIALIZATION
    # ============================================================

    def to_dict(self):

        return {
            "name": self.name,

            "mastery": round(
                self.mastery,
                2
            ),

            "last_score": (
                self.last_score
            ),

            "confidence": round(
                self.confidence,
                2
            ),

            "attempts": (
                self.attempts
            ),

            "correct_attempts": (
                self.correct_attempts
            ),

            "mistakes": list(
                self.mistakes
            ),

            "mistake_types": dict(
                self.mistake_types
            ),

            "last_seen": (
                self.last_seen
            ),

            "review_count": (
                self.review_count
            ),

            "successful_reviews": (
                self.successful_reviews
            )
        }

    @classmethod
    def from_dict(
        cls,
        data
    ):
        """
        Reconstruct a Concept from persisted state.
        """

        concept = cls(
            name=data.get(
                "name",
                ""
            ),
            mastery=data.get(
                "mastery",
                0
            )
        )

        concept.last_score = (
            data.get(
                "last_score"
            )
        )

        concept.confidence = float(
            data.get(
                "confidence",
                0
            )
        )

        concept.attempts = int(
            data.get(
                "attempts",
                0
            )
        )

        concept.correct_attempts = int(
            data.get(
                "correct_attempts",
                0
            )
        )

        concept.mistakes = list(
            data.get(
                "mistakes",
                []
            )
        )

        concept.mistake_types = dict(
            data.get(
                "mistake_types",
                {}
            )
        )

        concept.last_seen = (
            data.get(
                "last_seen"
            )
        )

        concept.review_count = int(
            data.get(
                "review_count",
                0
            )
        )

        concept.successful_reviews = int(
            data.get(
                "successful_reviews",
                0
            )
        )

        return concept
