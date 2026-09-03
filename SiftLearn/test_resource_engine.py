import os
from core.resource_engine import ResourceEngine


print("=" * 70)
print("SIFT RESOURCE QUALITY + CROSS-SUBJECT TEST")
print("=" * 70)


engine = ResourceEngine()


# ================================================================
# HELPER
# ================================================================


def check_candidate(
    name,
    title,
    description,
    concept,
    subject,
    should_pass,
):
    print()
    print("-" * 70)
    print(name)
    print("-" * 70)

    score, reasons, rejected = (
        engine._score_video(
            title=title,
            description=description,
            concept=concept,
            subject=subject,
        )
    )

    print("concept:", concept)
    print("subject:", subject)
    print("title:", title)
    print("score:", score)
    print("rejected:", rejected)
    print("reasons:", reasons)

    if should_pass:

        assert rejected is False, (
            f"Expected candidate to PASS, "
            f"but it was rejected: {reasons}"
        )

        assert (
            score >= engine.MIN_VIDEO_SCORE
        ), (
            f"Expected score >= "
            f"{engine.MIN_VIDEO_SCORE}, "
            f"got {score}"
        )

        print("EXPECTED: ACCEPT")
        print("RESULT: PASS")

    else:

        assert rejected is True, (
            f"Expected candidate to be rejected, "
            f"but it was accepted: {reasons}"
        )

        print("EXPECTED: REJECT")
        print("RESULT: PASS")


# ================================================================
# QUICK TIP
# ================================================================


print("\nQUICK TIP")
print("-" * 70)


tip = engine.generate_quick_tip(
    concept="modulo operator",
    mistake_type="conceptual",
    misconception=(
        "The learner thinks % performs normal division."
    ),
    learner_level="Beginner",
)

print(tip)

assert tip["type"] == "quick_tip"
assert tip["concept"] == "modulo operator"
assert tip["body"]
assert tip["example"] == "17 % 5 = 2"

print("quick tip: PASS")


# ================================================================
# PYTHON
# ================================================================


print("\n")
print("=" * 70)
print("PYTHON")
print("=" * 70)


check_candidate(
    name="Python modulo — correct resource",
    title=(
        "Python Modulo Operator (%) "
        "Explained for Beginners"
    ),
    description=(
        "Learn how the Python modulo operator "
        "returns the remainder after division."
    ),
    concept="modulo operator",
    subject="Python",
    should_pass=True,
)


check_candidate(
    name="Python modulo — remainder explanation",
    title=(
        "Calculating the Remainder of Division "
        "in Python"
    ),
    description=(
        "Learn Python remainder calculations "
        "using the modulo operator."
    ),
    concept="modulo operator",
    subject="Python",
    should_pass=True,
)


check_candidate(
    name="Python modulo — STRING operator false positive",
    title=(
        "Python Part 4: "
        "How Python String Operators Actually Work"
    ),
    description=(
        "Learn about string operators and "
        "string manipulation in Python."
    ),
    concept="modulo operator",
    subject="Python",
    should_pass=False,
)


check_candidate(
    name="Python modulo — generic Python false positive",
    title=(
        "Python Programming Tutorial for Beginners"
    ),
    description=(
        "Learn Python programming basics."
    ),
    concept="modulo operator",
    subject="Python",
    should_pass=False,
)


# ================================================================
# DATA STRUCTURES & ALGORITHMS
# ================================================================


print("\n")
print("=" * 70)
print("DATA STRUCTURES & ALGORITHMS")
print("=" * 70)


check_candidate(
    name="Binary search — correct",
    title=(
        "Binary Search Algorithm Explained "
        "with Examples"
    ),
    description=(
        "Learn binary search on a sorted array "
        "step by step."
    ),
    concept="binary search",
    subject="Data Structures & Algorithms",
    should_pass=True,
)


check_candidate(
    name="Binary search — unrelated search algorithm",
    title=(
        "Linear Search Algorithm Explained"
    ),
    description=(
        "Learn sequential searching through an array."
    ),
    concept="binary search",
    subject="Data Structures & Algorithms",
    should_pass=False,
)


check_candidate(
    name="Linked list — correct",
    title=(
        "Linked List Data Structure "
        "Explained for Beginners"
    ),
    description=(
        "Learn how linked lists work and "
        "how nodes are connected."
    ),
    concept="linked list",
    subject="Data Structures & Algorithms",
    should_pass=True,
)


check_candidate(
    name="Linked list — unrelated",
    title=(
        "Binary Tree Data Structure Explained"
    ),
    description=(
        "Learn binary trees and tree traversal."
    ),
    concept="linked list",
    subject="Data Structures & Algorithms",
    should_pass=False,
)


# ================================================================
# MACHINE LEARNING
# ================================================================


print("\n")
print("=" * 70)
print("MACHINE LEARNING")
print("=" * 70)


check_candidate(
    name="Gradient descent — correct",
    title=(
        "Gradient Descent Explained "
        "for Machine Learning"
    ),
    description=(
        "Learn how gradient descent optimizes "
        "machine learning models."
    ),
    concept="gradient descent",
    subject="Machine Learning",
    should_pass=True,
)


check_candidate(
    name="Gradient descent — unrelated ML",
    title=(
        "Decision Trees in Machine Learning "
        "Explained"
    ),
    description=(
        "Learn how decision tree models work."
    ),
    concept="gradient descent",
    subject="Machine Learning",
    should_pass=False,
)


