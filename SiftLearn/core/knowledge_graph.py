class KnowledgeGraph:
    """Stores prerequisite relationships between concepts."""

    def __init__(self, graph=None):
        self.graph = graph or {}

    def add_concept(self, concept, prerequisites=None):
        self.graph[concept] = prerequisites or []

    def get_prerequisites(self, concept):
        return self.graph.get(concept, [])

    def find_blockers(self, concept, concepts):
        """
        Find weak prerequisites that may block understanding
        of the target concept.
        """

        prerequisites = self.get_prerequisites(concept)

        concept_lookup = {
            item.name: item
            for item in concepts
        }

        blockers = []

        for prerequisite in prerequisites:
            item = concept_lookup.get(prerequisite)

            if item and item.mastery < 60:
                blockers.append(item)

        return blockers

    def explain_dependency(self, concept, concepts):
        """Explain why a prerequisite may be blocking a concept."""

        blockers = self.find_blockers(
            concept,
            concepts
        )

        if not blockers:
            return None

        weakest = min(
            blockers,
            key=lambda item: item.mastery
        )

        return {
            "target": concept,
            "blocker": weakest.name,
            "blocker_mastery": round(weakest.mastery),
            "reason": (
                f"{weakest.name} may be limiting progress "
                f"on {concept} because it is a prerequisite."
            )
        }