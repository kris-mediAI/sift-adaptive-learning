"""
Sift high-level orchestrator.

Application/UI code should communicate with this component
rather than directly coordinating the individual Sift
subsystems.

Core architecture:

    Repository
        â†“
    Learner
        â†“
    Knowledge State
        â†“
    Assessment
        â†“
    Adaptive Engine
        â†“
    Dynamic Content Engine
        â†“
    Gemini
        â†“
    Learning Session
        â†“
    Persistence

The Dynamic Content Engine is deliberately kept
at the orchestration layer for now. This lets us
integrate dynamic generation without destabilizing
the existing SiftSession implementation.
"""

from datetime import datetime, timezone

from core.knowledge_graph import KnowledgeGraph
from core.repository import SiftRepository
from core.session import SiftSession

from core.subject_graphs import (
    SUBJECT_GRAPHS as REGISTERED_SUBJECT_GRAPHS,
    SUPPORTED_SUBJECTS as REGISTERED_SUPPORTED_SUBJECTS,
)

from core.time_planner import TimeBudgetPlanner

from core.content_engine import (
    ContentEngine,
    ContentGenerationError,
    ContentValidationError,
)

from core.llm.gemini_provider import GeminiProvider
from core.resource_engine import ResourceEngine


class SiftOrchestrator:
    """
    High-level controller for Sift.

    Application/UI code should communicate with this
    component rather than directly coordinating the
    individual Sift subsystems.

    The orchestrator is intentionally thin.

    It coordinates existing Sift components without
    replacing their internal behavior.
    """

    # ============================================================
    # SUBJECT REGISTRY
    # ============================================================

    # Keep this as a class attribute because existing code/tests
    # may access:
    #
    #     SiftOrchestrator.SUBJECT_GRAPHS
    #
    # We source it from subject_graphs.py so there is only one
    # authoritative subject registry.
    SUBJECT_GRAPHS = REGISTERED_SUBJECT_GRAPHS

    SUPPORTED_SUBJECTS = REGISTERED_SUPPORTED_SUBJECTS

    def __init__(
        self,
        repository=None,
        content_engine=None,
        gemini_provider=None,
        resource_engine=None,
    ):
        self.repository = (
            repository
            or SiftRepository()
        )

        self.sessions = {}
        self.resource_engine = resource_engine or ResourceEngine()

        # --------------------------------------------------------
        # Dynamic content
        # --------------------------------------------------------

        # If a ContentEngine is explicitly supplied, use it.
        #
        # This is important for tests because the existing test
        # suite can inject a controlled/mock content engine.
        #
        # Production can simply use:
        #
        #     SiftOrchestrator()
        #
        # and receive the real Gemini-backed engine.

        if content_engine is not None:
            self.content_engine = (
                content_engine
            )

        else:
            if gemini_provider is None:
                gemini_provider = (
                    GeminiProvider()
                )

            self.content_engine = (
                ContentEngine(
                    model=gemini_provider,
                    strict=True,
                    # Keep the learner loop alive if the external model is
                    # temporarily unavailable. Fallback tasks remain subject
                    # to the same structural, concept and novelty validation.
                    allow_fallback=True,
                )
            )

    # ============================================================
    # SUBJECTS
    # ============================================================

    def get_supported_subjects(
        self,
    ):
        """
        Return the subjects currently supported by Sift.

        This method gives the UI a single backend source of
        truth instead of hard-coding a second subject list.
        """

        return list(
            self.SUPPORTED_SUBJECTS
        )

    def validate_subject(
        self,
        subject,
    ):
        """
        Validate that a subject has a registered knowledge graph.

        Raises:
            ValueError: if the subject is unsupported.
        """

        if not subject:
            raise ValueError(
                "Subject is required."
            )

        if subject not in self.SUBJECT_GRAPHS:
            supported = ", ".join(
                self.get_supported_subjects()
            )

            raise ValueError(
                f"Unsupported subject: {subject}. "
                f"Supported subjects: {supported}"
            )

        return True

    def get_subject_graph(
        self,
        subject,
    ):
        """
        Return the registered graph for a subject.

        A defensive copy is returned so callers cannot
        accidentally mutate the global subject registry.
        """

        self.validate_subject(
            subject
        )

        graph = (
            self.SUBJECT_GRAPHS[
                subject
            ]
        )

        return {
            concept: list(
                prerequisites
            )
            for concept, prerequisites
            in graph.items()
        }

    def get_subject_concepts(
        self,
        subject,
    ):
        """
        Return all concepts registered for a subject.
        """

        graph = self.get_subject_graph(
            subject
        )

        return list(
            graph.keys()
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
        learning_purpose="Coursework",
    ):
        """
        Get or create a learner using the existing repository
        behavior.

        Subject validation is performed before persistence so
        Sift cannot create a learner for a track that has no
        knowledge graph.
        """

        self.validate_subject(
            subject
        )

        learner_id, learner = (
            self.repository
            .get_or_create_learner(
                name=name,
                goal=goal,
                subject=subject,
                available_minutes=available_minutes,
                current_level=current_level,
                target_days=target_days,
                learning_purpose=learning_purpose,
            )
        )

        return (
            learner_id,
            learner,
        )

    # ============================================================
    # SESSION
    # ============================================================

    def create_session(
        self,
        learner_id,
        subject=None,
    ):
        """
        Create an adaptive session for a learner.

        Existing persisted concept state is restored through
        SiftSession.load_persisted_concepts().
        """

        learner = (
            self.repository
            .load_learner(
                learner_id
            )
        )

        if learner is None:
            raise ValueError(
                f"Learner {learner_id} does not exist."
            )

        subject = (
            subject
            or learner.subject
        )

        self.validate_subject(
            subject
        )

        graph_data = (
            self.get_subject_graph(
                subject
            )
        )

        graph = KnowledgeGraph(
            graph_data
        )

        session = SiftSession(
            learner=learner,
            knowledge_graph=graph,
            repository=self.repository,
            learner_id=learner_id,
        )

        # Preserve existing persistence behavior.
        session.load_persisted_concepts()

        self.sessions[
            learner_id
        ] = session

        return session

    def get_session(
        self,
        learner_id,
    ):
        """
        Return an active session.

        If one does not exist in memory, recreate it from
        the persisted learner state.
        """

        if learner_id not in self.sessions:
            return self.create_session(
                learner_id
            )

        return self.sessions[
            learner_id
        ]

    # ============================================================
    # STUDY PLAN
    # ============================================================

    def build_study_plan(
        self,
        learner_id,
        available_minutes=None,
    ):
        """
        Build a dependency-aware adaptive study plan.

        The existing TimeBudgetPlanner remains responsible for
        the planning logic.
        """

        session = self.get_session(
            learner_id
        )

        planner = TimeBudgetPlanner(
            session.engine
        )

        concepts = list(
            session.concepts.values()
        )

        if not concepts:
            return planner.build_plan(
                learner=session.learner,
                concepts=[],
                available_minutes=(
                    available_minutes
                ),
            )

        return planner.build_plan(
            learner=session.learner,
            concepts=concepts,
            available_minutes=(
                available_minutes
            ),
        )

    def update_study_plan(self, learner_id, available_minutes=None, target_days=None):
        """Persist planning preferences without changing learner evidence."""
        session = self.get_session(learner_id)
        if available_minutes is not None:
            minutes = max(10, min(240, int(available_minutes)))
            session.learner.available_minutes = minutes
        if target_days is not None:
            days = max(7, min(365, int(target_days)))
            session.learner.target_days = days
        session._persist_learner()
        return {
            "available_minutes": session.learner.available_minutes,
            "target_days": session.learner.target_days,
        }

    # ============================================================
    # USER-FACING STUDY SESSIONS
    # ============================================================

    def create_learning_session(self, learner_id, subject, topic, session_goal=None,
                                available_minutes=30, teaching_style="Adaptive",
                                starting_point="Let Sift assess me"):
        self.validate_subject(subject)
        topic=" ".join(str(topic or "").strip().split())
        if len(topic)<2: raise ValueError("Enter a topic or learning objective.")
        if len(topic)>100: raise ValueError("Topic is too long. Keep it under 100 characters.")
        # Defense in depth: the UI performs semantic/AI validation, but the
        # persistence boundary must never accept obvious non-topics either.
        from ai.topic_validator import VAGUE_INPUTS
        if topic.casefold() in VAGUE_INPUTS:
            raise ValueError("That is too vague to create a learning session. Choose a topic or describe what you want to learn.")
        self.create_custom_topic(learner_id, topic)
        sid=self.repository.db.create_study_session(learner_id,subject,topic,session_goal,available_minutes,teaching_style,starting_point)
        session=self.get_session(learner_id); session.set_focus_concept(topic)
        return sid

    def list_learning_sessions(self, learner_id):
        return self.repository.db.list_study_sessions(learner_id)

    def update_learning_session(self, session_id, **fields):
        return self.repository.db.update_study_session(session_id, **fields)

    # ============================================================
    # ASSESSMENT
    # ============================================================

    def assess(
        self,
        learner_id,
        question,
        answer,
    ):
        """
        Run one learner assessment.

        IMPORTANT:
        The existing SiftSession.process_answer() remains the
        owner of assessment â†’ knowledge update â†’ adaptive
        decision behavior.

        This method only provides the orchestration boundary.
        """

        session = self.get_session(
            learner_id
        )

        return session.process_answer(
            subject=session.learner.subject,
            question=question,
            answer=answer,
        )

    # ============================================================
    # DYNAMIC CONTENT
    # ============================================================

    def generate_dynamic_task(
        self,
        learner_id,
        recommendation,
    ):
        """
        Generate a completely new learning task from
        the current adaptive recommendation.

        Flow:

            Adaptive Engine
                â†“
            Dynamic Content Engine
                â†“
            Gemini
                â†“
            Validate Task
                â†“
            Persist Dynamic Task
                â†“
            Active Intervention
        """

        if not recommendation:
            raise ValueError(
                "A recommendation is required "
                "to generate a dynamic task."
            )

        session = self.get_session(
            learner_id
        )

        concept_name = (
            recommendation.get(
                "concept"
            )
        )

        if not concept_name:
            raise ValueError(
                "Adaptive recommendation does not "
                "contain a concept."
            )

        if concept_name not in session.engine.knowledge_graph.graph:
            raise ValueError(
                f"Concept '{concept_name}' "
                f"is not part of the learner's "
                f"{session.learner.subject} knowledge graph."
            )

        concept = session.get_or_create_concept(
            concept_name
        )

        # --------------------------------------------------------
        # Do not generate another task while one is active.
        # --------------------------------------------------------

        if (
            session.active_intervention
            is not None
        ):
            raise RuntimeError(
                "There is already an active intervention. "
                "Complete it before generating another task."
            )

        # --------------------------------------------------------
        # Generate dynamic content.
        # --------------------------------------------------------

        previous_tasks = (
            self.repository.load_dynamic_task_history(
                learner_id=learner_id,
                limit=50,
            )
        )

        try:
            result = (
                self.content_engine.generate(
                    learner=session.learner,
                    recommendation=recommendation,
                    concept=concept,
                    previous_tasks=previous_tasks,
                )
            )

        except (
            ContentGenerationError,
            ContentValidationError,
        ):
            raise

        if not isinstance(
            result,
            dict,
        ):
            raise RuntimeError(
                "ContentEngine returned an invalid result."
            )

        task = result.get(
            "task"
        )

        if not isinstance(
            task,
            dict,
        ):
            raise RuntimeError(
                "ContentEngine returned a result "
                "without a valid task."
            )

        if not task.get(
            "question"
        ):
            raise RuntimeError(
                "Generated dynamic task has no question."
            )

        # --------------------------------------------------------
        # Capture mastery BEFORE intervention.
        # --------------------------------------------------------

        pre_mastery = (
            concept.mastery
        )

        strategy = (
            task.get(
                "strategy"
            )
            or recommendation.get(
                "strategy"
            )
        )

        action = (
            task.get(
                "action"
            )
            or recommendation.get(
                "action",
                "teach",
            )
        )

        # --------------------------------------------------------
        # Ensure persisted task contains adaptive metadata.
        #
        # This makes the stored task self-contained.
        # --------------------------------------------------------

        persisted_task = dict(
            task
        )

        persisted_task.setdefault(
            "concept",
            concept_name,
        )

        persisted_task.setdefault(
            "strategy",
            strategy,
        )

        persisted_task.setdefault(
            "action",
            action,
        )
        persisted_task.setdefault(
            "target_concept",
            recommendation.get("target_concept"),
        )
        persisted_task.setdefault(
            "diagnosis",
            recommendation.get("diagnosis"),
        )
        persisted_task.setdefault(
            "pre_mastery",
            pre_mastery,
        )
        persisted_task.setdefault(
            "started_at",
            datetime.now(timezone.utc).isoformat(),
        )
        persisted_task["dynamic"] = True

        # --------------------------------------------------------
        # Build the existing persistence shape.
        # --------------------------------------------------------

        persistence_result = {
            "task": persisted_task,
            "spec": (
                result.get(
                    "spec",
                    {},
                )
            ),
        }

        # --------------------------------------------------------
        # Persist through the dedicated dynamic-task path.
        #
        # Do NOT use session._persist_intervention(task) here.
        # --------------------------------------------------------

        intervention_id = (
            self.repository.record_dynamic_task(
                learner_id=learner_id,
                task_result=persistence_result,
            )
        )

        # --------------------------------------------------------
        # Create active intervention.
        # --------------------------------------------------------

        session.active_intervention = {
            "concept": concept_name,

            "strategy": strategy,

            "action": action,

            "target_concept": (
                recommendation.get(
                    "target_concept"
                )
            ),

            "diagnosis": (
                recommendation.get(
                    "diagnosis"
                )
            ),

            "pre_mastery": pre_mastery,

            "intervention": persisted_task,

            "started_at": (
                datetime.now(
                    timezone.utc
                ).isoformat()
            ),

            "dynamic": True,

            # Keep the database intervention ID so completion
            # can update the exact generated task.
            "intervention_id": intervention_id,
        }

        # Return the original ContentEngine result.
        return result

    # ============================================================
    # ASSESS + DYNAMIC TASK
    # ============================================================

    def assess_and_generate(
        self,
        learner_id,
        question,
        answer,
    ):
        """
        Complete one adaptive decision step.

        Flow:

            Student Answer
                â†“
            Assess
                â†“
            Adaptive Decision
                â†“
            Dynamic Task Generation

        This method does NOT complete the generated task.
        The learner still needs to answer it.
        """

        assessment = self.assess(
            learner_id=learner_id,
            question=question,
            answer=answer,
        )

        recommendation = (
            self._extract_recommendation(
                assessment
            )
        )

        if recommendation is None:
            raise RuntimeError(
                "Sift assessment completed, but "
                "no adaptive recommendation could "
                "be extracted."
            )

        dynamic_content = (
            self.generate_dynamic_task(
                learner_id=learner_id,
                recommendation=recommendation,
            )
        )

        return {
            "assessment": assessment,

            "recommendation": (
                recommendation
            ),

            "dynamic_content": (
                dynamic_content
            ),
        }

    # ============================================================
    # RECOMMENDATION EXTRACTION
    # ============================================================

    def _extract_recommendation(
        self,
        assessment_result,
    ):
        """
        Extract the Adaptive Engine recommendation from
        the existing session result.

        Supports the structures currently used by Sift
        without forcing a change to SiftSession.
        """

        if not isinstance(
            assessment_result,
            dict,
        ):
            return None

        # Most direct structure.
        for key in (
            "recommendation",
            "adaptive_decision",
            "decision",
        ):
            value = (
                assessment_result.get(
                    key
                )
            )

            if isinstance(
                value,
                dict,
            ):
                return value

        # Some Sift results may put the decision inside
        # a nested result/state/session object.
        for key in (
            "result",
            "state",
            "session",
        ):
            nested = (
                assessment_result.get(
                    key
                )
            )

            if isinstance(
                nested,
                dict,
            ):
                for recommendation_key in (
                    "recommendation",
                    "adaptive_decision",
                    "decision",
                ):
                    value = (
                        nested.get(
                            recommendation_key
                        )
                    )

                    if isinstance(
                        value,
                        dict,
                    ):
                        return value

        # If the result itself already looks like an
        # AdaptiveEngine recommendation, accept it.
        required_signals = {
            "action",
            "concept",
            "strategy",
        }

        if required_signals.issubset(
            assessment_result.keys()
        ):
            return assessment_result

        return None

    # ============================================================
    # INTERVENTION
    # ============================================================

    def generate_intervention(
        self,
        learner_id,
        recommendation,
    ):
        """
        Existing intervention pathway.

        Kept intact for backward compatibility.
        """

        session = self.get_session(
            learner_id
        )

        return session.generate_next_intervention(
            subject=session.learner.subject,
            recommendation=recommendation,
        )

    # ============================================================
    # COMPLETE INTERVENTION
    # ============================================================

    def complete_intervention(
        self,
        learner_id,
        question,
        answer,
    ):
        """
        Complete an existing intervention.

        Kept intact for backward compatibility.
        """

        session = self.get_session(
            learner_id
        )

        return session.complete_intervention(
            subject=session.learner.subject,
            question=question,
            answer=answer,
        )

    # ============================================================
    # DYNAMIC TASK COMPLETION
    # ============================================================

    def complete_dynamic_task(
        self,
        learner_id,
        question,
        answer,
    ):
        """
        Complete the currently active dynamic task.

        Reuses SiftSession.complete_intervention().

        This gives the dynamic task the same learning
        pipeline as the existing intervention system:

            Dynamic Task
                â†“
            Reassessment
                â†“
            Knowledge Update
                â†“
            Learning Gain
                â†“
            LearningRecord
                â†“
            Strategy Evidence
                â†“
            Persistence
                â†“
            Next Recommendation
        """

        session = self.get_session(
            learner_id
        )

        if (
            session.active_intervention
            is None
        ):
            raise RuntimeError(
                "There is no active dynamic task."
            )

        active = (
            session.active_intervention
        )

        if not active.get(
            "dynamic",
            False,
        ):
            raise RuntimeError(
                "The active intervention is not "
                "a dynamic task."
            )

        # --------------------------------------------------------
        # Make sure caller is answering the actual generated
        # question.
        # --------------------------------------------------------

        active_task = (
            active.get(
                "intervention",
                {},
            )
        )

        expected_question = (
            active_task.get(
                "question"
            )
            if isinstance(
                active_task,
                dict,
            )
            else None
        )

        if (
            expected_question
            and question != expected_question
        ):
            raise ValueError(
                "The submitted question does not "
                "match the active dynamic task."
            )

        return session.complete_intervention(
            subject=session.learner.subject,
            question=question,
            answer=answer,
        )

    # ============================================================
    # ONE COMPLETE LEARNING TURN
    # ============================================================

    def run(
        self,
        learner_id,
        question,
        answer,
    ):
        """
        Existing high-level Sift turn.

        Kept unchanged for backward compatibility.
        """

        session = self.get_session(
            learner_id
        )

        return session.run_step(
            subject=session.learner.subject,
            question=question,
            answer=answer,
        )

    # ============================================================
    # NEW CLOSED-LOOP TURN
    # ============================================================

    def run_dynamic(
        self,
        learner_id,
        question,
        answer,
    ):
        """
        New closed-loop adaptive turn.

        Flow:

            Existing learner answer
                â†“
            Assess
                â†“
            Adaptive decision
                â†“
            Dynamic Gemini task
                â†“
            Return to learner

        The returned dynamic task is NOT automatically
        answered or completed.

        The UI should display the task and collect the
        learner's response.

        Then call:

            complete_dynamic_task()
        """

        return self.assess_and_generate(
            learner_id=learner_id,
            question=question,
            answer=answer,
        )

    # ============================================================
    # RESOURCES
    # ============================================================

    def recommend_resources(
        self,
        learner_id,
        concept=None,
        recommendation=None,
        mistake_type=None,
        misconception=None,
    ):
        """Return contextual learning resources for the current concept."""
        session = self.get_session(learner_id)
        recommendation = recommendation or {}
        concept = concept or recommendation.get("concept")

        if not concept:
            raise ValueError("A concept is required for resource recommendations.")

        if concept not in session.concepts:
            raise ValueError(
                f"Concept '{concept}' is not loaded for learner {learner_id}."
            )

        return self.resource_engine.recommend(
            concept=concept,
            subject=session.learner.subject,
            learner_level=getattr(
                session.learner,
                "current_level",
                "Beginner",
            ),
            strategy=recommendation.get("strategy"),
            mistake_type=mistake_type,
            misconception=misconception,
        )

    # ============================================================
    # PERSONAL TOPICS
    # ============================================================

    def create_custom_topic(self, learner_id, topic):
        """Create or focus a learner-owned topic without requiring a preset syllabus node."""
        session = self.get_session(learner_id)
        topic = " ".join(str(topic or "").strip().split())
        if len(topic) < 2:
            raise ValueError("Topic must contain at least 2 characters.")
        if len(topic) > 100:
            raise ValueError("Topic is too long. Keep it under 100 characters.")

        session.engine.knowledge_graph.add_concept(topic, [])
        session.get_or_create_concept(topic)
        topics = list(getattr(session.learner, "custom_topics", []) or [])
        is_new = topic not in topics
        if is_new:
            topics.append(topic)
        session.learner.custom_topics = topics[-50:]
        session.set_focus_concept(topic)
        session._persist_learner()
        return {
            "topic": topic,
            "focus_concept": topic,
            "is_new": is_new,
        }

    # ============================================================
    # FOCUSED CONCEPT PATH
    # ============================================================

    def set_focus_concept(self, learner_id, concept):
        return self.get_session(learner_id).set_focus_concept(concept)

    def clear_focus_concept(self, learner_id):
        self.get_session(learner_id).clear_focus_concept()

    # ============================================================
    # STATE
    # ============================================================

    def get_state(
        self,
        learner_id,
    ):
        """
        Return current learner/session state.
        """

        session = self.get_session(
            learner_id
        )

        return session.get_state()

    def get_summary(
        self,
        learner_id,
    ):
        """
        Return persisted learner summary.
        """

        return (
            self.repository
            .db
            .get_learner_summary(
                learner_id
            )
        )

    # ============================================================
    # CONTENT ENGINE STATE
    # ============================================================

    def get_content_engine(
        self,
    ):
        """
        Expose the ContentEngine for UI/tests without exposing
        provider internals.
        """

        return self.content_engine
