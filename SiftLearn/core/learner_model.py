class LearningRecord:
    """
    Represents one completed learning intervention.

    LearningRecord is deliberately independent from
    the database.

    It can be converted to/from dictionaries
    for persistence.

    intervention_type is normalized to one of:

        teaching
        practice
        challenge
        review
    """

    VALID_INTERVENTION_TYPES = {
        "teaching",
        "practice",
        "challenge",
        "review",
    }

    INTERVENTION_ALIASES = {
        "teach": "teaching",
        "teaching": "teaching",
        "learn": "teaching",

        "practice": "practice",
        "practise": "practice",

        "challenge": "challenge",

        "review": "review",
        "retrieval": "review",
        "retrieval_practice": "review",
    }

    def __init__(
        self,
        concept,
        strategy,
        pre_mastery,
        post_mastery,
        learning_gain=None,
        intervention_type="teaching",
        completed=True,
        created_at=None,
        duration_seconds=0,
        question=None,
        answer=None,
        evaluation=None,
    ):
        self.concept = concept
        self.strategy = strategy

        self.pre_mastery = (
            self._normalize_number(
                pre_mastery
            )
        )

        self.post_mastery = (
            self._normalize_number(
                post_mastery
            )
        )

        if learning_gain is None and self.pre_mastery is not None and self.post_mastery is not None:
            learning_gain = self.post_mastery - self.pre_mastery

        self.learning_gain = (
            self._normalize_gain(
                learning_gain
            )
        )

        self.intervention_type = (
            self.normalize_intervention_type(
                intervention_type
            )
        )

        self.completed = bool(
            completed
        )

        self.created_at = created_at

        try:
            self.duration_seconds = max(0, int(duration_seconds or 0))
        except (TypeError, ValueError):
            self.duration_seconds = 0

        self.question = question
        self.answer = answer
        self.evaluation = dict(evaluation or {}) if isinstance(evaluation, dict) else {}

    # ============================================================
    # NORMALIZATION
    # ============================================================

    @classmethod
    def normalize_intervention_type(
        cls,
        value
    ):
        """
        Normalize historical aliases.

        Examples:

            teach -> teaching
            teaching -> teaching
            retrieval_practice -> review
        """

        if value is None:
            return "teaching"

        value = str(
            value
        ).strip().lower()

        return cls.INTERVENTION_ALIASES.get(
            value,
            "teaching"
        )

    @staticmethod
    def _normalize_number(
        value
    ):
        if value is None:
            return None

        try:
            return float(
                value
            )
        except (
            TypeError,
            ValueError
        ):
            return None

    @staticmethod
    def _normalize_gain(
        value
    ):
        if value is None:
            return None

        try:
            return round(
                float(value),
                2
            )
        except (
            TypeError,
            ValueError
        ):
            return None

    # ============================================================
    # VALIDATION
    # ============================================================

    def is_complete(self):
        """
        A learning record is complete only when
        both mastery states are known.
        """

        return (
            self.pre_mastery is not None
            and self.post_mastery is not None
            and self.completed
        )

    # ============================================================
    # SERIALIZATION
    # ============================================================

    def to_dict(self):
        """
        Convert to JSON-safe dictionary.
        """

        return {
            "concept": self.concept,

            "strategy": self.strategy,

            "pre_mastery": (
                self.pre_mastery
            ),

            "post_mastery": (
                self.post_mastery
            ),

            "learning_gain": (
                self.learning_gain
            ),

            "intervention_type": (
                self.intervention_type
            ),

            "completed": (
                self.completed
            ),

            "created_at": (
                self.created_at
            ),

            "duration_seconds": self.duration_seconds,
            "question": self.question,
            "answer": self.answer,
            "evaluation": dict(self.evaluation)
        }

    @classmethod
    def from_dict(
        cls,
        data
    ):
        """
        Reconstruct a LearningRecord from
        persisted JSON.

        This also repairs legacy intervention
        type names automatically.
        """

        if not isinstance(
            data,
            dict
        ):
            raise TypeError(
                "LearningRecord.from_dict() "
                "requires a dictionary."
            )

        return cls(
            concept=data.get(
                "concept"
            ),

            strategy=data.get(
                "strategy"
            ),

            pre_mastery=data.get(
                "pre_mastery"
            ),

            post_mastery=data.get(
                "post_mastery"
            ),

            learning_gain=data.get(
                "learning_gain"
            ),

            intervention_type=data.get(
                "intervention_type",
                "teaching"
            ),

            completed=data.get(
                "completed",
                True
            ),

            created_at=data.get(
                "created_at"
            ),

            duration_seconds=data.get(
                "duration_seconds",
                0,
            ),

            question=data.get(
                "question"
            ),

            answer=data.get(
                "answer"
            ),

            evaluation=data.get("evaluation", {}),
        )


