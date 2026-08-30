import json
import sqlite3
from datetime import datetime, timezone


class SiftDatabase:

    def __init__(
        self,
        db_path="database/sift.db"
    ):
        self.db_path = db_path
        self._initialize_database()

    # ============================================================
    # CONNECTION
    # ============================================================

    def _connect(self):

        connection = sqlite3.connect(
            self.db_path,
            timeout=10.0,
        )

        connection.row_factory = sqlite3.Row

        # SQLite is used as the local source of truth. WAL allows
        # readers to continue while a writer is committing, while
        # busy_timeout gives short concurrent writes time to finish
        # instead of failing immediately with "database is locked".
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = NORMAL")

        return connection

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def _initialize_database(self):

        connection = self._connect()

        try:

            cursor = connection.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS learners (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    name TEXT NOT NULL,
                    goal TEXT,
                    learning_purpose TEXT DEFAULT 'Coursework',
                    subject TEXT,

                    available_minutes INTEGER DEFAULT 30,
                    current_level TEXT,
                    target_days INTEGER,
                    focus_concept TEXT,

                    preferred_strategies TEXT DEFAULT '{}',
                    mistake_patterns TEXT DEFAULT '{}',
                    concept_history TEXT DEFAULT '{}',
                    learning_records TEXT DEFAULT '[]',

                    time_accuracy TEXT DEFAULT
                    '{"estimated_minutes": 0,
                     "actual_minutes": 0}',

                    activity_streak TEXT DEFAULT
                    '{"current": 0, "longest": 0, "total_active_days": 0, "last_activity_date": null}',

                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,

                    UNIQUE(name, subject)
                )
                """
            )

            self._ensure_column(
                cursor,
                "preferred_strategies",
                "TEXT DEFAULT '{}'"
            )

            self._ensure_column(
                cursor,
                "mistake_patterns",
                "TEXT DEFAULT '{}'"
            )

            self._ensure_column(
                cursor,
                "concept_history",
                "TEXT DEFAULT '{}'"
            )

            self._ensure_column(
                cursor,
                "learning_records",
                "TEXT DEFAULT '[]'"
            )

            self._ensure_column(
                cursor,
                "time_accuracy",
                (
                    "TEXT DEFAULT "
                    "'{\"estimated_minutes\": 0, "
                    "\"actual_minutes\": 0}'"
                )
            )

            self._ensure_column(
                cursor,
                "activity_streak",
                (
                    "TEXT DEFAULT "
                    "\'{\"current\": 0, \"longest\": 0, \"total_active_days\": 0, \"last_activity_date\": null}\'"
                )
            )

            self._ensure_column(cursor, "focus_concept", "TEXT")
            self._ensure_column(cursor, "learning_purpose", "TEXT DEFAULT 'Coursework'")
            self._ensure_column(cursor, "custom_topics", "TEXT DEFAULT '[]'")
            # ====================================================
            # CONCEPTS
            # ====================================================

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS concepts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    learner_id INTEGER NOT NULL,
                    name TEXT NOT NULL,

                    mastery REAL DEFAULT 0,
                    attempts INTEGER DEFAULT 0,
                    correct_attempts INTEGER DEFAULT 0,

                    mistakes TEXT DEFAULT '[]',
                    mistake_types TEXT DEFAULT '{}',

                    last_seen TEXT,

                    confidence REAL DEFAULT 0,
                    last_score REAL DEFAULT 0,

                    review_count INTEGER DEFAULT 0,
                    successful_reviews INTEGER DEFAULT 0,

                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,

                    UNIQUE(learner_id, name),

                    FOREIGN KEY (learner_id)
                    REFERENCES learners(id)
                    ON DELETE CASCADE
                )
                """
            )

            # ====================================================
            # ASSESSMENTS
            # ====================================================

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS assessments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    learner_id INTEGER NOT NULL,
                    concept TEXT NOT NULL,

                    score REAL,
                    correct INTEGER,

                    mistake_type TEXT,
                    misconception TEXT,

                    confidence REAL,
                    explanation TEXT,
                    next_concept TEXT,
                    question TEXT,
                    answer TEXT,

                    created_at TEXT NOT NULL,

                    FOREIGN KEY (learner_id)
                    REFERENCES learners(id)
                    ON DELETE CASCADE
                )
                """
            )

            # ====================================================
            # INTERVENTIONS
            # ====================================================

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS interventions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    learner_id INTEGER NOT NULL,
                    concept TEXT NOT NULL,

                    strategy TEXT,
                    action TEXT,

                    title TEXT,
                    explanation TEXT,
                    task TEXT,

                    completed INTEGER DEFAULT 0,

                    created_at TEXT NOT NULL,

                    FOREIGN KEY (learner_id)
                    REFERENCES learners(id)
                    ON DELETE CASCADE
                )
                """
            )

            # ====================================================
            # LEARNING EVENTS
            # ====================================================

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS learning_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    learner_id INTEGER NOT NULL,
                    concept TEXT NOT NULL,

                    strategy TEXT,
                    intervention_type TEXT,

                    pre_mastery REAL,
                    post_mastery REAL,
                    learning_gain REAL,
                    duration_seconds INTEGER DEFAULT 0,
                    question TEXT,
                    answer TEXT,
                    evaluation TEXT,

                    completed INTEGER DEFAULT 0,

                    created_at TEXT NOT NULL,

                    FOREIGN KEY (learner_id)
                    REFERENCES learners(id)
                    ON DELETE CASCADE
                )
                """
            )

            # ====================================================
            # STUDY SESSIONS
            # ====================================================

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS study_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    learner_id INTEGER NOT NULL,

                    available_minutes INTEGER,
                    planned_minutes INTEGER,
                    actual_minutes INTEGER DEFAULT 0,

                    status TEXT DEFAULT 'planned',

                    created_at TEXT NOT NULL,
                    completed_at TEXT,

                    FOREIGN KEY (learner_id)
                    REFERENCES learners(id)
                    ON DELETE CASCADE
                )
                """
            )

            self._ensure_table_column(cursor, "study_sessions", "subject", "TEXT")
            self._ensure_table_column(cursor, "study_sessions", "topic", "TEXT")
            self._ensure_table_column(cursor, "study_sessions", "session_goal", "TEXT")
            self._ensure_table_column(cursor, "study_sessions", "teaching_style", "TEXT DEFAULT 'Adaptive'")
            self._ensure_table_column(cursor, "study_sessions", "starting_point", "TEXT DEFAULT 'Let Sift assess me'")
            self._ensure_table_column(cursor, "study_sessions", "time_cap", "INTEGER")
            self._ensure_table_column(cursor, "study_sessions", "updated_at", "TEXT")

            # ====================================================
            # SESSION TASKS
            # ====================================================

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS session_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    session_id INTEGER NOT NULL,

                    concept TEXT NOT NULL,
                    action TEXT,
                    strategy TEXT,

                    planned_minutes INTEGER,
                    actual_minutes INTEGER DEFAULT 0,

                    priority REAL,
                    completed INTEGER DEFAULT 0,

                    FOREIGN KEY (session_id)
                    REFERENCES study_sessions(id)
                    ON DELETE CASCADE
                )
                """
            )

            self._ensure_table_column(cursor, "assessments", "question", "TEXT")
            self._ensure_table_column(cursor, "assessments", "answer", "TEXT")
            self._ensure_table_column(cursor, "learning_events", "duration_seconds", "INTEGER DEFAULT 0")
            self._ensure_table_column(cursor, "learning_events", "question", "TEXT")
            self._ensure_table_column(cursor, "learning_events", "answer", "TEXT")
            self._ensure_table_column(cursor, "learning_events", "evaluation", "TEXT")

            connection.commit()

        finally:

            connection.close()

    # ====================================================
    # STUDY SESSION RECORDS
    # ====================================================

    def create_study_session(self, learner_id, subject, topic, session_goal=None,
                             available_minutes=30, teaching_style="Adaptive",
                             starting_point="Let Sift assess me"):
        now = self._now()
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(
                """INSERT INTO study_sessions
                (learner_id, subject, topic, session_goal, available_minutes, planned_minutes,
                 status, teaching_style, starting_point, time_cap, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?)""",
                (learner_id, subject, topic, session_goal, int(available_minutes or 30),
                 int(available_minutes or 30), teaching_style, starting_point,
                 int(available_minutes or 30), now, now),
            )
            connection.commit()
            return int(cursor.lastrowid)
        finally:
            connection.close()

    def list_study_sessions(self, learner_id):
        connection = self._connect()
        try:
            rows=connection.execute(
                "SELECT * FROM study_sessions WHERE learner_id=? ORDER BY COALESCE(updated_at, created_at) DESC, id DESC",
                (learner_id,),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    def update_study_session(self, session_id, **fields):
        allowed={"topic","session_goal","available_minutes","planned_minutes","actual_minutes",
                 "status","teaching_style","starting_point","time_cap","completed_at","updated_at"}
        updates={k:v for k,v in fields.items() if k in allowed}
        if not updates: return
        updates["updated_at"]=self._now()
        sql=", ".join(f"{k}=?" for k in updates)
        values=list(updates.values())+[session_id]
        connection=self._connect()
        try:
            connection.execute(f"UPDATE study_sessions SET {sql} WHERE id=?", values)
            connection.commit()
        finally:
            connection.close()


    # ============================================================
    # MIGRATION
    # ============================================================

    def _ensure_table_column(
        self,
        cursor,
        table_name,
        column_name,
        definition,
    ):
        columns = cursor.execute(
            f"PRAGMA table_info({table_name})"
        ).fetchall()
        existing = {row["name"] for row in columns}
        if column_name not in existing:
            cursor.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
            )

    def _ensure_column(
        self,
        cursor,
        column_name,
        definition
    ):

        columns = cursor.execute(
            """
            PRAGMA table_info(learners)
            """
        ).fetchall()

        existing = {
            row["name"]
            for row in columns
        }

        if column_name not in existing:

            cursor.execute(
                f"""
                ALTER TABLE learners
                ADD COLUMN {column_name}
                {definition}
                """
            )

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def _now():

        return datetime.now(
            timezone.utc
        ).isoformat()

    @staticmethod
    def _json(value):

        if value is None:
            value = {}

        return json.dumps(
            value
        )

    @staticmethod
    def _loads(
        value,
        default
    ):

        if not value:
            return default

        try:

            return json.loads(
                value
            )

        except (
            json.JSONDecodeError,
            TypeError
        ):

            return default

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

        existing = self._find_learner(
            name,
            subject
        )

        if existing:

            self.update_learner(
                existing["id"],
                goal=goal,
                learning_purpose=learning_purpose,
                available_minutes=available_minutes,
                current_level=current_level,
                target_days=target_days
            )

            return existing["id"]

        return self.create_learner(
            name=name,
            goal=goal,
            subject=subject,
            learning_purpose=learning_purpose,
            available_minutes=available_minutes,
            current_level=current_level,
            target_days=target_days
        )

    def _find_learner(
        self,
        name,
        subject
    ):

        connection = self._connect()

        try:

            row = connection.execute(
                """
                SELECT *
                FROM learners
                WHERE name = ?
                AND subject = ?
                LIMIT 1
                """,
                (
                    name,
                    subject
                )
            ).fetchone()

            if row is None:
                return None

            return self._learner_row(
                row
            )

        finally:

            connection.close()

    def create_learner(
        self,
        name,
        goal,
        subject,
        available_minutes=30,
        current_level="Beginner",
        target_days=30,
        learning_purpose="Coursework"
    ):

        now = self._now()

        connection = self._connect()

        try:

            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO learners (
                    name,
                    goal,
                    learning_purpose,
                    subject,
                    available_minutes,
                    current_level,
                    target_days,
                    preferred_strategies,
                    mistake_patterns,
                    concept_history,
                    learning_records,
                    time_accuracy,
                    created_at,
                    updated_at
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    name,
                    goal,
                    learning_purpose,
                    subject,
                    available_minutes,
                    current_level,
                    target_days,
                    "{}",
                    "{}",
                    "{}",
                    "[]",
                    (
                        '{"estimated_minutes": 0, '
                        '"actual_minutes": 0}'
                    ),
                    now,
                    now
                )
            )

            connection.commit()

            return cursor.lastrowid

        finally:

            connection.close()

    def list_learners_by_name(self, name):
        """Return all learner profiles belonging to a local user name."""
        name = str(name or "").strip()
        if not name:
            return []
        connection = self._connect()
        try:
            rows = connection.execute(
                "SELECT * FROM learners WHERE lower(name)=lower(?) ORDER BY updated_at DESC, id DESC",
                (name,),
            ).fetchall()
            return [self._learner_row(row) for row in rows]
        finally:
            connection.close()

    def get_learner(
        self,
        learner_id
    ):

        connection = self._connect()

        try:

            row = connection.execute(
                """
                SELECT *
                FROM learners
                WHERE id = ?
                """,
                (
                    learner_id,
                )
            ).fetchone()

            if row is None:
                return None

            return self._learner_row(
                row
            )

        finally:

            connection.close()

    def _learner_row(
        self,
        row
    ):

        data = dict(
            row
        )

        data["preferred_strategies"] = (
            self._loads(
                data.get(
                    "preferred_strategies"
                ),
                {}
            )
        )

        data["mistake_patterns"] = (
            self._loads(
                data.get(
                    "mistake_patterns"
                ),
                {}
            )
        )

        data["concept_history"] = (
            self._loads(
                data.get(
                    "concept_history"
                ),
                {}
            )
        )

        data["learning_records"] = (
            self._loads(
                data.get(
                    "learning_records"
                ),
                []
            )
        )

        data["time_accuracy"] = (
            self._loads(
                data.get(
                    "time_accuracy"
                ),
                {
                    "estimated_minutes": 0,
                    "actual_minutes": 0
                }
            )
        )

        data["custom_topics"] = self._loads(data.get("custom_topics"), [])

        data["activity_streak"] = self._loads(
            data.get("activity_streak"),
            {"current": 0, "longest": 0, "total_active_days": 0, "last_activity_date": None}
        )

        return data

    def update_learner(
        self,
        learner_id,
        **fields
    ):

        allowed = {
            "name",
            "goal",
            "learning_purpose",
            "subject",
            "available_minutes",
            "current_level",
            "target_days",
            "focus_concept",
            "custom_topics",
            "preferred_strategies",
            "mistake_patterns",
            "concept_history",
            "learning_records",
            "time_accuracy",
            "activity_streak"
        }

        updates = []
        values = []

        for field, value in fields.items():

            if field not in allowed:
                continue

            if field in {
                "preferred_strategies",
                "mistake_patterns",
                "concept_history",
                "learning_records",
                "time_accuracy",
                "activity_streak",
                "custom_topics"
            }:

                value = self._json(
                    value
                )

            updates.append(
                f"{field} = ?"
            )

            values.append(
                value
            )

        if not updates:
            return

        updates.append(
            "updated_at = ?"
        )

        values.append(
            self._now()
        )

        values.append(
            learner_id
        )

        connection = self._connect()

        try:

            connection.execute(
                f"""
                UPDATE learners
                SET {", ".join(updates)}
                WHERE id = ?
                """,
                values
            )

            connection.commit()

        finally:

            connection.close()

    def save_learner_state(
        self,
        learner_id,
        learner
    ):

        learning_records = []

        for record in (
            learner.learning_records
        ):

            if hasattr(
                record,
                "to_dict"
            ):

                learning_records.append(
                    record.to_dict()
                )

            elif isinstance(
                record,
                dict
            ):

                learning_records.append(
                    record
                )

            else:

                raise TypeError(
                    "Unsupported learning record "
                    f"type: {type(record)}"
                )

        self.update_learner(
            learner_id,

            name=learner.name,

            goal=learner.goal,

            learning_purpose=getattr(learner, "learning_purpose", "Coursework"),

            subject=learner.subject,

            available_minutes=(
                learner.available_minutes
            ),

            current_level=(
                learner.current_level
            ),

            target_days=(
                learner.target_days
            ),

            focus_concept=getattr(learner, "focus_concept", None),

            custom_topics=getattr(learner, "custom_topics", []),

            preferred_strategies=(
                learner.preferred_strategies
            ),

            mistake_patterns=(
                learner.mistake_patterns
            ),

            concept_history=(
                learner.concept_history
            ),

            learning_records=(
                learning_records
            ),

            time_accuracy=(
                learner.time_accuracy
            ),
            activity_streak=(
                learner.get_streak()
            )
        )

    # ============================================================
    # CONCEPTS
    # ============================================================

    def save_concept(
        self,
        learner_id,
        concept
    ):

        now = self._now()

        connection = self._connect()

        try:

            connection.execute(
                """
                INSERT INTO concepts (
                    learner_id,
                    name,
                    mastery,
                    attempts,
                    correct_attempts,
                    mistakes,
                    mistake_types,
                    last_seen,
                    confidence,
                    last_score,
                    review_count,
                    successful_reviews,
                    created_at,
                    updated_at
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?
                )

                ON CONFLICT(
                    learner_id,
                    name
                )
                DO UPDATE SET
                    mastery =
                        excluded.mastery,

                    attempts =
                        excluded.attempts,

                    correct_attempts =
                        excluded.correct_attempts,

                    mistakes =
                        excluded.mistakes,

                    mistake_types =
                        excluded.mistake_types,

                    last_seen =
                        excluded.last_seen,

                    confidence =
                        excluded.confidence,

                    last_score =
                        excluded.last_score,

                    review_count =
                        excluded.review_count,

                    successful_reviews =
                        excluded.successful_reviews,

                    updated_at =
                        excluded.updated_at
                """,
                (
                    learner_id,

                    concept.name,

                    concept.mastery,

                    concept.attempts,

                    concept.correct_attempts,

                    self._json(
                        concept.mistakes
                    ),

                    self._json(
                        concept.mistake_types
                    ),

                    getattr(
                        concept,
                        "last_seen",
                        None
                    ),

                    getattr(
                        concept,
                        "confidence",
                        0
                    ),

                    getattr(
                        concept,
                        "last_score",
                        0
                    ),

                    getattr(
                        concept,
                        "review_count",
                        0
                    ),

                    getattr(
                        concept,
                        "successful_reviews",
                        0
                    ),

                    now,

                    now
                )
            )

            connection.commit()

        finally:

            connection.close()

    def get_concept(
        self,
        learner_id,
        concept_name
    ):

        connection = self._connect()

        try:

            row = connection.execute(
                """
                SELECT *
                FROM concepts
                WHERE learner_id = ?
                AND name = ?
                """,
                (
                    learner_id,
                    concept_name
                )
            ).fetchone()

            if row is None:
                return None

            data = dict(
                row
            )

            data["mistakes"] = (
                self._loads(
                    data.get(
                        "mistakes"
                    ),
                    []
                )
            )

            data["mistake_types"] = (
                self._loads(
                    data.get(
                        "mistake_types"
                    ),
                    {}
                )
            )

            return data

        finally:

            connection.close()

    def get_all_concepts(
        self,
        learner_id
    ):

        connection = self._connect()

        try:

            rows = connection.execute(
                """
                SELECT *
                FROM concepts
                WHERE learner_id = ?
                ORDER BY mastery ASC
                """,
                (
                    learner_id,
                )
            ).fetchall()

            result = []

            for row in rows:

                data = dict(
                    row
                )

                data["mistakes"] = (
                    self._loads(
                        data.get(
                            "mistakes"
                        ),
                        []
                    )
                )

                data["mistake_types"] = (
                    self._loads(
                        data.get(
                            "mistake_types"
                        ),
                        {}
                    )
                )

                result.append(
                    data
                )

            return result

        finally:

            connection.close()

    # ============================================================
    # ASSESSMENTS
    # ============================================================

    def save_assessment(
        self,
        learner_id,
        assessment
    ):

        connection = self._connect()

        try:

            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO assessments (
                    learner_id,
                    concept,
                    score,
                    correct,
                    mistake_type,
                    misconception,
                    confidence,
                    explanation,
                    next_concept,
                    question,
                    answer,
                    created_at
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    learner_id,

                    assessment.get(
                        "concept"
                    ),

                    assessment.get(
                        "score"
                    ),

                    int(
                        bool(
                            assessment.get(
                                "correct",
                                False
                            )
                        )
                    ),

                    assessment.get(
                        "mistake_type"
                    ),

                    assessment.get(
                        "misconception"
                    ),

                    assessment.get(
                        "confidence"
                    ),

                    assessment.get(
                        "explanation"
                    ),

                    assessment.get(
                        "next_concept"
                    ),

                    assessment.get("question"),
                    assessment.get("answer"),

                    self._now()
                )
            )

            connection.commit()

            return cursor.lastrowid

        finally:

            connection.close()

    def get_recent_assessments(
        self,
        learner_id,
        limit=20
    ):

        connection = self._connect()

        try:

            rows = connection.execute(
                """
                SELECT *
                FROM assessments
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

    # ============================================================
    # INTERVENTIONS
    # ============================================================

    def save_intervention(
        self,
        learner_id,
        intervention,
        action=None,
        completed=False
    ):

        connection = self._connect()

        try:

            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO interventions (
                    learner_id,
                    concept,
                    strategy,
                    action,
                    title,
                    explanation,
                    task,
                    completed,
                    created_at
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    learner_id,

                    intervention.get(
                        "concept"
                    ),

                    intervention.get(
                        "strategy"
                    ),

                    action,

                    intervention.get(
                        "title"
                    ),

                    intervention.get(
                        "explanation"
                    ),

                    intervention.get(
                        "task"
                    ),

                    int(
                        completed
                    ),

                    self._now()
                )
            )

            connection.commit()

            return cursor.lastrowid

        finally:

            connection.close()
    # ============================================================
    # INTERVENTION COMPLETION
    # ============================================================
    def get_interventions(
        self,
        learner_id,
        limit=20
    ):
        """
        Return persisted interventions for a learner,
        newest first.
        """

        connection = self._connect()

        try:

            cursor = connection.cursor()

            cursor.execute(
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
            )

            rows = cursor.fetchall()

            return [
                dict(row)
                for row in rows
            ]

        finally:

            connection.close()
    def complete_intervention(
        self,
        intervention_id
    ):
        """
        Mark a persisted intervention/task as completed.

        Returns:
            True  - intervention existed and was updated.
            False - intervention did not exist.
        """

        connection = self._connect()

        try:

            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE interventions
                SET completed = 1
                WHERE id = ?
                """,
                (
                    intervention_id,
                )
            )

            connection.commit()

            return cursor.rowcount > 0

        finally:

            connection.close()


    # ============================================================
    # LEARNING EVENTS
    # ============================================================

    def save_learning_event(
        self,
        learner_id,
        record
    ):
        """
        Persist a LearningRecord.

        IMPORTANT:
        This method accepts BOTH:

            LearningRecord
            dict

        The LearningRecord is converted to a
        persistence-safe dictionary before SQLite
        operations begin.
        """

        # --------------------------------------------------------
        # Normalize LearningRecord -> dict
        # --------------------------------------------------------

        if hasattr(
            record,
            "to_dict"
        ):

            record = record.to_dict()

        elif isinstance(
            record,
            dict
        ):

            record = dict(
                record
            )

        else:

            raise TypeError(
                "Unsupported learning record type: "
                f"{type(record)}"
            )

        # --------------------------------------------------------
        # Persist event
        # --------------------------------------------------------

        connection = self._connect()

        try:

            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO learning_events (
                    learner_id,
                    concept,
                    strategy,
                    intervention_type,
                    pre_mastery,
                    post_mastery,
                    learning_gain,
                    duration_seconds,
                    question,
                    answer,
                    evaluation,
                    completed,
                    created_at
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    learner_id,

                    record.get(
                        "concept"
                    ),

                    record.get(
                        "strategy"
                    ),

                    record.get(
                        "intervention_type",
                        "teaching"
                    ),

                    record.get(
                        "pre_mastery"
                    ),

                    record.get(
                        "post_mastery"
                    ),

                    record.get(
                        "learning_gain"
                    ),

                    int(record.get("duration_seconds", 0) or 0),
                    record.get("question"),
                    record.get("answer"),
                    json.dumps(record.get("evaluation", {}), ensure_ascii=False),

                    int(
                        bool(
                            record.get(
                                "completed",
                                True
                            )
                        )
                    ),

                    record.get(
                        "created_at"
                    )
                    or self._now()
                )
            )

            connection.commit()

            return cursor.lastrowid

        finally:

            connection.close()

    def update_learning_event_evaluation(self, event_id, evaluation):
        """Update the persisted evaluation after the adaptive next-step decision."""
        if not event_id:
            return False
        connection = self._connect()
        try:
            cursor = connection.execute(
                "UPDATE learning_events SET evaluation=? WHERE id=?",
                (json.dumps(evaluation or {}, ensure_ascii=False), int(event_id)),
            )
            connection.commit()
            return cursor.rowcount > 0
        finally:
            connection.close()

    # ============================================================
    # STRATEGY EFFECTIVENESS
    # ============================================================

    def get_strategy_effectiveness(
        self,
        learner_id
    ):

        connection = self._connect()

        try:

            rows = connection.execute(
                """
                SELECT
                    strategy,
                    COUNT(*) AS attempts,

                    COALESCE(
                        SUM(learning_gain),
                        0
                    ) AS total_improvement,

                    COALESCE(
                        AVG(learning_gain),
                        0
                    ) AS average_improvement

                FROM learning_events

                WHERE learner_id = ?
                AND strategy IS NOT NULL

                GROUP BY strategy

                ORDER BY
                    average_improvement DESC
                """,
                (
                    learner_id,
                )
            ).fetchall()

            return [
                dict(row)
                for row in rows
            ]

        finally:

            connection.close()

    # ============================================================
    # LEARNER SUMMARY
    # ============================================================

    def get_learner_summary(
        self,
        learner_id
    ):

        return {
            "learner": self.get_learner(
                learner_id
            ),

            "concepts": (
                self.get_all_concepts(
                    learner_id
                )
            ),

            "recent_assessments": (
                self.get_recent_assessments(
                    learner_id,
                    10
                )
            ),

            "strategy_effectiveness": (
                self.get_strategy_effectiveness(
                    learner_id
                )
            )
        }
