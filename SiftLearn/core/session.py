from datetime import datetime, timezone

from core.knowledge_model import Concept
from core.adaptive_engine import AdaptiveEngine
from core.learner_model import LearningRecord

from ai.assessment import assess_answer, validate_assessment
from ai.teaching import generate_intervention


class SiftSession:
    # A single learning turn is capped so an abandoned tab cannot accrue
    # hours of fake learning time. The timer is evidence, not a target.
    MAX_LEARNING_TURN_SECONDS = 45 * 60

    """
    Coordinates one adaptive Sift learning session.

    Pipeline:

        assessment
            â†“
        knowledge update
            â†“
        mistake evidence
            â†“
        adaptive decision
            â†“
        intervention
            â†“
        reassessment
            â†“
        learning gain
            â†“
        strategy evidence
            â†“
        persistence
            â†“
        next decision
    """

    def __init__(
        self,
        learner,
        knowledge_graph,
        repository=None,
        learner_id=None
    ):
        self.learner = learner

        self.engine = AdaptiveEngine(
            knowledge_graph=knowledge_graph
        )

        self.repository = repository
        self.learner_id = learner_id

        self.concepts = {}

        self.active_intervention = None
        self.focus_concept = getattr(learner, "focus_concept", None)

        self.session_started_at = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )

        self.session_history = []

    # ============================================================
    # CONCEPTS
    # ============================================================

    def get_or_create_concept(
        self,
        name
    ):
        if not name:
            raise ValueError(
                "Concept name cannot be empty."
            )

        if name not in self.concepts:

            concept = None

            if (
                self.repository is not None
                and self.learner_id is not None
            ):
                concept = (
                    self.repository
                    .load_concept(
                        self.learner_id,
                        name
                    )
                )

            if concept is None:
                concept = Concept(
                    name
                )

            self.concepts[
                name
            ] = concept

        return self.concepts[
            name
        ]

    def load_persisted_concepts(self):

        if (
            self.repository is None
            or self.learner_id is None
        ):
            return []

        concepts = (
            self.repository
            .load_concepts(
                self.learner_id
            )
        )

        for concept in concepts:
            self.concepts[concept.name] = concept

        # Keep the complete registered syllabus available to the progression
        # engine/UI. Missing nodes are zero-evidence concepts; they are not
        # persisted until the learner actually demonstrates knowledge of them.
        # Restore learner-created topics as first-class graph nodes.
        # They have no forced prerequisite chain; Sift discovers the learner's actual gaps inside the topic instead of making a canned course.
        for topic in getattr(self.learner, "custom_topics", []) or []:
            topic = str(topic).strip()
            if topic:
                self.engine.knowledge_graph.add_concept(topic, [])
                if topic not in self.concepts:
                    self.concepts[topic] = Concept(topic)

        self._restore_active_dynamic_task()

        return list(self.concepts.values())

    def _restore_active_dynamic_task(self):
        """Restore an unfinished dynamic task after process restart."""
        if self.repository is None or self.learner_id is None:
            return None

        loader = getattr(
            self.repository,
            "load_active_dynamic_task",
            None,
        )
        if loader is None:
            return None

        item = loader(self.learner_id)
        if not item:
            return None

        task = item.get("task")
        if not isinstance(task, dict):
            return None

        concept_name = task.get("concept") or item.get("concept")
        if not concept_name:
            return None

        # Only restore tasks that belong to this subject's graph.
        if concept_name not in self.engine.knowledge_graph.graph:
            return None

        pre_mastery = task.get(
            "pre_mastery",
            self.get_or_create_concept(concept_name).mastery,
        )

        self.active_intervention = {
            "concept": concept_name,
            "strategy": task.get("strategy") or item.get("strategy"),
            "action": task.get("action") or item.get("action") or "teach",
            "target_concept": task.get("target_concept"),
            "diagnosis": task.get("diagnosis"),
            "pre_mastery": float(pre_mastery),
            "intervention": task,
            "started_at": task.get("started_at") or item.get("created_at"),
            "dynamic": True,
            "intervention_id": item.get("intervention_id"),
        }

        return self.active_intervention


    def _canonicalize_assessment_concept(
        self,
        assessment,
        question="",
    ):
        """
        Keep LLM assessment labels inside the registered subject graph.

        The assessment model is allowed to describe a concept naturally, but
        learner state must use one canonical graph node. This prevents valid
        answers such as "stack vs queue ordering principles" or "list vs
        tuple" from creating an unregistered concept and then failing the
        closed-loop validation gate.
        """
        graph = self.engine.knowledge_graph.graph
        reported = str(
            assessment.get("concept", "")
        ).strip()

        if not reported:
            return assessment

        def normalize(value):
            import re
            return re.sub(
                r"[^a-z0-9]+",
                " ",
                str(value).lower(),
            ).strip()

        normalized_reported = normalize(reported)

        # Dynamic tasks are scoped to the exact concept selected by the
        # adaptive engine. If this answer is for the active generated task,
        # the task target is authoritative even when the model uses a related
        # or mistaken natural-language label. This prevents fresh learners
        # from failing the validation boundary because they have no prior
        # evidence for an alternative concept label.
        active = self.active_intervention if isinstance(self.active_intervention, dict) else {}
        active_task = active.get("intervention") if isinstance(active.get("intervention"), dict) else {}
        active_question = str(active_task.get("question") or "").strip()
        active_concept = str(active.get("concept") or "").strip()
        if active.get("dynamic") and active_concept in graph and active_question and str(question).strip() == active_question:
            assessment["concept"] = active_concept
            return assessment

        # Canonicalize common multi-concept diagnostic labels before the
        # subject aliases. The assessment must still resolve to a node that
        # is actually registered in the learner graph.
        subject = str(getattr(self.learner, "subject", "")).strip()
        if subject == "Data Structures & Algorithms":
            multi_concept_aliases = (
                (("stack", "queue"), "Stacks"),
                (("queue", "stack"), "Queues"),
            )
            for terms, canonical in multi_concept_aliases:
                if canonical in graph and all(
                    normalize(term) in normalized_reported
                    for term in terms
                ):
                    assessment["concept"] = canonical
                    return assessment

        # 1. Exact/case-insensitive canonical match.
        for canonical in graph:
            if normalize(canonical) == normalized_reported:
                assessment["concept"] = canonical
                return assessment

        # 2. High-value subject-specific aliases for common diagnostic phrasing.

        alias_targets = {
            "Python": [
                (("modulo", "remainder", "%"), "modulo operator"),
                (("list", "lists"), "Lists"),
                (("dictionary", "dictionaries"), "Dictionaries"),
                (("call stack", "function call stack"), "Call Stack"),
                (("recursion", "recursive"), "Recursion"),
                (("condition", "if statement"), "Conditions"),
                (("loop", "for loop", "while loop"), "Loops"),
                (("function", "functions"), "Functions"),
                (("parameter", "parameters"), "Parameters"),
                (("class", "classes"), "Classes"),
                (("object oriented", "oop"), "OOP"),
            ],
            "Data Structures & Algorithms": [
                (("stack", "stacks"), "Stacks"),
                (("queue", "queues"), "Queues"),
                (("linked list", "linked lists"), "Linked Lists"),
                (("binary search tree", "bst"), "Binary Search Trees"),
                (("binary tree",), "Binary Trees"),
                (("binary search",), "Binary Search"),
                (("linear search",), "Linear Search"),
                (("sorting", "sort"), "Sorting"),
                (("array", "arrays"), "Arrays"),
                (("graph", "graphs"), "Graphs"),
                (("breadth first", "bfs"), "BFS"),
                (("depth first", "dfs"), "DFS"),
                (("recursion", "recursive"), "Recursion"),
                (("complexity", "big o"), "Complexity"),
            ],
            "Machine Learning": [
                (("overfitting",), "Overfitting"),
                (("regularization",), "Regularization"),
                (("cross validation",), "Cross Validation"),
                (("model evaluation", "test data", "training data"), "Model Evaluation"),
                (("classification",), "Classification"),
                (("regression",), "Regression"),
                (("supervised learning",), "Supervised Learning"),
                (("feature engineering",), "Feature Engineering"),
                (("data preparation", "data preprocessing"), "Data Preparation"),
                (("gradient descent",), "Gradient Descent"),
                (("loss function", "loss functions"), "Loss Functions"),
                (("neural network", "neural networks"), "Neural Networks"),
                (("backpropagation",), "Backpropagation"),
                (("statistics",), "Statistics"),
                (("probability",), "Probability"),
                (("linear algebra",), "Linear Algebra"),
            ],
            "Mathematics": [
                (("bayes", "bayes theorem"), "Bayes Theorem"),
                (("conditional probability",), "Conditional Probability"),
                (("probability",), "Probability"),
                (("derivative", "derivatives", "differentiation"), "Derivatives"),
                (("integral", "integrals", "integration"), "Integrals"),
                (("limit", "limits"), "Limits"),
                (("function", "functions"), "Functions"),
                (("equation", "equations"), "Equations"),
                (("algebra",), "Algebra"),
                (("arithmetic",), "Arithmetic"),
                (("matrix", "matrices"), "Matrices"),
                (("vector", "vectors"), "Vectors"),
                (("linear algebra",), "Linear Algebra"),
                (("number", "numbers"), "Numbers"),
            ],
        }

        # Match the reported concept first.
        reported_low = normalized_reported
        aliases = alias_targets.get(subject, [])

        for terms, canonical in aliases:
            if canonical not in graph:
                continue
            for term in terms:
                if normalize(term) in reported_low:
                    assessment["concept"] = canonical
                    return assessment

        # Match the question as a second source of truth. This is particularly
        # useful for multi-concept diagnostics such as "stack vs queue": the
        # first registered concept explicitly named by the diagnostic question
        # becomes the assessment anchor, while the other concept remains valid
        # context for the explanation.
        question_low = normalize(question)

        for terms, canonical in aliases:
            if canonical not in graph:
                continue
            for term in terms:
                if normalize(term) and normalize(term) in question_low:
                    assessment["concept"] = canonical
                    return assessment

        # 3. Generic graph-token overlap, but only when there is a clear hit.
        # Never invent a new concept.
        report_tokens = set(
            token
            for token in normalized_reported.split()
            if len(token) >= 3
        )

        question_tokens = set(
            token
            for token in question_low.split()
            if len(token) >= 3
        )

        best = None
        best_score = 0

        for canonical in graph:
            concept_tokens = set(
                token
                for token in normalize(canonical).split()
                if len(token) >= 3
            )

            score = (
                len(report_tokens & concept_tokens) * 3
                + len(question_tokens & concept_tokens)
            )

            if score > best_score:
                best_score = score
                best = canonical

        if best is not None and best_score >= 3:
            assessment["concept"] = best
            return assessment

        # A dynamic task is already scoped to one canonical concept. If the
        # assessor uses a natural-language label that cannot be resolved, keep
        # the evidence attached to that task's target instead of failing a
        # fresh learner on an otherwise valid answer. This is only a fallback
        # after all explicit graph/alias/question matching above has failed.
        active = self.active_intervention if isinstance(self.active_intervention, dict) else {}
        active_concept = str(active.get("concept") or self.focus_concept or "").strip()
        if active_concept in graph:
            assessment["concept"] = active_concept

        return assessment

    # ============================================================
    # ASSESSMENT
    # ============================================================

    def process_answer(
        self,
        subject,
        question,
        answer
    ):
        """
        Process one learner answer.

        This is an assessment event, not an
        intervention completion event.
        """

        assessment = assess_answer(
            subject=subject,
            question=question,
            answer=answer,
            fallback_concept=(
                self.focus_concept
                or (
                    self.active_intervention or {}
                ).get("concept", "")
            ),
        )

        assessment = self._canonicalize_assessment_concept(
            assessment,
            question=question,
        )

        self._validate_assessment(
            assessment
        )

        concept_name = (
            assessment["concept"]
        )

        concept = (
            self.get_or_create_concept(
                concept_name
            )
        )

        mistake_type = (
            self._normalize_mistake_type(
                assessment.get(
                    "mistake_type"
                )
            )
        )

        misconception = (
            assessment.get(
                "misconception"
            )
        )

        # --------------------------------------------------------
        # Update concept
        # --------------------------------------------------------

        concept.update(
            score=assessment["score"],
            mistake=(
                misconception
                if mistake_type != "none"
                else None
            ),
            mistake_type=mistake_type
        )

        # --------------------------------------------------------
        # IMPORTANT:
        # Only incorrect evidence counts as a
        # learner-level mistake.
        # --------------------------------------------------------

        if (
            not assessment.get(
                "correct",
                False
            )
            and mistake_type != "none"
        ):
            self.learner.record_mistake(
                mistake_type
            )

        # --------------------------------------------------------
        # Concept history
        # --------------------------------------------------------

        self.learner.record_concept_observation(
            concept_name=concept.name,
            score=assessment["score"],
            mastery=concept.mastery
        )

        # --------------------------------------------------------
        # Persistence
        # --------------------------------------------------------

        assessment["question"] = question
        assessment["answer"] = answer

        self._persist_assessment(
            assessment
        )

        self._persist_concept(
            concept
        )

        self._persist_learner()

        # --------------------------------------------------------
        # Adaptive decision
        # --------------------------------------------------------

        recommendation = (
            self.engine.recommend(
                learner=self.learner,
                concepts=list(
                    self.concepts.values()
                ),
                focus_concept=(self.focus_concept or concept_name)
            )
        )

        result = {
            "assessment": assessment,

            "concept": (
                concept.to_dict()
            ),

            "recommendation": (
                recommendation
            )
        }

        self.session_history.append(
            {
                "type": "assessment",
                "result": result
            }
        )

        return result

    # ============================================================
    # INTERVENTION
    # ============================================================

    def generate_next_intervention(
        self,
        subject,
        recommendation
    ):
        """
        Generate and remember the selected intervention.
        """

        if not recommendation:
            raise ValueError(
                "Recommendation is required."
            )

        if (
            recommendation.get(
                "action"
            )
            == "diagnostic"
        ):
            return None

        concept_name = (
            recommendation.get(
                "concept"
            )
        )

        strategy = (
            recommendation.get(
                "strategy"
            )
        )

        action = (
            recommendation.get(
                "action",
                "teach"
            )
        )

        if not concept_name:
            raise ValueError(
                "Recommendation has no concept."
            )

        concept = (
            self.get_or_create_concept(
                concept_name
            )
        )

        # Capture BEFORE intervention.
        pre_mastery = (
            concept.mastery
        )

        intervention = (
            generate_intervention(
                subject=subject,
                concept=concept_name,
                strategy=strategy,
                learner=self.learner
            )
        )

        self.active_intervention = {
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

            "pre_mastery": (
                pre_mastery
            ),

            "intervention": (
                intervention
            ),

            "started_at": (
                datetime.now(
                    timezone.utc
                ).isoformat()
            )
        }

        self._persist_intervention(
            intervention=intervention,
            action=action,
            completed=False
        )

        return intervention

    # ============================================================
    # COMPLETE INTERVENTION
    # ============================================================

    def complete_intervention(
        self,
        subject,
        question,
        answer
    ):
        """
        Reassess the learner after intervention.

        Crucially:

            correct reassessment
                != mistake

        It becomes positive evidence that the
        intervention worked.

        For dynamic interventions, the exact persisted
        intervention row is marked completed instead
        of creating a duplicate completed row.
        """

        if (
            self.active_intervention
            is None
        ):
            raise RuntimeError(
                "There is no active intervention."
            )

        active = (
            self.active_intervention
        )

        duration_seconds = 0
        started_at = active.get("started_at")
        if started_at:
            try:
                started = datetime.fromisoformat(str(started_at))
                if started.tzinfo is None:
                    started = started.replace(tzinfo=timezone.utc)
                duration_seconds = int(
                    max(0.0, (datetime.now(timezone.utc) - started).total_seconds())
                )
                duration_seconds = min(
                    duration_seconds,
                    self.MAX_LEARNING_TURN_SECONDS,
                )
            except (TypeError, ValueError):
                duration_seconds = 0

        assessment = assess_answer(
            subject=subject,
            question=question,
            answer=answer,
            fallback_concept=(
                active.get("concept", "")
                if isinstance(active, dict)
                else self.focus_concept
            ),
        )

        assessment = self._canonicalize_assessment_concept(
            assessment,
            question=question,
        )

        self._validate_assessment(
            assessment
        )

        concept = (
            self.get_or_create_concept(
                active["concept"]
            )
        )

        pre_mastery = (
            float(
                active["pre_mastery"]
            )
        )

        mistake_type = (
            self._normalize_mistake_type(
                assessment.get(
                    "mistake_type"
                )
            )
        )

        misconception = (
            assessment.get(
                "misconception"
            )
        )

        # --------------------------------------------------------
        # Update concept
        # --------------------------------------------------------

        concept.update(
            score=assessment["score"],
            mistake=(
                misconception
                if mistake_type != "none"
                else None
            ),
            mistake_type=mistake_type
        )

        post_mastery = (
            concept.mastery
        )

        learning_gain = round(
            post_mastery
            - pre_mastery,
            2
        )

        # --------------------------------------------------------
        # IMPORTANT:
        # Only an incorrect reassessment becomes
        # another learner mistake.
        # --------------------------------------------------------

        if (
            not assessment.get(
                "correct",
                False
            )
            and mistake_type != "none"
        ):
            self.learner.record_mistake(
                mistake_type
            )

        # --------------------------------------------------------
        # Concept history
        # --------------------------------------------------------

        self.learner.record_concept_observation(
            concept_name=concept.name,
            score=assessment["score"],
            mastery=concept.mastery
        )

        # --------------------------------------------------------
        # Canonical intervention type
        # --------------------------------------------------------

        intervention_type = (
            LearningRecord
            .normalize_intervention_type(
                active.get(
                    "action",
                    "teaching"
                )
            )
        )

        # --------------------------------------------------------
        # Learning record
        # --------------------------------------------------------

        record = LearningRecord(
            concept=active["concept"],

            strategy=active["strategy"],

            pre_mastery=pre_mastery,

            post_mastery=post_mastery,

            learning_gain=learning_gain,

            intervention_type=(
                intervention_type
            ),

            completed=True,

            created_at=(
                datetime.now(
                    timezone.utc
                ).isoformat()
            ),

            duration_seconds=duration_seconds,
            question=question,
            answer=answer,
            evaluation=assessment,
        )

        self.learner.record_learning(
            record
        )

        # --------------------------------------------------------
        # Persistence
        # --------------------------------------------------------

        assessment["question"] = question
        assessment["answer"] = answer

        self._persist_assessment(
            assessment
        )

        self._persist_concept(
            concept
        )

        learning_event_id = self._persist_learning_record(
            record
        )

        # --------------------------------------------------------
        # Dynamic intervention completion
        # --------------------------------------------------------
        #
        # Dynamic tasks already have a persisted database ID.
        #
        # Therefore:
        #
        #     UPDATE existing row
        #
        # rather than:
        #
        #     INSERT another intervention row.
        #
        # --------------------------------------------------------

        intervention_id = (
            active.get(
                "intervention_id"
            )
        )

        is_dynamic = (
            active.get(
                "dynamic",
                False
            )
        )

        if (
            is_dynamic
            and intervention_id is not None
        ):

            completed = (
                self.repository
                .complete_intervention(
                    intervention_id
                )
            )

            if not completed:
                raise RuntimeError(
                    "The persisted dynamic intervention "
                    f"{intervention_id} could not be marked "
                    "as completed."
                )

        else:

            # ----------------------------------------------------
            # Preserve existing behavior for non-dynamic
            # interventions.
            # ----------------------------------------------------

            self._persist_intervention(
                intervention=(
                    active["intervention"]
                ),
                action=(
                    active.get(
                        "action"
                    )
                ),
                completed=True
            )

        self._persist_learner()

        # --------------------------------------------------------
        # Strategy evidence
        # --------------------------------------------------------

        strategy_effectiveness = (
            self.learner
            .get_strategy_effectiveness(
                active["strategy"]
            )
        )

        # --------------------------------------------------------
        # Clear intervention. A focused path ends when its concept is complete.
        # --------------------------------------------------------

        self.active_intervention = None

        if self.focus_concept == concept.name:
            from core.progression import concept_is_complete
            if concept_is_complete(concept, self.learner.learning_records):
                self.clear_focus_concept()

        # --------------------------------------------------------
        # Decide next action
        # --------------------------------------------------------

        next_recommendation = (
            self.engine.recommend(
                learner=self.learner,
                concepts=list(
                    self.concepts.values()
                ),
                focus_concept=(
                    self.focus_concept
                    or assessment.get("next_concept")
                )
            )
        )

        # Store the adaptive decision with the learning record so History
        # can explain the closed loop instead of showing only a score.
        next_reason = ""
        if isinstance(next_recommendation, dict):
            next_reason = (
                next_recommendation.get("reason")
                or next_recommendation.get("diagnosis")
                or "Chosen from your latest evidence."
            )
        record.evaluation = dict(record.evaluation or {})
        record.evaluation["next_reason"] = next_reason
        record.evaluation["next_concept"] = (
            next_recommendation.get("concept")
            or next_recommendation.get("target_concept")
            if isinstance(next_recommendation, dict) else ""
        )
        # The learner JSON is the local longitudinal source of truth used by
        # the UI; update it after adding the adaptive reason.
        self._persist_learner()
        if learning_event_id is not None and self.repository is not None:
            try:
                self.repository.update_learning_event_evaluation(
                    learning_event_id, record.evaluation
                )
            except Exception:
                # History remains available from the learner snapshot even if
                # an older database schema/provider cannot update the event row.
                pass

        result = {
            "assessment": assessment,

            "concept": (
                concept.to_dict()
            ),

            "learning_record": (
                record.to_dict()
            ),

            "learning_gain": (
                learning_gain
            ),

            "strategy": (
                active["strategy"]
            ),

            "strategy_effectiveness": (
                strategy_effectiveness
            ),

            # Preserve the teaching material used for this turn so the UI
            # can explain what was taught and why the learner was rechecked.
            "intervention": dict(active.get("intervention", {}))
            if isinstance(active.get("intervention"), dict)
            else active.get("intervention"),

            "next_recommendation": (
                next_recommendation
            )
        }

        self.session_history.append(
            {
                "type": (
                    "intervention_completed"
                ),
                "result": result
            }
        )

        return result

    # ============================================================
    # ONE COMPLETE STEP
    # ============================================================

    def run_step(
        self,
        subject,
        question,
        answer
    ):
        """
        Run:

            answer
            â†“
            assessment
            â†“
            adaptive decision
            â†“
            intervention

        The intervention remains active until
        complete_intervention() is called.
        """

        result = (
            self.process_answer(
                subject=subject,
                question=question,
                answer=answer
            )
        )

        recommendation = (
            result[
                "recommendation"
            ]
        )

        intervention = (
            self.generate_next_intervention(
                subject=subject,
                recommendation=(
                    recommendation
                )
            )
        )

        result[
            "intervention"
        ] = intervention

        return result

    # ============================================================
    # VALIDATION
    # ============================================================

    def _validate_assessment(
        self,
        assessment
    ):
        """Validate assessment evidence before mutating learner state."""
        assessment = validate_assessment(assessment)

        concept_name = assessment["concept"]
        graph = self.engine.knowledge_graph.graph

        if concept_name not in graph:
            raise ValueError(
                f"Assessment concept '{concept_name}' is not part of "
                f"the learner's {self.learner.subject} knowledge graph."
            )

        next_concept = assessment.get("next_concept")
        if next_concept and next_concept not in graph:
            # The assessor may suggest a concept outside the current graph.
            # Do not allow that suggestion to silently become a new concept.
            assessment["next_concept"] = ""

        return assessment

    @staticmethod
    def _normalize_mistake_type(
        mistake_type
    ):
        if not mistake_type:
            return "none"

        value = str(
            mistake_type
        ).strip().lower()

        if value == "none":
            return "none"

        return value

    # ============================================================
    # PERSISTENCE
    # ============================================================

    def _persist_assessment(
        self,
        assessment
    ):
        if (
            self.repository is None
            or self.learner_id is None
        ):
            return

        self.repository.record_assessment(
            self.learner_id,
            assessment
        )

    def _persist_concept(
        self,
        concept
    ):
        if (
            self.repository is None
            or self.learner_id is None
        ):
            return

        self.repository.save_concept(
            self.learner_id,
            concept
        )

    def _persist_learner(self):
        if (
            self.repository is None
            or self.learner_id is None
        ):
            return

        self.repository.save_learner(
            self.learner_id,
            self.learner
        )

    def _persist_intervention(
        self,
        intervention,
        action=None,
        completed=False
    ):
        if (
            self.repository is None
            or self.learner_id is None
        ):
            return

        self.repository.record_intervention(
            learner_id=self.learner_id,
            intervention=intervention,
            action=action,
            completed=completed
        )

    def _persist_learning_record(
        self,
        record
    ):
        if (
            self.repository is None
            or self.learner_id is None
        ):
            return

        return self.repository.record_learning_event(
            self.learner_id,
            record
        )

    # ============================================================
    # USER-DIRECTED FOCUS
    # ============================================================

    def set_focus_concept(self, concept_name):
        if concept_name is None or not str(concept_name).strip():
            self.clear_focus_concept()
            return None

        concept_name = str(concept_name).strip()
        if concept_name not in self.engine.knowledge_graph.graph:
            # User-created topics are allowed. The graph remains authoritative
            # for built-in concepts while personal topics become zero-prereq nodes.
            self.engine.knowledge_graph.add_concept(concept_name, [])
            self.get_or_create_concept(concept_name)
            topics = list(getattr(self.learner, "custom_topics", []) or [])
            if concept_name not in topics:
                topics.append(concept_name)
                self.learner.custom_topics = topics[-50:]

        self.focus_concept = concept_name
        self.learner.focus_concept = concept_name
        self._persist_learner()
        return concept_name

    def clear_focus_concept(self):
        self.focus_concept = None
        self.learner.focus_concept = None
        self._persist_learner()

    # ============================================================
    # STATE
    # ============================================================

    def get_state(self):

        return {
            "learner": (
                self.learner.to_dict()
            ),

            "concepts": {
                name: concept.to_dict()
                for name, concept
                in self.concepts.items()
            },

            "active_intervention": (
                self.active_intervention
            ),

            "focus_concept": self.focus_concept,

            "session_started_at": (
                self.session_started_at
            ),

            "history_length": (
                len(
                    self.session_history
                )
            )
        }