class LearnerProfile:
    """
    Stores what Sift knows about an individual learner.

    This model deliberately separates:

        strategy evidence
        mistake patterns
        concept history
        learning records
        time accuracy
    """

    def __init__(
        self,
        name,
        goal,
        subject,
        available_minutes,
        current_level,
        target_days,
        learning_purpose="Coursework"
    ):
        self.name = name
        self.goal = goal
        self.subject = subject
        self.learning_purpose = learning_purpose or "Coursework"

        self.available_minutes = (
            int(available_minutes)
        )

        self.current_level = (
            current_level
        )

        self.target_days = (
            int(target_days)
        )

        # Optional user-directed short-term focus. This does not replace
        # the main syllabus or knowledge state.
        self.focus_concept = None

        # Learner-created topics. These are lightweight personal learning
        # destinations, not a second syllabus.
        self.custom_topics = []

        # ========================================================
        # STRATEGY EVIDENCE
        # ========================================================

        # This is NOT a claim about the learner's
        # psychological preference.
        #
        # It represents observed evidence about which
        # strategies have produced learning gains.

        self.preferred_strategies = {}

        # ========================================================
        # MISTAKE PATTERNS
        # ========================================================

        # Aggregate counts of actual incorrect
        # learning evidence.

        self.mistake_patterns = {}

        # ========================================================
        # CONCEPT HISTORY
        # ========================================================

        self.concept_history = {}

        # ========================================================
        # LEARNING RECORDS
        # ========================================================

        # IMPORTANT:
        # Always LearningRecord objects internally.

        self.learning_records = []

        # ========================================================
        # TIME ACCURACY
        # ========================================================

        self.time_accuracy = {
            "estimated_minutes": 0,
            "actual_minutes": 0
        }

        self.activity_streak = {
            "current": 0,
            "longest": 0,
            "total_active_days": 0,
            "last_activity_date": None,
        }

    # ============================================================
    # STREAKS
    # ============================================================

    def mark_learning_activity(
        self,
        activity_date=None,
        seconds=0,
        turn=False,
        concept=None,
    ):
        from datetime import datetime, timedelta

        if activity_date is None:
            activity_date = datetime.now().astimezone().date()

        today = activity_date.isoformat()
        state = dict(self.activity_streak or {})
        last = state.get("last_activity_date")

        current = int(state.get("current", 0) or 0)
        if last == today:
            pass
        else:
            current = 1
            if last:
                try:
                    last_date = datetime.fromisoformat(last).date()
                    if activity_date == last_date + timedelta(days=1):
                        current = int(state.get("current", 0) or 0) + 1
                except (TypeError, ValueError):
                    current = 1

            state["current"] = current
            state["longest"] = max(current, int(state.get("longest", 0) or 0))
            state["total_active_days"] = int(state.get("total_active_days", 0) or 0) + 1
            state["last_activity_date"] = today

        daily_minutes = dict(state.get("daily_minutes", {}) or {})
        daily_turns = dict(state.get("daily_turns", {}) or {})
        daily_concepts = dict(state.get("daily_concepts", {}) or {})

        minutes = max(0.0, float(seconds or 0) / 60.0)
        daily_minutes[today] = round(float(daily_minutes.get(today, 0) or 0) + minutes, 2)
        if turn:
            daily_turns[today] = int(daily_turns.get(today, 0) or 0) + 1
        if concept:
            names = list(daily_concepts.get(today, []) or [])
            if concept not in names:
                names.append(concept)
            daily_concepts[today] = names[-25:]

        # Keep local learner JSON bounded.
        keep = sorted(set(daily_minutes) | set(daily_turns) | set(daily_concepts))[-365:]
        state["daily_minutes"] = {k: daily_minutes.get(k, 0) for k in keep}
        state["daily_turns"] = {k: daily_turns.get(k, 0) for k in keep}
        state["daily_concepts"] = {k: daily_concepts.get(k, []) for k in keep}
        self.activity_streak = state
        return dict(state)

    def get_streak(self):
        from datetime import datetime, timedelta

        state = dict(self.activity_streak or {})
        state.setdefault("current", 0)
        state.setdefault("longest", 0)
        state.setdefault("total_active_days", 0)
        state.setdefault("last_activity_date", None)
        state.setdefault("daily_minutes", {})
        state.setdefault("daily_turns", {})
        state.setdefault("daily_concepts", {})

        last = state.get("last_activity_date")
        if last:
            try:
                last_date = datetime.fromisoformat(last).date()
                today = datetime.now().astimezone().date()
                if last_date < today - timedelta(days=1):
                    state["current"] = 0
            except (TypeError, ValueError):
                state["current"] = 0

        return state

    # ============================================================
    # STRATEGY EVIDENCE
    # ============================================================

    def record_strategy_result(
        self,
        strategy,
        improvement
    ):
        """
        Record observed effectiveness of a strategy.

        A strategy is evaluated by actual observed
        learning gain, not assumed preference.
        """

        if not strategy:
            return

        try:
            improvement = float(
                improvement
            )
        except (
            TypeError,
            ValueError
        ):
            return

        if strategy not in (
            self.preferred_strategies
        ):
            self.preferred_strategies[
                strategy
            ] = {
                "attempts": 0,
                "total_improvement": 0.0,
                "average_gain": 0.0
            }

        data = (
            self.preferred_strategies[
                strategy
            ]
        )

        attempts = int(
            data.get(
                "attempts",
                0
            )
        )

        total = float(
            data.get(
                "total_improvement",
                0
            )
        )

        attempts += 1
        total += improvement

        data["attempts"] = attempts
        data["total_improvement"] = (
            round(
                total,
                2
            )
        )

        data["average_gain"] = (
            round(
                total / attempts,
                2
            )
            if attempts
            else 0.0
        )

    def get_strategy_effectiveness(
        self,
        strategy
    ):
        """
        Return average observed learning gain.
        """

        data = (
            self.preferred_strategies.get(
                strategy
            )
        )

        if not data:
            return None

        attempts = int(
            data.get(
                "attempts",
                0
            )
        )

        if attempts <= 0:
            return None

        return round(
            float(
                data.get(
                    "total_improvement",
                    0
                )
            ) / attempts,
            2
        )

    # ============================================================
    # LEARNING RECORDS
    # ============================================================

    def record_learning(
        self,
        record
    ):
        """
        Store a completed learning intervention.

        Accepts:

            LearningRecord
            dictionary

        Dictionaries are reconstructed into the
        canonical LearningRecord class.
        """

        if isinstance(
            record,
            dict
        ):
            record = (
                LearningRecord.from_dict(
                    record
                )
            )

        if not isinstance(
            record,
            LearningRecord
        ):
            raise TypeError(
                "record must be a "
                "LearningRecord or dictionary"
            )

        self.learning_records.append(
            record
        )

        if record.completed:
            self.mark_learning_activity(
                seconds=getattr(record, "duration_seconds", 0),
                turn=True,
                concept=getattr(record, "concept", None),
            )
            self.record_time(
                estimated_minutes=0,
                actual_minutes=(
                    float(getattr(record, "duration_seconds", 0) or 0) / 60.0
                ),
            )

        gain = (
            record.learning_gain
        )

        if gain is not None:
            self.record_strategy_result(
                record.strategy,
                gain
            )

    # ============================================================
    # MISTAKES
    # ============================================================

    def record_mistake(
        self,
        mistake_type
    ):
        """
        Record one actual incorrect answer.

        IMPORTANT:
        The caller should only invoke this when
        mistake_type != 'none'.
        """

        if not mistake_type:
            return

        mistake_type = str(
            mistake_type
        ).strip().lower()

        if mistake_type == "none":
            return

        self.mistake_patterns[
            mistake_type
        ] = (
            self.mistake_patterns.get(
                mistake_type,
                0
            )
            + 1
        )

    # ============================================================
    # CONCEPT HISTORY
    # ============================================================

    def record_concept_observation(
        self,
        concept_name,
        score,
        mastery
    ):
        """
        Store a compact longitudinal history
        of concept performance.
        """

        if not concept_name:
            return

        try:
            score = float(
                score
            )
        except (
            TypeError,
            ValueError
        ):
            score = 0.0

        try:
            mastery = float(
                mastery
            )
        except (
            TypeError,
            ValueError
        ):
            mastery = 0.0

        history = (
            self.concept_history.setdefault(
                concept_name,
                {
                    "times_seen": 0,
                    "best_score": 0,
                    "current_mastery": 0
                }
            )
        )

        history[
            "times_seen"
        ] = int(
            history.get(
                "times_seen",
                0
            )
        ) + 1

        history[
            "best_score"
        ] = max(
            float(
                history.get(
                    "best_score",
                    0
                )
            ),
            score
        )

        history[
            "current_mastery"
        ] = round(
            mastery,
            2
        )

    # ============================================================
    # TIME
    # ============================================================

    def record_time(
        self,
        estimated_minutes,
        actual_minutes
    ):
        """
        Update time-estimation evidence.
        """

        try:
            estimated = float(
                estimated_minutes
            )
        except (
            TypeError,
            ValueError
        ):
            estimated = 0.0

        try:
            actual = float(
                actual_minutes
            )
        except (
            TypeError,
            ValueError
        ):
            actual = 0.0

        self.time_accuracy[
            "estimated_minutes"
        ] += estimated

        self.time_accuracy[
            "actual_minutes"
        ] += actual

    # ============================================================
    # SERIALIZATION
    # ============================================================

    def to_dict(self):
        """
        Convert the complete learner profile
        into JSON-friendly data.
        """

        return {
            "name": self.name,

            "goal": self.goal,

            "subject": self.subject,

            "available_minutes": (
                self.available_minutes
            ),

            "current_level": (
                self.current_level
            ),

            "target_days": (
                self.target_days
            ),

            "focus_concept": self.focus_concept,

            "custom_topics": list(self.custom_topics),

            "preferred_strategies": (
                self.preferred_strategies
            ),

            "mistake_patterns": (
                self.mistake_patterns
            ),

            "concept_history": (
                self.concept_history
            ),

            "learning_records": [
                record.to_dict()
                for record in (
                    self.learning_records
                )
            ],

            "time_accuracy": (
                self.time_accuracy
            ),
            "activity_streak": self.get_streak()
        }

    @classmethod
    def from_dict(
        cls,
        data
    ):
        """
        Reconstruct a complete LearnerProfile.

        Legacy dictionaries are accepted.
        Legacy LearningRecord intervention types
        are normalized automatically.
        """

        if not isinstance(
            data,
            dict
        ):
            raise TypeError(
                "LearnerProfile.from_dict() "
                "requires a dictionary."
            )

        learner = cls(
            data.get(
                "name",
                ""
            ),

            data.get(
                "goal",
                ""
            ),

            data.get(
                "subject",
                ""
            ),

            data.get(
                "available_minutes",
                30
            ),

            data.get(
                "current_level",
                "Beginner"
            ),

            data.get(
                "target_days",
                30
            )
        )

        learner.focus_concept = data.get("focus_concept")
        learner.custom_topics = [
            str(item).strip() for item in (data.get("custom_topics") or [])
            if str(item).strip()
        ][:50]

        learner.preferred_strategies = (
            dict(
                data.get(
                    "preferred_strategies",
                    {}
                )
            )
        )

        # Repair old strategy records that don't
        # have average_gain.

        for strategy, values in (
            learner.preferred_strategies.items()
        ):
            if not isinstance(
                values,
                dict
            ):
                learner.preferred_strategies[
                    strategy
                ] = {
                    "attempts": 0,
                    "total_improvement": 0.0,
                    "average_gain": 0.0
                }
                continue

            attempts = int(
                values.get(
                    "attempts",
                    0
                )
            )

            total = float(
                values.get(
                    "total_improvement",
                    0
                )
            )

            values["attempts"] = attempts
            values["total_improvement"] = (
                round(
                    total,
                    2
                )
            )

            values["average_gain"] = (
                round(
                    total / attempts,
                    2
                )
                if attempts
                else 0.0
            )

        learner.mistake_patterns = (
            dict(
                data.get(
                    "mistake_patterns",
                    {}
                )
            )
        )

        learner.concept_history = (
            dict(
                data.get(
                    "concept_history",
                    {}
                )
            )
        )

        learner.learning_records = []

        for record in data.get(
            "learning_records",
            []
        ):

            if isinstance(
                record,
                LearningRecord
            ):
                learner.learning_records.append(
                    record
                )

            elif isinstance(
                record,
                dict
            ):
                learner.learning_records.append(
                    LearningRecord.from_dict(
                        record
                    )
                )

        learner.time_accuracy = (
            dict(
                data.get(
                    "time_accuracy",
                    {
                        "estimated_minutes": 0,
                        "actual_minutes": 0
                    }
                )
            )
        )

        learner.activity_streak = dict(
            data.get(
                "activity_streak",
                {
                    "current": 0,
                    "longest": 0,
                    "total_active_days": 0,
                    "last_activity_date": None,
                }
            )
        )

        return learner