check_candidate(
    name="Overfitting — correct",
    title=(
        "Overfitting in Machine Learning "
        "Explained"
    ),
    description=(
        "Learn why machine learning models "
        "overfit and how to recognize it."
    ),
    concept="overfitting",
    subject="Machine Learning",
    should_pass=True,
)


check_candidate(
    name="Overfitting — unrelated",
    title=(
        "Underfitting in Machine Learning "
        "Explained"
    ),
    description=(
        "Learn about underfitted models."
    ),
    concept="overfitting",
    subject="Machine Learning",
    should_pass=False,
)


# ================================================================
# MATHEMATICS
# ================================================================


print("\n")
print("=" * 70)
print("MATHEMATICS")
print("=" * 70)


check_candidate(
    name="Derivative — correct",
    title=(
        "Derivatives Explained "
        "for Beginners"
    ),
    description=(
        "Learn differentiation and how to "
        "calculate derivatives."
    ),
    concept="derivative",
    subject="Mathematics",
    should_pass=True,
)


check_candidate(
    name="Derivative — unrelated calculus",
    title=(
        "Integrals and Integration Explained"
    ),
    description=(
        "Learn how integration works in calculus."
    ),
    concept="derivative",
    subject="Mathematics",
    should_pass=False,
)


check_candidate(
    name="Probability — correct",
    title=(
        "Probability Theory Explained "
        "with Simple Examples"
    ),
    description=(
        "Learn probability fundamentals "
        "and calculate probabilities."
    ),
    concept="probability",
    subject="Mathematics",
    should_pass=True,
)


check_candidate(
    name="Probability — unrelated math",
    title=(
        "Linear Algebra Basics Explained"
    ),
    description=(
        "Learn matrices and vectors."
    ),
    concept="probability",
    subject="Mathematics",
    should_pass=False,
)


# ================================================================
# SUBJECT MISMATCH
# ================================================================


print("\n")
print("=" * 70)
print("SUBJECT MISMATCH PROTECTION")
print("=" * 70)


check_candidate(
    name="Same concept but wrong subject",
    title=(
        "Probability in Machine Learning "
        "Explained"
    ),
    description=(
        "Learn probability concepts as used "
        "in machine learning."
    ),
    concept="probability",
    subject="Mathematics",
    should_pass=True,
)


# ================================================================
# UNKNOWN CONCEPT
# ================================================================


print("\n")
print("=" * 70)
print("UNKNOWN CONCEPT FALLBACK")
print("=" * 70)


check_candidate(
    name="Unknown concept — exact phrase",
    title=(
        "Bayes Theorem Explained "
        "for Beginners"
    ),
    description=(
        "Learn Bayes theorem with simple "
        "probability examples."
    ),
    concept="Bayes theorem",
    subject="Mathematics",
    should_pass=True,
)


check_candidate(
    name="Unknown concept — unrelated",
    title=(
        "Derivatives Explained for Beginners"
    ),
    description=(
        "Learn differentiation and calculus."
    ),
    concept="Bayes theorem",
    subject="Mathematics",
    should_pass=False,
)


# ================================================================
# QUALITY THRESHOLD
# ================================================================


print("\n")
print("=" * 70)
print("QUALITY THRESHOLD")
print("=" * 70)


assert engine.MIN_VIDEO_SCORE >= 70

print(
    "minimum video score:",
    engine.MIN_VIDEO_SCORE,
)

print(
    "quality threshold: PASS"
)


# ================================================================
# LIVE YOUTUBE TEST
# ================================================================


print("\n")
print("=" * 70)
print("LIVE YOUTUBE TEST")
print("=" * 70)


if engine.youtube_api_key and os.getenv("SIFT_LIVE_YOUTUBE_TEST", "0") == "1":

    print("YOUTUBE_API_KEY: FOUND; live test explicitly enabled")

    videos = engine.search_youtube(
        concept="modulo operator",
        subject="Python",
        learner_level="Beginner",
        strategy="visual_explanation",
        mistake_type="conceptual",
        misconception=(
            "The learner thinks % performs "
            "normal division."
        ),
        max_results=10,
    )

    print(
        "accepted videos:",
        len(videos),
    )

    for index, video in enumerate(
        videos,
        start=1,
    ):

        print()
        print(
            f"VIDEO {index}"
        )

        print(
            "title:",
            video["title"],
        )

        print(
            "channel:",
            video["channel"],
        )

        print(
            "score:",
            video["quality_score"],
        )

        print(
            "reasons:",
            video["quality_reasons"],
        )

        print(
            "url:",
            video["url"],
        )

        # --------------------------------------------------------
        # Critical guarantees.
        # --------------------------------------------------------

        assert (
            video["rejected"]
            is False
        )

        assert (
            video["quality_score"]
            >= engine.MIN_VIDEO_SCORE
        )

    print()
    print(
        "all live videos passed quality gate: PASS"
    )

else:

    if engine.youtube_api_key:
        print("YOUTUBE_API_KEY: FOUND; live test disabled by default.")
    else:
        print("YOUTUBE_API_KEY: NOT FOUND")
    print("Live YouTube test skipped. Set SIFT_LIVE_YOUTUBE_TEST=1 to opt in.")


# ================================================================
# FINAL RESULT
# ================================================================


print("\n")
print("=" * 70)
print("RESULT: PASS")
print("=" * 70)

print(
    """
SIFT RESOURCE QUALITY SYSTEM VERIFIED

Concept
   ↓
Subject
   ↓
Search
   ↓
Multiple YouTube candidates
   ↓
Concept relevance
   ↓
Subject relevance
   ↓
Educational signal
   ↓
False-positive protection
   ↓
Quality threshold
   ↓
Ranked resource
   ↓
Learner
"""
)