"""
SIFT RESOURCE ENGINE
============================================================

Purpose
-------
Find safe, relevant external learning resources for Sift.

Pipeline
--------

    Learner state
          ↓
       Concept
          ↓
       Subject
          ↓
    Resource search
          ↓
    Candidate videos
          ↓
    Concept relevance
          ↓
    Subject relevance
          ↓
    Educational signal
          ↓
      Quality gate
          ↓
    Ranked resources
          ↓
       Learner


IMPORTANT DESIGN RULES
----------------------

1. Concept relevance is the most important signal.

2. An unrelated concept MUST NOT pass merely because
   the video is educational.

3. Subject relevance improves the score but does not
   reject an otherwise strongly relevant exact-concept
   resource.

4. Known aliases are used for common concepts.

5. Unknown concepts can still work through exact phrase
   matching.

6. Generic words such as "operator" are NOT enough to
   establish the modulo concept.

7. External resources are optional. A YouTube failure
   should not crash the learning experience.

============================================================
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# EXCEPTIONS
# ============================================================


class ResourceEngineError(Exception):
    """Base exception for the resource engine."""


class ResourceConfigurationError(
    ResourceEngineError
):
    """Raised when required configuration is missing."""


class ResourceSearchError(
    ResourceEngineError
):
    """Raised when an external resource search fails."""


# ============================================================
# RESOURCE ENGINE
# ============================================================


class ResourceEngine:
    """
    Sift's external learning-resource engine.

    Currently supports:
        - Quick learning tips
        - YouTube educational resources
        - Resource quality scoring
        - Concept relevance
        - Subject relevance
        - Educational-content detection
        - False-positive protection
    """

    # ========================================================
    # CONFIGURATION
    # ========================================================

    MIN_VIDEO_SCORE = 70

    MAX_YOUTUBE_RESULTS = 10

    # ========================================================
    # EDUCATIONAL LANGUAGE
    # ========================================================

    EDUCATIONAL_TERMS = {
        "tutorial",
        "explained",
        "explanation",
        "learn",
        "learning",
        "guide",
        "lesson",
        "course",
        "beginner",
        "basics",
        "basic",
        "introduction",
        "intro",
        "example",
        "examples",
        "how",
        "understand",
        "understanding",
        "practice",
        "programming",
        "concept",
        "concepts",
        "lecture",
    }

    # ========================================================
    # SUBJECT ALIASES
    # ========================================================

    SUBJECT_ALIASES = {

        # ----------------------------------------------------
        # Python
        # ----------------------------------------------------

        "python": {
            "python",
            "python programming",
            "python programming language",
        },

        # ----------------------------------------------------
        # Data Structures & Algorithms
        # ----------------------------------------------------

        "data structures & algorithms": {
            "data structures",
            "data structure",
            "algorithm",
            "algorithms",
            "dsa",
            "data structures and algorithms",
        },

        "data structures and algorithms": {
            "data structures",
            "data structure",
            "algorithm",
            "algorithms",
            "dsa",
            "data structures and algorithms",
        },

        "dsa": {
            "data structures",
            "data structure",
            "algorithm",
            "algorithms",
            "dsa",
            "data structures and algorithms",
        },

        # ----------------------------------------------------
        # Machine Learning
        # ----------------------------------------------------

        "machine learning": {
            "machine learning",
            "machine-learning",
            "ml",
            "machine learning algorithms",
        },

        "ml": {
            "machine learning",
            "machine-learning",
            "ml",
            "machine learning algorithms",
        },

        # ----------------------------------------------------
        # Mathematics
        # ----------------------------------------------------

        "mathematics": {
            "mathematics",
            "math",
            "maths",
        },

        "math": {
            "mathematics",
            "math",
            "maths",
        },

        "maths": {
            "mathematics",
            "math",
            "maths",
        },
    }

    # ========================================================
    # CONCEPT ALIASES
    # ========================================================

    CONCEPT_ALIASES = {

        # ====================================================
        # PYTHON
        # ====================================================

        "modulo operator": {
            "modulo",
            "modulus",
            "remainder",
            "modulo operator",
            "modulus operator",
            "remainder operator",
        },

        "modulo operator (%)": {
            "modulo",
            "modulus",
            "remainder",
            "modulo operator",
            "modulus operator",
            "remainder operator",
        },

        "call stack": {
            "call stack",
            "stack frame",
            "stack frames",
            "function call stack",
            "function stack",
            "call frames",
        },

        "list comprehension": {
            "list comprehension",
            "list comprehensions",
            "python list comprehension",
        },

        "dictionary": {
            "dictionary",
            "dictionaries",
            "python dictionary",
            "python dictionaries",
        },

        "lambda function": {
            "lambda function",
            "lambda functions",
            "python lambda",
            "lambda expression",
            "lambda expressions",
        },

        "exception handling": {
            "exception handling",
            "error handling",
            "python exceptions",
            "handling exceptions",
        },

        "object oriented programming": {
            "object oriented programming",
            "object-oriented programming",
            "oop",
            "classes and objects",
            "python oop",
        },

        # ====================================================
        # DATA STRUCTURES & ALGORITHMS
        # ====================================================

        "binary search": {
            "binary search",
            "binary searching",
            "search in sorted array",
            "search in sorted list",
        },

        "linear search": {
            "linear search",
            "linear searching",
            "sequential search",
            "sequential searching",
        },

        "linked list": {
            "linked list",
            "linked lists",
            "singly linked list",
            "doubly linked list",
            "circular linked list",
        },

        "stack": {
            "stack data structure",
            "stack data structures",
            "stack implementation",
            "stack data structure implementation",
        },

        "queue": {
            "queue data structure",
            "queue data structures",
            "queue implementation",
            "queue data structure implementation",
        },

        "binary tree": {
            "binary tree",
            "binary trees",
            "binary tree data structure",
        },

        "binary search tree": {
            "binary search tree",
            "binary search trees",
            "bst",
        },

        "hash table": {
            "hash table",
            "hash tables",
            "hash map",
            "hash maps",
            "hashtable",
        },

        "graph traversal": {
            "graph traversal",
            "graph traversals",
            "graph traversal algorithms",
        },

        "breadth first search": {
            "breadth first search",
            "breadth-first search",
            "bfs",
        },

        "depth first search": {
            "depth first search",
            "depth-first search",
            "dfs",
        },

        "recursion": {
            "recursion",
            "recursive",
            "recursive function",
            "recursive functions",
        },

        # ====================================================
        # MACHINE LEARNING
        # ====================================================

        "gradient descent": {
            "gradient descent",
            "gradient descent algorithm",
            "gradient-based optimization",
        },

        "linear regression": {
            "linear regression",
            "simple linear regression",
            "multiple linear regression",
        },

        "logistic regression": {
            "logistic regression",
            "logistic classifier",
        },

        "neural network": {
            "neural network",
            "neural networks",
            "artificial neural network",
            "artificial neural networks",
        },

        "overfitting": {
            "overfitting",
            "overfit",
            "overfitted",
        },

        "underfitting": {
            "underfitting",
            "underfit",
            "underfitted",
        },

        "supervised learning": {
            "supervised learning",
            "supervised machine learning",
        },

        "unsupervised learning": {
            "unsupervised learning",
            "unsupervised machine learning",
        },

        "classification": {
            "classification",
            "classification algorithm",
            "classification algorithms",
            "classification machine learning",
        },

        "clustering": {
            "clustering",
            "clustering algorithm",
            "clustering algorithms",
            "machine learning clustering",
        },

        "k means": {
            "k means",
            "k-means",
            "kmeans",
            "k means clustering",
        },

        "decision tree": {
            "decision tree",
            "decision trees",
            "decision tree algorithm",
        },

        # ====================================================
        # MATHEMATICS
        # ====================================================

        "mean": {
            "mean",
            "arithmetic mean",
            "average",
        },

        "median": {
            "median",
        },

        "mode": {
            "mode",
            "statistical mode",
        },

        "probability": {
            "probability",
            "probability theory",
        },

        "derivative": {
            "derivative",
            "derivatives",
            "differentiation",
        },

        "integral": {
            "integral",
            "integrals",
            "integration",
        },

        "matrix": {
            "matrix",
            "matrices",
            "matrix algebra",
        },

        "vectors": {
            "vector",
            "vectors",
            "vector algebra",
        },

        "linear algebra": {
            "linear algebra",
        },

        "quadratic equation": {
            "quadratic equation",
            "quadratic equations",
        },

        "pythagorean theorem": {
            "pythagorean theorem",
            "pythagoras theorem",
            "pythagorean theorem proof",
        },
    }

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        youtube_api_key: Optional[str] = None,
    ):

        self.youtube_api_key = (
            youtube_api_key
            or os.getenv(
                "YOUTUBE_API_KEY"
            )
        )

        self._youtube = None

    # ========================================================
    # QUICK TIP
    # ========================================================

    def generate_quick_tip(
        self,
        concept: str,
        mistake_type: Optional[str] = None,
        misconception: Optional[str] = None,
        learner_level: str = "Beginner",
    ) -> Dict[str, Any]:

        if not isinstance(
            concept,
            str,
        ) or not concept.strip():

            raise ValueError(
                "A concept is required to generate a quick tip."
            )

        concept_text = concept.strip()

        normalized = (
            self._normalize_text(
                concept_text
            )
        )

        # ----------------------------------------------------
        # Modulo
        # ----------------------------------------------------

        if normalized in {
            "modulo operator",
            "modulo operator %",
            "modulo",
        }:

            return {
                "type": "quick_tip",

                "title": (
                    "Remember the remainder"
                ),

                "concept": concept_text,

                "body": (
                    "The % operator returns what is "
                    "left after division. It does not "
                    "return the normal division result."
                ),

                "example": (
                    "17 % 5 = 2"
                ),

                "reason": (
                    "This directly reinforces the "
                    "modulo concept."
                ),
                "situation": "Use this when a problem asks what remains after division or when deciding if a value is divisible.",
                "next_move": "Try one fresh remainder example without looking at the rule.",
            }

        # ----------------------------------------------------
        # Call Stack
        # ----------------------------------------------------

        if normalized == "call stack":

            return {
                "type": "quick_tip",

                "title": (
                    "Think in layers"
                ),

                "concept": concept_text,

                "body": (
                    "Think of the call stack like a "
                    "stack of plates: the most recently "
                    "called function is the first one "
                    "to finish."
                ),

                "example": (
                    "A → B → C means C is currently "
                    "at the top of the stack."
                ),

                "reason": (
                    "A concrete mental model makes "
                    "stack behavior easier to remember."
                ),
                "situation": "Use this when tracing nested function calls, recursion, or deciding which function returns first.",
                "next_move": "Trace one call chain from the first call to the final return.",
            }

        # ----------------------------------------------------
        # Generic fallback
        # ----------------------------------------------------

        if (
            isinstance(
                misconception,
                str,
            )
            and misconception.strip()
        ):

            body = (
                f"Focus on the difference between "
                f"{concept_text} and the idea you "
                f"confused it with."
            )

        else:

            body = (
                f"Focus on the core idea behind "
                f"{concept_text} before moving to "
                f"harder examples."
            )

        return {
            "type": "quick_tip",

            "title": (
                f"Keep {concept_text} simple"
            ),

            "concept": concept_text,

            "body": body,

            "example": None,

            "reason": (
                f"Reinforcement for a "
                f"{learner_level.lower()} learner."
            ),
            "situation": (
                f"Use this when you get stuck on {concept_text} "
                "or need to connect the definition to a problem."
            ),
            "next_move": (
                "Try the next problem from memory; if you hesitate, "
                "return to the example rather than memorizing a definition."
            ),
        }

    # ========================================================
    # YOUTUBE SEARCH
    # ========================================================

    def search_youtube(
        self,
        concept: str,
        subject: str = "Python",
        learner_level: str = "Beginner",
        strategy: Optional[str] = None,
        mistake_type: Optional[str] = None,
        misconception: Optional[str] = None,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:

        if not self.youtube_api_key:

            raise ResourceConfigurationError(
                "YOUTUBE_API_KEY was not found."
            )

        if not concept:

            raise ValueError(
                "A concept is required for YouTube search."
            )

        max_results = max(
            1,
            min(
                max_results,
                self.MAX_YOUTUBE_RESULTS,
            ),
        )

        youtube = (
            self._get_youtube_client()
        )

        query = (
            self._build_search_query(
                concept=concept,
                subject=subject,
                learner_level=learner_level,
                strategy=strategy,
                mistake_type=mistake_type,
                misconception=misconception,
            )
        )

        try:

            response = (
                youtube.search()
                .list(
                    part="snippet",
                    q=query,
                    type="video",
                    maxResults=max_results,
                    videoDuration="medium",
                    videoEmbeddable="true",
                    videoSyndicated="true",
                    videoCaption="closedCaption",
                    safeSearch="strict",
                    relevanceLanguage="en",
                    order="relevance",
                )
                .execute()
            )

        except Exception as exc:

            raise ResourceSearchError(
                f"YouTube search failed: {exc}"
            ) from exc

        candidates = []

        for item in response.get(
            "items",
            [],
        ):

            video_id = (
                item
                .get(
                    "id",
                    {},
                )
                .get(
                    "videoId"
                )
            )

            snippet = item.get(
                "snippet",
                {}
            )

            if not video_id:
                continue

            title = snippet.get(
                "title",
                "",
            )

            description = snippet.get(
                "description",
                "",
            )

            (
                score,
                reasons,
                rejected,
            ) = self._score_video(
                title=title,
                description=description,
                concept=concept,
                subject=subject,
            )

            candidates.append(
                {
                    "type": "youtube",

                    "video_id": video_id,

                    "title": title,

                    "description": description,

                    "channel": snippet.get(
                        "channelTitle"
                    ),

                    "published_at": snippet.get(
                        "publishedAt"
                    ),

                    "thumbnail": (
                        snippet
                        .get(
                            "thumbnails",
                            {}
                        )
                        .get(
                            "high",
                            {}
                        )
                        .get(
                            "url"
                        )
                    ),

                    "url": (
                        "https://www.youtube.com/watch?v="
                        + video_id
                    ),

                    "embed_url": (
                        "https://www.youtube.com/embed/"
                        + video_id
                    ),

                    "search_query": query,

                    "quality_score": score,

                    "quality_reasons": reasons,

                    "rejected": rejected,
                }
            )

        # ----------------------------------------------------
        # Only accepted resources continue.
        # ----------------------------------------------------

        accepted = [
            video
            for video in candidates
            if (
                not video["rejected"]
                and video["quality_score"]
                >= self.MIN_VIDEO_SCORE
            )
        ]

        accepted.sort(
            key=lambda video: (
                video["quality_score"],
                self._educational_score(
                    video
                ),
            ),
            reverse=True,
        )

        return accepted

    # ========================================================
    # RESOURCE BUNDLE
    # ========================================================

    def recommend(
        self,
        concept: str,
        subject: str = "Python",
        learner_level: str = "Beginner",
        strategy: Optional[str] = None,
        mistake_type: Optional[str] = None,
        misconception: Optional[str] = None,
    ) -> Dict[str, Any]:

        quick_tip = (
            self.generate_quick_tip(
                concept=concept,
                mistake_type=mistake_type,
                misconception=misconception,
                learner_level=learner_level,
            )
        )

        videos = []

        try:

            videos = (
                self.search_youtube(
                    concept=concept,
                    subject=subject,
                    learner_level=learner_level,
                    strategy=strategy,
                    mistake_type=mistake_type,
                    misconception=misconception,
                    max_results=10,
                )
            )

        except (
            ResourceConfigurationError,
            ResourceSearchError,
        ):

            # External resources are optional.
            videos = []

        best_video = (
            videos[0]
            if videos
            else None
        )

        if best_video:

            best_video["reason"] = (
                f"Selected because it strongly matches "
                f"the concept '{concept}' and passed "
                f"Sift's resource quality gate."
            )

        return {
            "concept": concept,

            "quick_tip": quick_tip,

            "youtube": best_video,

            "youtube_candidates": videos,

            "has_external_resource": (
                best_video is not None
            ),
        }

    # ========================================================
    # VIDEO QUALITY SCORING
    # ========================================================

    def _score_video(
        self,
        title: str,
        description: str,
        concept: str,
        subject: str,
    ) -> Tuple[int, List[str], bool]:
        """
        Score and validate one candidate.

        Important:

            Concept relevance
                = REQUIRED

            Subject relevance
                = BONUS

            Educational language
                = BONUS

        Therefore:

            Exact concept + educational
                can pass even if the creator did not
                explicitly write the subject.

        This is intentional because a resource such as:

            "Bayes Theorem Explained for Beginners"

        is clearly about the requested concept even if
        the title does not explicitly say "Mathematics".

        However:

            "Python String Operators"

        must NOT pass for:

            "modulo operator"

        because there is no meaningful modulo concept
        signal.
        """

        title_text = (
            self._normalize_text(
                title
            )
        )

        description_text = (
            self._normalize_text(
                description
            )
        )

        full_text = (
            title_text
            + " "
            + description_text
        )

        normalized_concept = (
            self._normalize_text(
                concept
            )
        )

        concept_terms = (
            self._get_concept_terms(
                concept
            )
        )

        subject_terms = (
            self._get_subject_terms(
                subject
            )
        )

        # ====================================================
        # CONCEPT SIGNALS
        # ====================================================

        exact_concept_in_title = (
            bool(normalized_concept)
            and self._phrase_in_text(
                normalized_concept,
                title_text,
            )
        )

        exact_concept_in_description = (
            bool(normalized_concept)
            and self._phrase_in_text(
                normalized_concept,
                description_text,
            )
        )

        title_concept_matches = (
            self._matching_terms(
                title_text,
                concept_terms,
            )
        )

        description_concept_matches = (
            self._matching_terms(
                description_text,
                concept_terms,
            )
        )

        # ====================================================
        # SUBJECT SIGNALS
        # ====================================================

        title_subject_matches = (
            self._matching_terms(
                title_text,
                subject_terms,
            )
        )

        description_subject_matches = (
            self._matching_terms(
                description_text,
                subject_terms,
            )
        )

        # ====================================================
        # EDUCATIONAL SIGNAL
        # ====================================================

        educational_matches = (
            self._matching_terms(
                full_text,
                self.EDUCATIONAL_TERMS,
            )
        )

        # ====================================================
        # SCORE
        # ====================================================

        score = 0

        reasons: List[str] = []

        # ----------------------------------------------------
        # Exact concept in title.
        # ----------------------------------------------------

        if exact_concept_in_title:

            score += 50

            reasons.append(
                "exact concept appears in title"
            )

        # ----------------------------------------------------
        # Exact concept in description.
        # ----------------------------------------------------

        elif exact_concept_in_description:

            score += 25

            reasons.append(
                "exact concept appears in description"
            )

        # ----------------------------------------------------
        # Alias in title.
        # ----------------------------------------------------

        elif title_concept_matches:

            score += 35

            reasons.append(
                "strong concept alias appears in title"
            )

        # ----------------------------------------------------
        # Alias in description.
        # ----------------------------------------------------

        elif description_concept_matches:

            score += 15

            reasons.append(
                "strong concept alias appears in description"
            )

        # ====================================================
        # SUBJECT
        # ====================================================

        if title_subject_matches:

            score += 25

            reasons.append(
                "subject appears in title"
            )

        elif description_subject_matches:

            score += 10

            reasons.append(
                "subject appears in description"
            )

        # ====================================================
        # EDUCATIONAL LANGUAGE
        # ====================================================

        if educational_matches:

            score += 10

            reasons.append(
                "educational language detected"
            )

        # ====================================================
        # CONCEPT REINFORCED BY DESCRIPTION
        # ====================================================

        has_title_concept = (
            exact_concept_in_title
            or bool(
                title_concept_matches
            )
        )

        has_description_concept = (
            exact_concept_in_description
            or bool(
                description_concept_matches
            )
        )

        if (
            has_title_concept
            and has_description_concept
        ):

            score += 10

            reasons.append(
                "concept reinforced by description"
            )

        # ====================================================
        # HARD CONCEPT GATE
        # ====================================================

        has_concept_signal = (
            exact_concept_in_title
            or exact_concept_in_description
            or bool(
                title_concept_matches
            )
            or bool(
                description_concept_matches
            )
        )

        rejected = False

        # ----------------------------------------------------
        # NO CONCEPT = ALWAYS REJECT
        # ----------------------------------------------------

        if not has_concept_signal:

            rejected = True

            reasons.append(
                "REJECTED: no meaningful concept signal"
            )

        # ====================================================
        # SUBJECT GATE
        # ====================================================

        has_subject_signal = (
            bool(title_subject_matches)
            or bool(description_subject_matches)
        )

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # Subject is NOT a hard rejection condition anymore.
        #
        # The test suite explicitly expects:
        #
        # probability
        # +
        # Mathematics
        # +
        # "Probability in Machine Learning Explained"
        #
        # to pass.
        #
        # Exact concept relevance is therefore sufficient.
        # Subject relevance affects the score only.
        # ----------------------------------------------------

        if (
            not has_subject_signal
            and has_concept_signal
        ):

            reasons.append(
                "subject not explicitly signaled; "
                "exact concept relevance accepted"
            )

        # ====================================================
        # WEAK ALIAS PROTECTION
        # ====================================================

        # ----------------------------------------------------
        # For unknown concepts, exact phrase matching is safe.
        #
        # For known concepts, aliases are trusted.
        #
        # But a single generic alias must not make a video pass.
        # ----------------------------------------------------

        if (
            not exact_concept_in_title
            and not exact_concept_in_description
            and title_concept_matches
            and len(
                title_concept_matches
            ) == 1
        ):

            only_match = next(
                iter(
                    title_concept_matches
                )
            )

            normalized_only_match = (
                self._normalize_text(
                    only_match
                )
            )

            # ------------------------------------------------
            # A one-word alias is less reliable than an exact
            # multi-word concept.
            # ------------------------------------------------

            if (
                len(
                    normalized_only_match.split()
                ) == 1
                and normalized_concept
                and len(
                    normalized_concept.split()
                ) > 1
            ):

                rejected = True

                reasons.append(
                    "REJECTED: weak ambiguous concept match"
                )

        # ====================================================
        # FINAL SCORE GATE
        # ====================================================

        if score < self.MIN_VIDEO_SCORE:

            rejected = True

            reasons.append(
                "REJECTED: score below quality threshold"
            )

        return (
            score,
            reasons,
            rejected,
        )

    # ========================================================
    # EDUCATIONAL SCORE
    # ========================================================

    def _educational_score(
        self,
        video: Dict[str, Any],
    ) -> int:

        reasons = video.get(
            "quality_reasons",
            []
        )

        if (
            "educational language detected"
            in reasons
        ):

            return 1

        return 0

    # ========================================================
    # SEARCH QUERY
    # ========================================================

    def _build_search_query(
        self,
        concept: str,
        subject: str,
        learner_level: str,
        strategy: Optional[str],
        mistake_type: Optional[str],
        misconception: Optional[str],
    ) -> str:
        """
        Build a focused YouTube search query.

        The misconception itself is not blindly inserted into
        the query because that can make searches noisy.
        """

        parts = [
            str(subject).strip(),
            str(concept).strip(),
            "explained",
        ]

        if learner_level:

            parts.append(
                str(
                    learner_level
                ).strip()
            )

        # ----------------------------------------------------
        # Strategy hints.
        # ----------------------------------------------------

        if strategy:

            strategy_map = {

                "visual_explanation":
                    "visual explanation",

                "worked_example":
                    "worked example",

                "analogy":
                    "analogy explanation",

                "socratic":
                    "concept explanation",

                "practice_first":
                    "practice examples",
            }

            parts.append(
                strategy_map.get(
                    strategy,
                    strategy.replace(
                        "_",
                        " ",
                    ),
                )
            )

        # ----------------------------------------------------
        # Mistake type.
        # ----------------------------------------------------

        if mistake_type:

            parts.append(
                str(
                    mistake_type
                ).strip()
            )

        # ----------------------------------------------------
        # Concept-specific search terms.
        # ----------------------------------------------------

        normalized = (
            self._normalize_text(
                concept
            )
        )

        if normalized in {
            "modulo",
            "modulo operator",
            "modulo operator %",
        }:

            parts.append(
                "remainder"
            )

        elif normalized == "call stack":

            parts.append(
                "function calls"
            )

        elif normalized == "binary search":

            parts.append(
                "sorted array"
            )

        elif normalized == "gradient descent":

            parts.append(
                "optimization"
            )

        elif normalized == "derivative":

            parts.append(
                "calculus"
            )

        parts.append(
            "tutorial"
        )

        return " ".join(
            part
            for part in parts
            if part
        )

    # ========================================================
    # GET CONCEPT TERMS
    # ========================================================

    def _get_concept_terms(
        self,
        concept: str,
    ) -> Set[str]:

        normalized = (
            self._normalize_text(
                concept
            )
        )

        aliases = (
            self.CONCEPT_ALIASES.get(
                normalized
            )
        )

        if aliases:

            return set(
                aliases
            )

        # ----------------------------------------------------
        # UNKNOWN CONCEPT FALLBACK
        #
        # This is the important fix for:
        #
        #     Bayes theorem
        #
        # If it isn't in our alias table, use the exact
        # normalized phrase.
        # ----------------------------------------------------

        if normalized:

            return {
                normalized
            }

        return set()

    # ========================================================
    # GET SUBJECT TERMS
    # ========================================================

    def _get_subject_terms(
        self,
        subject: str,
    ) -> Set[str]:

        normalized = (
            self._normalize_text(
                subject
            )
        )

        aliases = (
            self.SUBJECT_ALIASES.get(
                normalized
            )
        )

        if aliases:

            return set(
                aliases
            )

        if normalized:

            return {
                normalized
            }

        return set()

    # ========================================================
    # NORMALIZE TEXT
    # ========================================================

    def _normalize_text(
        self,
        text: str,
    ) -> str:
        """
        Normalize text for safe matching.

        Examples:

            "Binary-Search!"
                →
            "binary search"

            "Data Structures & Algorithms"
                →
            "data structures algorithms"
        """

        if not isinstance(
            text,
            str,
        ):

            return ""

        text = text.lower()

        text = (
            text
            .replace(
                "’",
                "'",
            )
            .replace(
                "`",
                "'",
            )
        )

        text = re.sub(
            r"[^a-z0-9%]+",
            " ",
            text,
        )

        return " ".join(
            text.split()
        )

    # ========================================================
    # PHRASE MATCHING
    # ========================================================

    def _phrase_in_text(
        self,
        phrase: str,
        text: str,
    ) -> bool:

        if not phrase or not text:

            return False

        normalized_phrase = (
            self._normalize_text(
                phrase
            )
        )

        normalized_text = (
            self._normalize_text(
                text
            )
        )

        if not normalized_phrase:

            return False

        return (
            normalized_phrase
            in normalized_text
        )

    # ========================================================
    # TERM MATCHING
    # ========================================================

    def _matching_terms(
        self,
        text: str,
        terms: Set[str],
    ) -> Set[str]:
        """
        Safely match aliases.

        Multi-word aliases:
            phrase matching

        Single-word aliases:
            complete-token matching

        This avoids substring mistakes such as:

            "stack" matching "stacked"

        """

        if not text or not terms:

            return set()

        normalized_text = (
            self._normalize_text(
                text
            )
        )

        text_tokens = set(
            normalized_text.split()
        )

        matches: Set[str] = set()

        for term in terms:

            normalized_term = (
                self._normalize_text(
                    term
                )
            )

            if not normalized_term:

                continue

            # ------------------------------------------------
            # Multi-word phrase.
            # ------------------------------------------------

            if " " in normalized_term:

                if (
                    normalized_term
                    in normalized_text
                ):

                    matches.add(
                        term
                    )

                continue

            # ------------------------------------------------
            # Single token.
            # ------------------------------------------------

            if (
                normalized_term
                in text_tokens
            ):

                matches.add(
                    term
                )

        return matches

    # ========================================================
    # YOUTUBE CLIENT
    # ========================================================

    def _get_youtube_client(self):

        if self._youtube is not None:

            return self._youtube

        try:

            from googleapiclient.discovery import (
                build
            )

        except ImportError as exc:

            raise ResourceConfigurationError(
                "google-api-python-client is not installed. "
                "Run: python -m pip install "
                "google-api-python-client"
            ) from exc

        self._youtube = build(
            "youtube",
            "v3",
            developerKey=self.youtube_api_key,
        )

        return self._youtube