import json

from core.learner_model import (
    LearnerProfile,
    LearningRecord
)

from core.knowledge_model import Concept

from database.db import SiftDatabase


class SiftRepository:
    """
    Persistence boundary for Sift.

    Converts between:
        SQLite
        dictionaries
        domain objects

    Also provides persisted dynamic-task history so the
    content engine can avoid repeating tasks for a learner.
    """

    def __init__(
        self,
        database=None
    ):
        self.db = (
            database
            or SiftDatabase()
        )

    # ============================================================
    # LEARNER
    # ============================================================

    def get_or_create_learner(
        self,
        name,
        goal,
        subject,
        available_minutes=30,
        current_level="Beginner",
        target_days=30,
        learning_purpose="Coursework"
    ):
        """
        Create the learner if necessary and return:

            learner_id
            learner_profile

        SiftDatabase.get_or_create_learner()
        returns only the learner ID.

        The learner itself is then loaded separately.
        """

        learner_id = (
            self.db.get_or_create_learner(
                name=name,
                goal=goal,
                subject=subject,
                available_minutes=available_minutes,
                current_level=current_level,
                target_days=target_days,
                learning_purpose=learning_purpose
            )
        )

        data = self.db.get_learner(
            learner_id
        )

        if data is None:
            raise RuntimeError(
                "Learner was created/found but "
                "could not be loaded from the database."
            )

        learner = (
            self._learner_from_dict(
                data
            )
        )

        return (
            learner_id,
            learner
        )

    def list_learners_by_name(self, name):
        """Load every subject profile for the current local learner."""
        rows = self.db.list_learners_by_name(name)
        learners = []
        for row in rows:
            learner = self._learner_from_dict(row)
            # Keep the database identity available to UI/session discovery
            # without changing the public LearnerProfile model.
            learner._db_id = row.get("id")
            learners.append(learner)
        return learners

    def load_learner(
        self,
        learner_id
    ):
        data = self.db.get_learner(
            learner_id
        )

        if data is None:
            return None

        return (
            self._learner_from_dict(
                data
            )
        )

    def save_learner(
        self,
        learner_id,
        learner
    ):
        self.db.save_learner_state(
            learner_id,
            learner
        )

    # ============================================================
    # CONCEPTS
    # ============================================================

    def load_concept(
        self,
        learner_id,
        concept_name
    ):
        data = self.db.get_concept(
            learner_id,
            concept_name
        )

        if data is None:
            return None

        return (
            self._concept_from_dict(
                data
            )
        )

    def load_concepts(
        self,
        learner_id
    ):
        rows = self.db.get_all_concepts(
            learner_id
        )

        return [
            self._concept_from_dict(
                row
            )
            for row in rows
        ]

    def save_concept(
        self,
        learner_id,
        concept
    ):
        self.db.save_concept(
            learner_id,
            concept
        )

    # ============================================================
    # ASSESSMENTS
    # ============================================================

    def record_assessment(
        self,
        learner_id,
        assessment
    ):
        return self.db.save_assessment(
            learner_id,
            assessment
        )

    # ============================================================
    # INTERVENTIONS
    # ============================================================

    def record_intervention(
        self,
        learner_id,
        intervention,
        action=None,
        completed=False
    ):
        return self.db.save_intervention(
            learner_id=learner_id,
            intervention=intervention,
            action=action,
            completed=completed
        )

    def complete_intervention(
        self,
        intervention_id
    ):
        """
        Mark a persisted intervention/task as completed.

        Returns:
            True
                if the intervention existed and was updated.

            False
                if no intervention with the given ID exists.
        """

        return self.db.complete_intervention(
            intervention_id
        )

    # ============================================================
    # DYNAMIC TASK HISTORY
    # ============================================================

    def record_dynamic_task(
        self,
        learner_id,
        task_result
    ):
        """
        Persist a generated dynamic task.

        Dynamic tasks are stored inside the existing
        interventions table.

        IMPORTANT:
        SQLite cannot store a Python dict directly.

        Therefore the task is converted to JSON before
        being passed to database.save_intervention().
        """

        if not isinstance(
            task_result,
            dict
        ):
            raise TypeError(
                "task_result must be a dictionary."
            )

        task = task_result.get(
            "task"
        )

        spec = task_result.get(
            "spec",
            {}
        )

        if not isinstance(
            task,
            dict
        ):
            raise ValueError(
                "task_result does not contain "
                "a valid task dictionary."
            )

        if not isinstance(
            spec,
            dict
        ):
            spec = {}

        concept = (
            task.get(
                "concept"
            )
            or spec.get(
                "concept"
            )
        )

        strategy = (
            task.get(
                "strategy"
            )
            or spec.get(
                "strategy"
            )
        )

        action = (
            task.get(
                "action"
            )
            or spec.get(
                "action"
            )
        )

        if not concept:
            raise ValueError(
                "Dynamic task has no concept."
            )

        # --------------------------------------------------------
        # Convert task dictionary into SQLite-safe JSON.
        # --------------------------------------------------------

        task_json = json.dumps(
            task,
            ensure_ascii=False
        )

        stored_intervention = {
            "concept": concept,
            "strategy": strategy,
            "title": task.get(
                "title",
                ""
            ),
            "explanation": task.get(
                "context",
                ""
            ),
            "task": task_json
        }

        return self.record_intervention(
            learner_id=learner_id,
            intervention=stored_intervention,
            action=action,
            completed=False
        )

    def load_dynamic_task_history(
        self,
        learner_id,
        limit=20
    ):
        """
        Load previously generated dynamic tasks.

        Only structured dynamic tasks containing a
        question are returned.

        Older/non-dynamic interventions are ignored.

        The returned history includes the persisted
        completion state.
        """

        rows = []

        # --------------------------------------------------------
        # Preferred DB method
        # --------------------------------------------------------

        if hasattr(
            self.db,
            "get_interventions"
        ):
            try:
                rows = (
                    self.db.get_interventions(
                        learner_id=learner_id,
                        limit=limit
                    )
                )

            except TypeError:
                rows = (
                    self.db.get_interventions(
                        learner_id,
                        limit
                    )
                )

        # --------------------------------------------------------
        # Compatibility fallback
        # --------------------------------------------------------

        else:
            rows = (
                self._load_interventions_directly(
                    learner_id=learner_id,
                    limit=limit
                )
            )

        if rows is None:
            rows = []

        history = []

        for row in rows:

            if not isinstance(
                row,
                dict
            ):
                try:
                    row = dict(row)

                except (
                    TypeError,
                    ValueError
                ):
                    continue

            task_value = row.get(
                "task"
            )

            if not task_value:
                continue

            task = None

            # ----------------------------------------------------
            # Already decoded
            # ----------------------------------------------------

            if isinstance(
                task_value,
                dict
            ):
                task = task_value

            # ----------------------------------------------------
            # JSON string
            # ----------------------------------------------------

            elif isinstance(
                task_value,
                str
            ):

                try:

                    parsed = json.loads(
                        task_value
                    )

                    if isinstance(
                        parsed,
                        dict
                    ):
                        task = parsed

                except (
                    json.JSONDecodeError,
                    TypeError,
                    ValueError
                ):
                    task = None

            # ----------------------------------------------------
            # Invalid/old task
            # ----------------------------------------------------

            if not isinstance(
                task,
                dict
            ):
                continue

            # ----------------------------------------------------
            # Dynamic task identification
            # ----------------------------------------------------

            if not task.get(
                "question"
            ):
                continue

            normalized_task = dict(task)
            normalized_task.setdefault("concept", row.get("concept"))
            normalized_task.setdefault("strategy", row.get("strategy"))
            normalized_task.setdefault("action", row.get("action"))
            normalized_task.setdefault("title", row.get("title", ""))
            normalized_task.setdefault("context", row.get("explanation", ""))

            history.append(
                {
                    "intervention_id": row.get("id"),
                    "task": normalized_task,
                    "title": normalized_task.get("title", ""),

                    "question": task.get(
                        "question",
                        ""
                    ),

                    "context": task.get(
                        "context",
                        row.get(
                            "explanation",
                            ""
                        )
                    ),

                    "concept": task.get(
                        "concept",
                        row.get(
                            "concept"
                        )
                    ),

                    "strategy": task.get(
                        "strategy",
                        row.get(
                            "strategy"
                        )
                    ),

                    "action": task.get(
                        "action",
                        row.get(
                            "action"
                        )
                    ),

                    "difficulty": task.get(
                        "difficulty"
                    ),

                    "question_type": task.get(
                        "question_type"
                    ),

                    # ------------------------------------------------
                    # NEW:
                    # Preserve the database completion state.
                    #
                    # Existing old rows without this field are
                    # treated as incomplete.
                    # ------------------------------------------------
                    "completed": bool(
                        row.get(
                            "completed",
                            False
                        )
                    )
                }
            )

        # Database history is normally newest first.
        # ContentEngine receives chronological history.
        history.reverse()

        return history[
            -limit:
        ]

    def _load_interventions_directly(
        self,
        learner_id,
        limit=20
    ):
        """
        Compatibility fallback for databases that do not
        expose get_interventions().
        """

        connection = self.db._connect()

        try:

            rows = connection.execute(
                """
                SELECT
                    id,
                    learner_id,
                    concept,
                    strategy,
                    action,
                    title,
                    explanation,
                    task,
                    completed,
                    created_at
                FROM interventions
                WHERE learner_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (
                    learner_id,
                    limit
                )
            ).fetchall()

            return [
                dict(row)
                for row in rows
            ]

        finally:
            connection.close()

    def load_active_dynamic_task(
        self,
        learner_id,
    ):
        """Return the newest incomplete persisted dynamic task, if any."""
        history = self.load_dynamic_task_history(
            learner_id=learner_id,
            limit=50,
        )

        for item in reversed(history):
            if not item.get("completed", False):
                return item

        return None

    # ============================================================
    # LEARNING EVENTS
    # ============================================================

    def record_learning_event(
        self,
        learner_id,
        record
    ):
        return self.db.save_learning_event(
            learner_id,
            record
        )

    def update_learning_event_evaluation(self, event_id, evaluation):
        return self.db.update_learning_event_evaluation(event_id, evaluation)

    # ============================================================
    # STRATEGY DATA
    # ============================================================

    def strategy_effectiveness(
        self,
        learner_id
    ):
        return (
            self.db.get_strategy_effectiveness(
                learner_id
            )
        )

    # ============================================================
    # SUMMARY
    # ============================================================

    def get_summary(
        self,
        learner_id
    ):
        return self.db.get_learner_summary(
            learner_id
        )

    # ============================================================
    # LEARNER CONVERSION
    # ============================================================

    def _learner_from_dict(
        self,
        data
    ):
        learner = LearnerProfile(
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
            ),
            data.get("learning_purpose", "Coursework")
        )

        learner.focus_concept = data.get("focus_concept")
        learner.custom_topics = [
            str(item).strip() for item in (data.get("custom_topics") or [])
            if str(item).strip()
        ][:50]

        learner.preferred_strategies = dict(
            data.get(
                "preferred_strategies",
                {}
            )
        )

        learner.mistake_patterns = dict(
            data.get(
                "mistake_patterns",
                {}
            )
        )

        learner.concept_history = dict(
            data.get(
                "concept_history",
                {}
            )
        )

        learner.learning_records = []

        for record_data in data.get(
            "learning_records",
            []
        ):

            if isinstance(
                record_data,
                LearningRecord
            ):
                record = record_data

            else:
                record = (
                    LearningRecord.from_dict(
                        record_data
                    )
                )

            learner.learning_records.append(
                record
            )

        learner.time_accuracy = dict(
            data.get(
                "time_accuracy",
                {
                    "estimated_minutes": 0,
                    "actual_minutes": 0
                }
            )
        )

        learner.activity_streak = dict(
            data.get(
                "activity_streak",
                {"current": 0, "longest": 0, "total_active_days": 0, "last_activity_date": None}
            )
        )

        return learner

    # ============================================================
    # CONCEPT CONVERSION
    # ============================================================

    def _concept_from_dict(
        self,
        data
    ):
        concept = Concept(
            data["name"]
        )

        concept.mastery = float(
            data.get(
                "mastery",
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

        if hasattr(
            concept,
            "last_seen"
        ):
            concept.last_seen = data.get(
                "last_seen"
            )

        if hasattr(
            concept,
            "confidence"
        ):
            concept.confidence = float(
                data.get(
                    "confidence",
                    0
                )
            )

        if hasattr(
            concept,
            "last_score"
        ):
            concept.last_score = float(
                data.get(
                    "last_score",
                    0
                )
            )

        if hasattr(
            concept,
            "review_count"
        ):
            concept.review_count = int(
                data.get(
                    "review_count",
                    0
                )
            )

        if hasattr(
            concept,
            "successful_reviews"
        ):
            concept.successful_reviews = int(
                data.get(
                    "successful_reviews",
                    0
                )
            )

        return concept
