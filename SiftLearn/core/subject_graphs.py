"""
Sift subject knowledge graphs.

Each graph maps:

    concept -> prerequisite concepts

Concept names are intentionally human-readable.
Keep graphs acyclic and make sure every concept can actually
be assessed/taught by Sift.
"""


# ============================================================
# PYTHON
# ============================================================

PYTHON_GRAPH = {
    # Foundations
    "Variables": [],

    "Conditions": [
        "Variables",
    ],

    "Loops": [
        "Conditions",
    ],

    # Operators
    # The modulo operator is explicitly represented because
    # Sift's assessment engine can return it as a concept.
    "modulo operator": [
        "Variables",
    ],

    # Functions
    "Functions": [
        "Variables",
    ],

    "Parameters": [
        "Functions",
    ],

    # Core data structures
    "Lists": [
        "Variables",
    ],

    "Dictionaries": [
        "Lists",
    ],

    # Execution model
    "Call Stack": [
        "Functions",
    ],

    "Recursion": [
        "Functions",
        "Call Stack",
    ],

    # Object-oriented programming
    "Classes": [
        "Functions",
    ],

    "OOP": [
        "Classes",
    ],
}


# ============================================================
# DATA STRUCTURES & ALGORITHMS
# ============================================================

DSA_GRAPH = {
    # Foundations
    "Complexity": [],

    "Arrays": [
        "Complexity",
    ],

    # Searching
    "Linear Search": [
        "Arrays",
    ],

    "Binary Search": [
        "Arrays",
        "Complexity",
    ],

    # Sorting
    "Sorting": [
        "Arrays",
        "Complexity",
    ],

    # Linked structures
    "Linked Lists": [
        "Complexity",
    ],

    "Stacks": [
        "Linked Lists",
    ],

    "Queues": [
        "Linked Lists",
    ],

    # Recursion
    "Recursion": [
        "Complexity",
    ],

    # Trees
    "Trees": [
        "Recursion",
    ],

    "Binary Trees": [
        "Trees",
    ],

    "Binary Search Trees": [
        "Binary Trees",
        "Binary Search",
    ],

    "Heaps": [
        "Binary Trees",
    ],

    # Graphs
    "Graphs": [
        "Complexity",
    ],

    "BFS": [
        "Graphs",
        "Queues",
    ],

    "DFS": [
        "Graphs",
        "Stacks",
        "Recursion",
    ],
}


# ============================================================
# MACHINE LEARNING
# ============================================================

MACHINE_LEARNING_GRAPH = {
    # Mathematical / statistical foundations
    "Probability": [],

    "Statistics": [
        "Probability",
    ],

    "Linear Algebra": [],

    # Data foundations
    "Data Preparation": [
        "Statistics",
    ],

    "Feature Engineering": [
        "Data Preparation",
    ],

    # Core ML concepts
    "Supervised Learning": [
        "Statistics",
        "Data Preparation",
    ],

    "Regression": [
        "Supervised Learning",
    ],

    "Classification": [
        "Supervised Learning",
    ],

    # Model evaluation
    "Model Evaluation": [
        "Statistics",
        "Supervised Learning",
    ],

    "Cross Validation": [
        "Model Evaluation",
    ],

    # Optimization
    "Loss Functions": [
        "Regression",
        "Classification",
    ],

    "Gradient Descent": [
        "Loss Functions",
        "Linear Algebra",
    ],

    # Generalization
    "Overfitting": [
        "Model Evaluation",
    ],

    "Regularization": [
        "Overfitting",
    ],

    # Neural networks
    "Neural Networks": [
        "Linear Algebra",
        "Gradient Descent",
    ],

    "Backpropagation": [
        "Neural Networks",
        "Gradient Descent",
    ],
}


# ============================================================
# MATHEMATICS
# ============================================================

MATHEMATICS_GRAPH = {
    # Arithmetic foundations
    "Numbers": [],

    "Arithmetic": [
        "Numbers",
    ],

    # Algebra
    "Algebra": [
        "Arithmetic",
    ],

    "Equations": [
        "Algebra",
    ],

    "Functions": [
        "Algebra",
    ],

    # Calculus
    "Limits": [
        "Functions",
    ],

    "Derivatives": [
        "Limits",
        "Functions",
    ],

    "Integrals": [
        "Derivatives",
    ],

    # Probability
    "Probability": [
        "Numbers",
        "Arithmetic",
    ],

    "Conditional Probability": [
        "Probability",
    ],

    "Bayes Theorem": [
        "Conditional Probability",
    ],

    # Linear algebra
    "Vectors": [
        "Numbers",
    ],

    "Matrices": [
        "Vectors",
    ],

    "Linear Algebra": [
        "Vectors",
        "Matrices",
    ],
}


# ============================================================
# ALL SUBJECT GRAPHS
# ============================================================


SQL_DBMS_GRAPH={"SQL Basics":[],"SELECT and Filtering":["SQL Basics"],"Joins":["SELECT and Filtering"],"Grouping and Aggregation":["SELECT and Filtering"],"Subqueries":["Joins"],"Indexes":["SQL Basics"]}
OPERATING_SYSTEMS_GRAPH={"OS Basics":[],"Processes":["OS Basics"],"Threads":["Processes"],"CPU Scheduling":["Processes"],"Memory Management":["OS Basics"],"Deadlocks":["Processes","Threads"]}
COMPUTER_NETWORKS_GRAPH={"Network Basics":[],"OSI and TCP/IP":["Network Basics"],"IP Addressing":["OSI and TCP/IP"],"TCP and UDP":["OSI and TCP/IP"],"Routing":["IP Addressing"],"HTTP and DNS":["TCP and UDP","IP Addressing"]}

SUBJECT_GRAPHS = {
    "Python": PYTHON_GRAPH,
    "Data Structures & Algorithms": DSA_GRAPH,
    "Machine Learning": MACHINE_LEARNING_GRAPH,
    "Mathematics": MATHEMATICS_GRAPH,
    "SQL / DBMS": SQL_DBMS_GRAPH,
    "Operating Systems": OPERATING_SYSTEMS_GRAPH,
    "Computer Networks": COMPUTER_NETWORKS_GRAPH,
}


# ============================================================
# PUBLIC HELPERS
# ============================================================

SUPPORTED_SUBJECTS = tuple(
    SUBJECT_GRAPHS.keys()
)


def get_supported_subjects():
    """Return the authoritative registered subject list."""
    return list(SUPPORTED_SUBJECTS)


def get_subject_graph(subject):
    """
    Return the knowledge graph definition for a subject.

    Raises:
        ValueError: if the subject is not supported.
    """

    if not subject:
        raise ValueError(
            "Subject is required."
        )

    graph = SUBJECT_GRAPHS.get(subject)

    if graph is None:
        raise ValueError(
            f"Unsupported subject: {subject}. "
            f"Supported subjects: "
            f"{', '.join(SUPPORTED_SUBJECTS)}"
        )

    # Return a copy so callers cannot accidentally mutate
    # the global subject definition.
    return {
        concept: list(prerequisites)
        for concept, prerequisites in graph.items()
    }
