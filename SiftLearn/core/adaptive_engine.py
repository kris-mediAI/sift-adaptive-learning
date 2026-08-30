import math

from core.knowledge_graph import KnowledgeGraph
from core.retention import RetentionEngine
from core.progression import concept_is_complete


class AdaptiveEngine:
    """
    Sift's decision-making layer.

    Combines:

        learner profile
        concept mastery
        concept confidence
        mistake evidence
        prerequisite relationships
        retention
        strategy effectiveness
    """

    STRATEGIES = [
        "worked_example",
        "visual_explanation",
        "analogy",
        "socratic",
        "practice_first",
    ]

    def __init__(
        self,
        knowledge_graph=None,
        retention_engine=None
    ):
        self.knowledge_graph = (
            knowledge_graph
            or KnowledgeGraph()
        )

        self.retention_engine = (
            retention_engine
            or RetentionEngine()
        )

    # ============================================================
    # PUBLIC DECISION
    # ============================================================

    def recommend(
        self,
        learner,
        concepts,
        focus_concept=None
    ):
        """
        Decide what Sift should do next.

        Priority:

            1. prerequisite repair
            2. retention review
            3. teach
            4. practice
            5. challenge
        """

        if not concepts:
            return (
                self._diagnostic_recommendation()
            )

        concept_lookup = {
            concept.name: concept
            for concept in concepts
        }

        # --------------------------------------------------------
        # User-directed focus has priority over the initial diagnostic.
        # A learner may explicitly ask for a brand-new topic (for example,
        # an exam tomorrow), so Sift must be able to teach that topic before
        # it has any prior evidence for it. The first generated task becomes
        # the evidence-building step.
        # --------------------------------------------------------

        if (
            focus_concept
            and focus_concept in concept_lookup
            and not concept_is_complete(
                concept_lookup[focus_concept],
                getattr(learner, "learning_records", []),
            )
        ):
            target = concept_lookup[focus_concept]

        # A fresh session with no user-directed topic needs a diagnostic.
        elif not any(int(getattr(c, "attempts", 0) or 0) > 0 for c in concepts):
            return self._diagnostic_recommendation()

        else:
            candidates = []
            for concept in concepts:
                complete = concept_is_complete(concept, getattr(learner, "learning_records", []))

                if complete:
                    # Completed concepts return only when the retention model
                    # says retrieval practice is due. This preserves forward
                    # progress without allowing old concepts to disappear.
                    if self.retention_engine.needs_review(concept):
                        priority = (
                            self.retention_engine.review_priority(concept)
                            + 5.0
                        )
                        candidates.append((priority, concept))
                    continue

                priority = self._calculate_priority(learner, concept)
                candidates.append((priority, concept))

            # Prefer a concept whose prerequisites are satisfied. If none is
            # available because the graph/evidence is sparse, fall back to
            # the highest-priority concept rather than getting stuck.
            available = []
            for priority, concept in candidates:
                blockers = self.knowledge_graph.find_blockers(concept.name, concepts)
                if not blockers:
                    available.append((priority, concept))

            pool = available or candidates
            if not pool:
                # Everything is complete. Revisit the most retention-risky
                # concept so the syllabus never dead-ends.
                pool = [(
                    self._calculate_priority(learner, concept),
                    concept,
                ) for concept in concepts]

            pool.sort(key=lambda item: item[0], reverse=True)
            _, target = pool[0]

        # --------------------------------------------------------
        # Prerequisite blocker
        # --------------------------------------------------------

        diagnosis = (
            self.knowledge_graph
            .explain_dependency(
                target.name,
                concepts
            )
        )

        if diagnosis:

            blocker = concept_lookup[
                diagnosis["blocker"]
            ]

            action = (
                self._choose_action(
                    blocker
                )
            )

            strategy = (
                self._choose_strategy(
                    learner
                )
            )

            return {
                "action": action,

                "concept": blocker.name,

                "mastery": round(
                    blocker.mastery
                ),

                "confidence": round(
                    blocker.confidence,
                    2
                ),

                "priority": round(
                    self._calculate_priority(
                        learner,
                        blocker
                    ),
                    2
                ),

                "strategy": strategy,

                "target_concept": (
                    target.name
                ),

                "diagnosis": (
                    "prerequisite_blocker"
                ),

                "reason": (
                    f"{target.name} is weak, but "
                    f"{blocker.name} appears to be "
                    f"a prerequisite blocker. "
                    f"Sift recommends repairing "
                    f"{blocker.name} first."
                )
            }

        # --------------------------------------------------------
        # Retention
        # --------------------------------------------------------

        if self.retention_engine.needs_review(
            target
        ):

            retention = (
                self.retention_engine
                .predicted_retention(
                    target
                )
            )

            review_priority = (
                self.retention_engine
                .review_priority(
                    target
                )
            )

            return {
                "action": "review",

                "concept": target.name,

                "mastery": round(
                    target.mastery
                ),

                "confidence": round(
                    target.confidence,
                    2
                ),

                "priority": (
                    review_priority
                ),

                "strategy": (
                    "retrieval_practice"
                ),

                "target_concept": (
                    target.name
                ),

                "diagnosis": (
                    "retention_risk"
                ),

                "retention": (
                    retention
                ),

                "reason": (
                    f"{target.name} has "
                    f"{target.mastery:.0f}% estimated "
                    f"mastery, but its predicted "
                    f"retention has fallen to "
                    f"{retention:.0f}%. "
                    f"Sift recommends retrieval "
                    f"practice to reinforce the "
                    f"concept."
                )
            }

        # --------------------------------------------------------
        # Normal decision
        # --------------------------------------------------------

        action = (
            self._choose_action(
                target
            )
        )

        strategy = (
            self._choose_strategy(
                learner
            )
        )

        return {
            "action": action,

            "concept": target.name,

            "mastery": round(
                target.mastery
            ),

            "confidence": round(
                target.confidence,
                2
            ),

            "priority": round(
                self._calculate_priority(
                    learner,
                    target
                ),
                2
            ),

            "strategy": strategy,

            "target_concept": (
                target.name
            ),

            "diagnosis": (
                "direct_concept_gap"
            ),

            "reason": (
                self._build_reason(
                    target,
                    action,
                    strategy
                )
            )
        }

    # ============================================================
    # PRIORITY
    # ============================================================

    def _calculate_priority(
        self,
        learner,
        concept
    ):
        """
        Calculate urgency.

        Factors:

            weakness
            mistake evidence
            conceptual errors
            uncertainty
        """

        weakness = max(
            0.0,
            100
            - concept.mastery
        )

        mistake_pressure = min(
            len(
                concept.mistakes
            ) * 5,
            25
        )

        conceptual_errors = (
            concept.mistake_types.get(
                "conceptual",
                0
            )
        )

        conceptual_pressure = min(
            conceptual_errors * 8,
            30
        )

        uncertainty = max(
            0,
            20
            - (
                concept.attempts * 5
            )
        )

        priority = (
            weakness * 0.50
            + mistake_pressure * 0.15
            + conceptual_pressure * 0.25
            + uncertainty * 0.10
        )

        return priority

    # ============================================================
    # ACTION
    # ============================================================

    def _choose_action(
        self,
        concept
    ):
        """
        Decide intervention type from mastery.

        Mastery:

            <= 50  → teach
            < 75   → practice
            >= 75  → challenge
        """

        if concept.mastery <= 50:
            return "teach"

        if concept.mastery < 75:
            return "practice"

        return "challenge"

    # ============================================================
    # STRATEGY
    # ============================================================

    def _choose_strategy(
        self,
        learner
    ):
        """
        Select a strategy using
        exploration/exploitation.

        Observed learning gain is treated as
        evidence, not psychological preference.
        """

        evidence = (
            learner.preferred_strategies
        )

        # --------------------------------------------------------
        # Exploration
        # --------------------------------------------------------

        for strategy in self.STRATEGIES:

            if strategy not in evidence:
                return strategy

        # --------------------------------------------------------
        # Exploitation + exploration
        # --------------------------------------------------------

        best_strategy = None

        best_score = (
            float("-inf")
        )

        total_attempts = sum(
            int(
                data.get(
                    "attempts",
                    0
                )
            )
            for data in evidence.values()
            if isinstance(
                data,
                dict
            )
        )

        total_attempts = max(
            total_attempts,
            1
        )

        for strategy in (
            self.STRATEGIES
        ):

            data = evidence.get(
                strategy,
                {}
            )

            attempts = int(
                data.get(
                    "attempts",
                    0
                )
            )

            total_gain = float(
                data.get(
                    "total_improvement",
                    0
                )
            )

            if attempts <= 0:
                return strategy

            average_gain = (
                total_gain
                / attempts
            )

            exploration = math.sqrt(
                (
                    2
                    * math.log(
                        total_attempts
                    )
                )
                / attempts
            )

            score = (
                average_gain
                + exploration * 10
            )

            if score > best_score:

                best_score = score

                best_strategy = (
                    strategy
                )

        return (
            best_strategy
            or "worked_example"
        )

    # ============================================================
    # DIAGNOSTIC
    # ============================================================

    def _diagnostic_recommendation(
        self
    ):

        return {
            "action": "diagnostic",

            "concept": None,

            "mastery": None,

            "confidence": None,

            "priority": 100,

            "strategy": "diagnostic",

            "target_concept": None,

            "diagnosis": (
                "insufficient_evidence"
            ),

            "reason": (
                "Sift needs more evidence "
                "about your current knowledge "
                "before choosing a learning path."
            )
        }

    # ============================================================
    # REASON
    # ============================================================

    def _build_reason(
        self,
        concept,
        action,
        strategy
    ):

        if action == "teach":

            return (
                f"{concept.name} is currently at "
                f"{concept.mastery:.0f}% mastery. "
                f"Sift recommends teaching the "
                f"concept before moving to harder "
                f"material."
            )

        if action == "practice":

            return (
                f"{concept.name} is developing at "
                f"{concept.mastery:.0f}% mastery. "
                f"Sift recommends targeted practice "
                f"using a "
                f"{strategy.replace('_', ' ')}."
            )

        return (
            f"{concept.name} is relatively strong "
            f"at {concept.mastery:.0f}% mastery. "
            f"Sift recommends a harder challenge."
        )