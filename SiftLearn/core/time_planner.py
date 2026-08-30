from dataclasses import dataclass


@dataclass
class StudyTask:
    """One task inside a Sift study session."""

    concept: str
    action: str
    minutes: int
    priority: float
    reason: str
    prerequisites: list
    dependency_depth: int = 0
    critical: bool = False

    def to_dict(self):
        return {
            "concept": self.concept,
            "action": self.action,
            "minutes": self.minutes,
            "priority": round(self.priority, 2),
            "reason": self.reason,
            "prerequisites": self.prerequisites,
            "dependency_depth": self.dependency_depth,
            "critical": self.critical,
        }


class TimeBudgetPlanner:
    """
    Sift's dependency-aware, time-aware study planner.

    The planner combines:

    - learner mastery
    - prerequisite relationships
    - prerequisite satisfaction
    - prerequisite blockers
    - retention/review decisions
    - adaptive priority
    - available study time

    Important principle:

        A prerequisite that is already mastered does NOT
        need to consume study time.

    Example:

        Functions = 88%
        Call Stack = 30%
        Recursion = 40%

        Functions is a prerequisite of Call Stack,
        but Functions is already strong.

        Therefore:

            Functions prerequisite = SATISFIED

        and Sift can start with:

            Call Stack → Recursion
    """

    # Minimum meaningful task size.
    MIN_TASK_MINUTES = 3

    # Mastery at or above this level is considered
    # sufficient for prerequisite purposes.
    PREREQUISITE_MASTERY_THRESHOLD = 75

    def __init__(self, adaptive_engine):
        self.adaptive_engine = adaptive_engine

    # ============================================================
    # PUBLIC API
    # ============================================================

    def build_plan(
        self,
        learner,
        concepts,
        available_minutes=None
    ):
        """
        Build the best study plan that fits the learner's
        available time.
        """

        if available_minutes is None:
            available_minutes = (
                learner.available_minutes
            )

        available_minutes = max(
            0,
            int(available_minutes)
        )

        # --------------------------------------------------------
        # No available study time.
        # --------------------------------------------------------

        if available_minutes == 0:
            return {
                "total_minutes": 0,
                "available_minutes": 0,
                "tasks": [],
                "message": (
                    "No study time is available. "
                    "Sift will preserve the learner's "
                    "state for the next session."
                )
            }

        # --------------------------------------------------------
        # No concepts.
        # --------------------------------------------------------

        if not concepts:
            return {
                "total_minutes": 0,
                "available_minutes": available_minutes,
                "tasks": [],
                "message": (
                    "Sift needs more learning evidence "
                    "before creating a study plan."
                )
            }

        concept_lookup = {
            concept.name: concept
            for concept in concepts
        }

        candidates = []

        # ========================================================
        # 1. Generate adaptive decisions.
        # ========================================================

        for concept in concepts:

            recommendation = (
                self.adaptive_engine.recommend(
                    learner=learner,
                    concepts=concepts,
                    focus_concept=concept.name
                )
            )

            action = recommendation.get(
                "action"
            )

            # Diagnostic means we don't yet have enough
            # evidence to schedule normal learning.
            if action == "diagnostic":
                continue

            prerequisites = (
                self.adaptive_engine
                .knowledge_graph
                .get_prerequisites(
                    concept.name
                )
            )

            dependency_depth = (
                self._dependency_depth(
                    concept_name=concept.name,
                    concept_lookup=concept_lookup
                )
            )

            critical = (
                self._is_critical_blocker(
                    concept=concept,
                    concept_lookup=concept_lookup
                )
            )

            priority = (
                self._calculate_planning_priority(
                    concept=concept,
                    action=action,
                    base_priority=float(
                        recommendation.get(
                            "priority",
                            0
                        )
                    ),
                    critical=critical
                )
            )

            minutes = self._estimate_minutes(
                action=action,
                mastery=concept.mastery
            )

            candidates.append(
                StudyTask(
                    concept=concept.name,
                    action=action,
                    minutes=minutes,
                    priority=priority,
                    reason=recommendation.get(
                        "reason",
                        ""
                    ),
                    prerequisites=prerequisites,
                    dependency_depth=dependency_depth,
                    critical=critical
                )
            )

        # ========================================================
        # 2. Build dependency-aware order.
        # ========================================================

        ordered = self._build_learning_order(
            tasks=candidates,
            concept_lookup=concept_lookup
        )

        # ========================================================
        # 3. Fit into available time.
        # ========================================================

        selected = self._fit_to_budget(
            tasks=ordered,
            available_minutes=available_minutes
        )

        return {
            "total_minutes": sum(
                task.minutes
                for task in selected
            ),
            "available_minutes": available_minutes,
            "tasks": [
                task.to_dict()
                for task in selected
            ],
            "message": self._build_message(
                tasks=selected,
                available_minutes=available_minutes
            )
        }

    # ============================================================
    # PREREQUISITE SATISFACTION
    # ============================================================

    def _is_prerequisite_satisfied(
        self,
        concept
    ):
        """
        Determine whether a prerequisite is already strong
        enough that Sift does not need to schedule it first.
        """

        return (
            concept.mastery
            >= self.PREREQUISITE_MASTERY_THRESHOLD
        )

    # ============================================================
    # CRITICAL BLOCKER
    # ============================================================

    def _is_critical_blocker(
        self,
        concept,
        concept_lookup
    ):
        """
        Determine whether a weak concept is blocking
        another weak concept.

        Example:

            Call Stack = 30%
            Recursion = 40%

        If Call Stack is required for Recursion,
        Call Stack becomes a critical blocker.

        But:

            Functions = 88%

        does NOT become a blocker simply because it
        appears earlier in the graph.
        """

        # Strong concepts cannot be urgent blockers.
        if self._is_prerequisite_satisfied(
            concept
        ):
            return False

        for other in concept_lookup.values():

            if other.name == concept.name:
                continue

            # Only another weak concept creates a
            # meaningful blocker relationship.
            if self._is_prerequisite_satisfied(
                other
            ):
                continue

            prerequisites = (
                self.adaptive_engine
                .knowledge_graph
                .get_prerequisites(
                    other.name
                )
            )

            if concept.name in prerequisites:
                return True

        return False

    # ============================================================
    # PLANNING PRIORITY
    # ============================================================

    def _calculate_planning_priority(
        self,
        concept,
        action,
        base_priority,
        critical
    ):
        """
        Calculate the value of spending scarce study time
        on a concept.
        """

        score = base_priority

        # --------------------------------------------------------
        # Critical blockers get a very strong boost.
        # --------------------------------------------------------

        if critical:
            score += 100

        # --------------------------------------------------------
        # Weak concepts get additional urgency.
        # --------------------------------------------------------

        if concept.mastery <= 30:
            score += 30

        elif concept.mastery <= 50:
            score += 20

        elif concept.mastery < 75:
            score += 8

        # --------------------------------------------------------
        # Strong concepts are deliberately deprioritized.
        # --------------------------------------------------------

        if concept.mastery >= 85:
            score -= 40

        # --------------------------------------------------------
        # Strong challenges are enrichment, not urgent
        # foundational learning.
        # --------------------------------------------------------

        if (
            action == "challenge"
            and concept.mastery >= 85
        ):
            score -= 15

        # --------------------------------------------------------
        # Retrieval review receives a modest boost.
        # --------------------------------------------------------

        if action == "review":
            score += 5

        return score

    # ============================================================
    # DEPENDENCY DEPTH
    # ============================================================

    def _dependency_depth(
        self,
        concept_name,
        concept_lookup,
        visited=None
    ):
        """
        Calculate how deep a concept is in the dependency graph.

        Example:

            Functions
                ↓
            Call Stack
                ↓
            Recursion

        Functions = 0
        Call Stack = 1
        Recursion = 2
        """

        if visited is None:
            visited = set()

        if concept_name in visited:
            return 0

        visited.add(
            concept_name
        )

        prerequisites = (
            self.adaptive_engine
            .knowledge_graph
            .get_prerequisites(
                concept_name
            )
        )

        relevant = [
            prerequisite
            for prerequisite in prerequisites
            if prerequisite in concept_lookup
        ]

        if not relevant:
            return 0

        return 1 + max(
            self._dependency_depth(
                concept_name=prerequisite,
                concept_lookup=concept_lookup,
                visited=visited.copy()
            )
            for prerequisite in relevant
        )

    # ============================================================
    # LEARNING ORDER
    # ============================================================

    def _build_learning_order(
        self,
        tasks,
        concept_lookup
    ):
        """
        Build the actual study sequence.

        Important:

        A prerequisite only blocks a concept if that
        prerequisite is itself weak.

        Therefore:

            Functions 88%
            Call Stack 30%
            Recursion 40%

        becomes:

            Call Stack → Recursion → Functions
        """

        task_lookup = {
            task.concept: task
            for task in tasks
        }

        remaining = set(
            task_lookup.keys()
        )

        ordered = []

        while remaining:

            available = []

            # ----------------------------------------------------
            # Find tasks whose UNSATISFIED prerequisites are
            # not still waiting.
            # ----------------------------------------------------

            for name in remaining:

                task = task_lookup[name]

                blocked = False

                for prerequisite_name in (
                    task.prerequisites
                ):

                    # Prerequisite isn't part of the current
                    # learning set. Nothing to wait for.
                    if prerequisite_name not in concept_lookup:
                        continue

                    prerequisite = concept_lookup[
                        prerequisite_name
                    ]

                    # Strong prerequisite is already satisfied.
                    if self._is_prerequisite_satisfied(
                        prerequisite
                    ):
                        continue

                    # Weak prerequisite is still in the plan.
                    if prerequisite_name in remaining:
                        blocked = True
                        break

                if not blocked:
                    available.append(
                        task
                    )

            # ----------------------------------------------------
            # Safety fallback for cyclic/malformed graphs.
            # ----------------------------------------------------

            if not available:
                available = [
                    task_lookup[name]
                    for name in remaining
                ]

            # ----------------------------------------------------
            # Select the most valuable currently available task.
            # ----------------------------------------------------

            def sort_key(task):

                concept = concept_lookup[
                    task.concept
                ]

                critical_score = (
                    1
                    if task.critical
                    else 0
                )

                weakness_score = (
                    100
                    - concept.mastery
                )

                planning_score = (
                    task.priority
                )

                # Critical blockers are first.
                #
                # Then weakness.
                #
                # Then overall planning value.
                return (
                    critical_score,
                    weakness_score,
                    planning_score
                )

            available.sort(
                key=sort_key,
                reverse=True
            )

            selected = available[0]

            ordered.append(
                selected
            )

            remaining.remove(
                selected.concept
            )

        return ordered

    # ============================================================
    # TIME ESTIMATION
    # ============================================================

    def _estimate_minutes(
        self,
        action,
        mastery
    ):
        """
        Estimate reasonable intervention time.
        """

        if action == "teach":

            if mastery <= 30:
                return 8

            return 6

        if action == "practice":
            return 6

        if action == "review":
            return 4

        if action == "challenge":
            return 5

        return 4

    # ============================================================
    # FIT TO BUDGET
    # ============================================================

    def _fit_to_budget(
        self,
        tasks,
        available_minutes
    ):
        """
        Fit the ordered learning path into the learner's
        available time.
        """

        selected = []

        remaining = available_minutes

        for task in tasks:

            if remaining < self.MIN_TASK_MINUTES:
                break

            minutes = min(
                task.minutes,
                remaining
            )

            if minutes < self.MIN_TASK_MINUTES:
                continue

            selected.append(
                StudyTask(
                    concept=task.concept,
                    action=task.action,
                    minutes=minutes,
                    priority=task.priority,
                    reason=task.reason,
                    prerequisites=task.prerequisites,
                    dependency_depth=task.dependency_depth,
                    critical=task.critical
                )
            )

            remaining -= minutes

        return selected

    # ============================================================
    # USER-FACING MESSAGE
    # ============================================================

    def _build_message(
        self,
        tasks,
        available_minutes
    ):
        """
        Explain the generated plan.
        """

        if not tasks:
            return (
                "Sift could not find a suitable "
                "learning path for this session."
            )

        used = sum(
            task.minutes
            for task in tasks
        )

        remaining = (
            available_minutes - used
        )

        if remaining == 0:
            return (
                f"Sift built a focused {used}-minute "
                "session using your full available time."
            )

        return (
            f"Sift planned {used} minutes of "
            f"high-value learning and left "
            f"{remaining} minutes unallocated."
        )