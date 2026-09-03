"""
Sift Dynamic Content Engine.

Pipeline:

    AdaptiveEngine
          ↓
       TaskSpec
          ↓
    ContentEngine
          ↓
    GeminiProvider
          ↓
    Structural Validation
          ↓
    Novelty Validation
          ↓
    Valid Learning Task
"""

import json
import re

from core.task_spec import TaskSpec


class ContentGenerationError(Exception):
    """Raised when dynamic content cannot be generated safely."""


class ContentValidationError(ContentGenerationError):
    """Raised when generated content fails validation."""


class ContentEngine:
    """
    Generates and validates adaptive learning tasks.

    The engine is responsible for:
        - converting adaptive recommendations into TaskSpec
        - generating content through the configured model
        - validating generated content
        - checking novelty against previous tasks
        - retrying invalid generations
        - preventing obvious task repetition
    """

    QUESTION_TYPES = {
        "short_answer",
        "code_prediction",
        "code_completion",
        "debugging",
        "multiple_choice",
        "trace_execution",
        "explain_reasoning",
        "transfer",
        "open_ended",
    }

    DIFFICULTIES = {
        "easy",
        "medium",
        "hard",
        "adaptive",
    }

    NOVELTY_LEVELS = {
        "familiar",
        "normal",
        "novel",
        "transfer",
    }

    REQUIRED_TASK_FIELDS = {
        "title",
        "question",
        "context",
        "hints",
        "success_signal",
        "expected_answer_type",
        "difficulty",
        "question_type",
        "learning_guide",
    }

    MAX_GENERATION_ATTEMPTS = 3

    def __init__(
        self,
        model=None,
        strict=True,
        allow_fallback=True,
    ):
        self.model = model
        self.strict = strict
        self.allow_fallback = allow_fallback

    # ============================================================
    # TASK SPECIFICATION
    # ============================================================

    def build_task_spec(
        self,
        learner,
        recommendation,
        concept,
        previous_tasks=None,
        remaining_minutes=None,
    ):
        action = recommendation.get(
            "action",
            "practice",
        )

        strategy = recommendation.get(
            "strategy",
            "worked_example",
        )

        mastery = float(
            recommendation.get(
                "mastery",
                getattr(
                    concept,
                    "mastery",
                    0,
                ),
            )
        )

        confidence = float(
            recommendation.get(
                "confidence",
                getattr(
                    concept,
                    "confidence",
                    0,
                ),
            )
        )

        misconception = self._latest_misconception(
            concept
        )

        difficulty = self._choose_difficulty(
            mastery,
            confidence,
            action,
        )

        question_type = self._choose_question_type(
            action,
            strategy,
            mastery,
        )

        novelty = self._choose_novelty(
            action,
            mastery,
        )

        objective = self._build_objective(
            action,
            concept.name,
        )

        target_skill = self._build_target_skill(
            action,
            concept.name,
            question_type,
        )

        constraints = [
            "Stay within the learner's current level.",
            "Do not assume knowledge of concepts outside the provided context.",
            "Use Python when the subject is Python.",
            "Return one clearly answerable task.",
            "Do not reveal the answer in the question.",
            "Do not use unnecessary advanced concepts.",
        ]

        if misconception:
            constraints.append(
                "Probe the known misconception without simply copying the previous task."
            )

        if novelty in {
            "novel",
            "transfer",
        }:
            constraints.append(
                "Use a meaningfully different example from previous tasks."
            )

            constraints.append(
                "Do not reuse the same numbers, variable values, code snippet, scenario, or wording from a previous task."
            )

        context = self._build_context(
            learner,
            concept,
            recommendation,
        )

        previous_task_data = self._summarize_previous_tasks(
            previous_tasks
        )

        metadata = {
            "subject": getattr(
                learner,
                "subject",
                "",
            ),
            "learning_purpose": getattr(learner, "learning_purpose", "Coursework"),
            "previous_tasks": previous_task_data,
        }
        if remaining_minutes is not None:
            try:
                metadata["remaining_minutes"] = max(0.0, float(remaining_minutes))
            except (TypeError, ValueError):
                metadata["remaining_minutes"] = 0.0

        return TaskSpec(
            concept=concept.name,
            action=action,
            strategy=strategy,
            difficulty=difficulty,
            objective=objective,
            target_skill=target_skill,
            question_type=question_type,
            misconception=misconception,
            target_concept=recommendation.get(
                "target_concept"
            ),
            diagnosis=recommendation.get(
                "diagnosis"
            ),
            learner_goal=getattr(
                learner,
                "goal",
                "",
            ),
            learner_level=getattr(
                learner,
                "current_level",
                "Beginner",
            ),
            mastery=mastery,
            confidence=confidence,
            novelty=novelty,
            context=context,
            constraints=constraints,
            metadata=metadata,
        )

    # ============================================================
    # PUBLIC GENERATION
    # ============================================================

    def generate(
        self,
        learner,
        recommendation,
        concept,
        previous_tasks=None,
        remaining_minutes=None,
    ):
        """Generate one validated learning task, with a safe offline fallback."""
        spec = self.build_task_spec(
            learner=learner,
            recommendation=recommendation,
            concept=concept,
            previous_tasks=previous_tasks,
            remaining_minutes=remaining_minutes,
        )
        prompt = self.build_prompt(spec)
        last_error = None

        for attempt in range(1, self.MAX_GENERATION_ATTEMPTS + 1):
            try:
                if self.model is None:
                    if not self.allow_fallback:
                        raise ContentGenerationError("No content model is configured.")
                    task = self._fallback_task(spec, previous_tasks=previous_tasks)
                else:
                    task = self._parse_task(self._call_model(prompt), spec)

                if self.strict:
                    self.validate_task(task, spec)
                    self.validate_novelty(task, spec, previous_tasks)

                return {
                    "spec": spec.to_dict(),
                    "task": task,
                    "prompt": prompt,
                    "generated_by": "fallback" if task.get("generation_fallback") else "llm",
                    "generation_attempts": attempt,
                }
            except Exception as exc:
                # Provider failures, malformed JSON, and content validation failures
                # must not strand the learner when deterministic content is safe.
                last_error = exc
                prompt = self._build_retry_prompt(spec, prompt, exc, attempt)

        if self.allow_fallback:
            try:
                task = self._fallback_task(spec, previous_tasks=previous_tasks)
                if self.strict:
                    self.validate_task(task, spec)
                    self.validate_novelty(task, spec, previous_tasks)
                return {
                    "spec": spec.to_dict(),
                    "task": task,
                    "prompt": prompt,
                    "generated_by": "fallback",
                    "generation_attempts": self.MAX_GENERATION_ATTEMPTS + 1,
                    "fallback_reason": str(last_error or "model unavailable"),
                }
            except Exception as fallback_error:
                last_error = fallback_error

        raise ContentGenerationError(
            "Unable to generate a valid learning task after "
            f"{self.MAX_GENERATION_ATTEMPTS} attempts: {last_error}"
        ) from last_error

    # ============================================================
    # MODEL
    # ============================================================

    def _call_model(
        self,
        prompt,
    ):
        if hasattr(
            self.model,
            "generate",
        ):
            return self.model.generate(
                prompt
            )

        if callable(
            self.model
        ):
            return self.model(
                prompt
            )

        raise TypeError(
            "Content model must provide "
            "generate(prompt) or be callable."
        )

    # ============================================================
    # PROMPT
    # ============================================================

    def build_prompt(
        self,
        spec,
    ):
        payload = json.dumps(
            spec.to_dict(),
            indent=2,
            ensure_ascii=False,
        )

        return f"""
You are Sift's adaptive learning content generator.

Generate ONE learning task for the learner.

The Adaptive Engine has already decided what
the learner needs to work on.

Do NOT change the concept.

TASK SPECIFICATION:

{payload}

STRICT RULES:

1. Generate exactly ONE task.
2. Stay at the requested learner level.
3. Respect the requested difficulty.
4. Respect the requested strategy.
5. Respect the requested question type.
6. Target the supplied misconception if one exists.
7. Do not simply repeat a previous task.
8. If novelty is "novel" or "transfer", create
   a genuinely different task.
9. Do NOT reuse previous numbers.
10. Do NOT reuse previous variable values.
11. Do NOT reuse previous code snippets.
12. Do NOT reuse the same surface scenario.
13. Do NOT merely change wording.
14. Keep testing the same underlying concept.
15. Use valid Python when the subject is Python.
16. Do not reveal the answer.
17. Do not invent unnecessary prerequisites.
18. The task must have an objectively assessable
    success condition.
19. Keep the task concise.
20. Return ONLY valid JSON.
21. Do not wrap JSON in Markdown code fences.
22. Include a short learning guide before the task.
23. The worked example MUST use different values/scenarios from the task.
24. The learning guide must teach the concept, not merely describe the task.
25. The guide must not reveal or imply the exact answer to the task.
26. If remaining session time is provided, keep the task proportional to that time.

For novel or transfer tasks, the previous tasks
listed in the specification are examples that
MUST NOT be copied.

Return exactly:

{{
  "title": "short task title",
  "question": "the learner-facing question",
  "context": "brief context if needed",
  "hints": [],
  "success_signal": "what a correct answer demonstrates",
  "expected_answer_type": "short answer / code / explanation / etc",
  "difficulty": "easy | medium | hard",
  "question_type": "one of the requested question types",
  "learning_guide": {{
    "explanation": "a concise teaching explanation of the concept",
    "worked_example": "a different example that teaches the idea without solving the task",
    "hint": "a first hint that nudges the learner without revealing the answer"
  }}
}}
""".strip()

    # ============================================================
    # RETRY PROMPT
    # ============================================================

    def _build_retry_prompt(
        self,
        spec,
        original_prompt,
        error,
        attempt,
    ):
        return f"""
{original_prompt}

IMPORTANT RETRY:

Generation attempt {attempt} failed validation.

Reason:

{error}

Generate a NEW task.

The new task must not reuse:
- the same numbers
- the same code
- the same variable values
- the same scenario
- the same wording pattern

Keep the underlying concept and learning objective
unchanged.

Return ONLY valid JSON.
""".strip()

    # ============================================================
    # PARSING
    # ============================================================

    def _parse_task(
        self,
        raw,
        spec,
    ):
        if isinstance(
            raw,
            dict,
        ):
            data = raw

        else:
            text = str(
                raw
            ).strip()

            text = self._strip_code_fences(
                text
            )

            try:
                data = json.loads(
                    text
                )

            except json.JSONDecodeError as exc:
                raise ContentValidationError(
                    "Gemini returned invalid JSON."
                ) from exc

        return self._normalize_task(
            data,
            spec,
        )

    @staticmethod
    def _strip_code_fences(
        text,
    ):
        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"\s*```$",
            "",
            text,
        )

        return text.strip()

    # ============================================================
    # NORMALIZATION
    # ============================================================

    def _normalize_task(
        self,
        data,
        spec,
    ):
        if not isinstance(
            data,
            dict,
        ):
            raise ContentValidationError(
                "Generated task is not a JSON object."
            )

        missing = (
            self.REQUIRED_TASK_FIELDS
            - {"learning_guide"}
            - set(data.keys())
        )

        if missing:
            raise ContentValidationError(
                "Generated task is missing fields: "
                + ", ".join(
                    sorted(missing)
                )
            )

        hints = data[
            "hints"
        ]

        if hints is None:
            hints = []

        if not isinstance(
            hints,
            list,
        ):
            raise ContentValidationError(
                "'hints' must be a list."
            )

        difficulty = data[
            "difficulty"
        ]

        if difficulty not in self.DIFFICULTIES:
            raise ContentValidationError(
                f"Invalid difficulty: {difficulty}"
            )

        question_type = data[
            "question_type"
        ]

        if question_type not in self.QUESTION_TYPES:
            raise ContentValidationError(
                f"Invalid question_type: "
                f"{question_type}"
            )

        guide = data.get("learning_guide") or {}
        if not isinstance(guide, dict):
            raise ContentValidationError("'learning_guide' must be an object.")

        # Backward compatibility: older deterministic providers/tests may not
        # return the new guide fields. The learner still gets real teaching
        # material derived from the task context rather than an empty panel.
        learning_guide = {
            "explanation": str(guide.get("explanation") or data.get("context") or f"Focus on the core rule behind {spec.concept}.").strip(),
            "worked_example": str(guide.get("worked_example") or f"Worked example: apply {spec.concept} to a simple case, then explain why the rule produces that result.").strip(),
            "hint": str(guide.get("hint") or "Start by stating the core rule, then apply it step by step to the situation.").strip(),
        }

        task = {
            "title": str(
                data["title"]
            ).strip(),

            "question": str(
                data["question"]
            ).strip(),

            "context": str(
                data["context"]
            ).strip(),

            "hints": [
                str(
                    hint
                ).strip()
                for hint in hints
            ],

            "success_signal": str(
                data["success_signal"]
            ).strip(),

            "expected_answer_type": str(
                data["expected_answer_type"]
            ).strip(),

            "difficulty": difficulty,

            "question_type": question_type,

            "learning_guide": learning_guide,

            "concept": spec.concept,

            "strategy": spec.strategy,

            "action": spec.action,
        }

        self._validate_required_strings(
            task
        )

        return task

    # ============================================================
    # REQUIRED STRING VALIDATION
    # ============================================================

    def _validate_required_strings(
        self,
        task,
    ):
        """
        Ensure all required learner-facing fields
        contain usable text.
        """

        required_strings = {
            "title",
            "question",
            "context",
            "success_signal",
            "expected_answer_type",
            "difficulty",
            "question_type",
        }

        for field in required_strings:
            value = task.get(
                field
            )

            if not isinstance(
                value,
                str,
            ):
                raise ContentValidationError(
                    f"Task field '{field}' "
                    f"must be a string."
                )

            if not value.strip():
                raise ContentValidationError(
                    f"Task field '{field}' "
                    f"cannot be empty."
                )

        hints = task.get(
            "hints"
        )

        if not isinstance(
            hints,
            list,
        ):
            raise ContentValidationError(
                "Task field 'hints' "
                "must be a list."
            )

        for index, hint in enumerate(
            hints
        ):
            if not isinstance(
                hint,
                str,
            ):
                raise ContentValidationError(
                    f"Hint {index} "
                    f"must be a string."
                )

            if not hint.strip():
                raise ContentValidationError(
                    f"Hint {index} "
                    f"cannot be empty."
                )

        return True

    # ============================================================
    # STRUCTURAL VALIDATION
    # ============================================================

    def validate_task(
        self,
        task,
        spec,
    ):
        if not isinstance(
            task,
            dict,
        ):
            raise ContentValidationError(
                "Task must be a dictionary."
            )

        # Accept legacy task payloads at this boundary and enrich them with
        # the teaching contract. New LLM generations are still required to
        # request the full guide in the prompt.
        if "learning_guide" not in task:
            task["learning_guide"] = {
                "explanation": str(task.get("context") or f"Focus on the core rule behind {spec.concept}.").strip(),
                "worked_example": f"Apply {spec.concept} to a simple example and explain the reasoning.",
                "hint": "Start with the core rule, then apply it step by step.",
            }

        missing = (
            self.REQUIRED_TASK_FIELDS
            - set(task.keys())
        )

        if missing:
            raise ContentValidationError(
                "Task missing required fields: "
                + ", ".join(
                    sorted(missing)
                )
            )

        self._validate_required_strings(
            task
        )

        if task.get(
            "concept"
        ) != spec.concept:
            raise ContentValidationError(
                "Generated task changed the target concept."
            )

        if task.get(
            "strategy"
        ) != spec.strategy:
            raise ContentValidationError(
                "Generated task changed the adaptive strategy."
            )

        if task.get(
            "action"
        ) != spec.action:
            raise ContentValidationError(
                "Generated task changed the adaptive action."
            )

        if task.get(
            "difficulty"
        ) not in self.DIFFICULTIES:
            raise ContentValidationError(
                "Generated task has invalid difficulty."
            )

        if task.get(
            "question_type"
        ) not in self.QUESTION_TYPES:
            raise ContentValidationError(
                "Generated task has invalid question type."
            )

        guide = task.get("learning_guide")
        if not isinstance(guide, dict) or not all(
            isinstance(guide.get(k), str) and guide.get(k).strip()
            for k in ("explanation", "worked_example", "hint")
        ):
            raise ContentValidationError("Task learning_guide must contain explanation, worked_example, and hint.")

        hints = task.get(
            "hints"
        )

        if not isinstance(
            hints,
            list,
        ):
            raise ContentValidationError(
                "Task hints must be a list."
            )

        if len(
            task["question"]
        ) < 10:
            raise ContentValidationError(
                "Generated question is too short."
            )

        if len(
            task["title"]
        ) < 3:
            raise ContentValidationError(
                "Generated title is too short."
            )

        if len(
            task["success_signal"]
        ) < 5:
            raise ContentValidationError(
                "Success signal is too short."
            )

        # Prevent a model from returning a structurally valid but semantically
        # unrelated task (for example, an array-indexing question while the
        # learner is explicitly working on recursion). A task only needs one
        # meaningful concept signal because good questions may use synonyms or
        # an application context instead of repeating the full concept name.
        concept_text = str(spec.concept or "").lower()
        task_text = " ".join(
            str(task.get(field) or "")
            for field in ("title", "question", "context", "success_signal")
        ).lower()
        concept_tokens = [
            token for token in re.findall(r"[a-z0-9]+", concept_text)
            if len(token) >= 4
        ]
        alias_tokens = {
            "recursion": {"recursive", "recursion"},
            "binary search": {"binary", "search"},
            "linked lists": {"linked", "list", "lists"},
            "data preparation": {"preparation", "preprocessing", "preprocess"},
            "feature engineering": {"feature", "engineering"},
            "machine learning": {"machine", "learning"},
            "object oriented programming": {"object", "oriented", "oop"},
        }.get(concept_text, set())
        concept_signals = set(concept_tokens) | alias_tokens
        task_tokens = set(re.findall(r"[a-z0-9]+", task_text))
        normalized_task_tokens = set(task_tokens)
        for token in list(task_tokens):
            if len(token) > 4 and token.endswith("s"):
                normalized_task_tokens.add(token[:-1])
        signal_match = False
        for token in concept_signals:
            if token in normalized_task_tokens:
                signal_match = True
                break
            if len(token) > 4 and token.endswith("s") and token[:-1] in normalized_task_tokens:
                signal_match = True
                break
        if concept_signals and not signal_match:
            raise ContentValidationError(
                f"Generated task does not contain a meaningful signal for concept '{spec.concept}'."
            )

        forbidden = {
            "answer",
            "correct_answer",
            "solution",
            "final_answer",
        }

        unexpected = (
            forbidden
            & set(task.keys())
        )

        if unexpected:
            raise ContentValidationError(
                "Generated task contains forbidden "
                "answer fields: "
                + ", ".join(
                    sorted(unexpected)
                )
            )

        return True

    # ============================================================
    # NOVELTY VALIDATION
    # ============================================================

    def validate_novelty(
        self,
        task,
        spec,
        previous_tasks=None,
    ):
        """
        Validate that novel/transfer content is not
        an obvious repetition of an earlier task.
        """

        if spec.novelty not in {
            "novel",
            "transfer",
        }:
            return True

        if not previous_tasks:
            return True

        current_question = (
            self._normalize_for_comparison(
                task.get(
                    "question",
                    "",
                )
            )
        )

        current_title = (
            self._normalize_for_comparison(
                task.get(
                    "title",
                    "",
                )
            )
        )

        for previous in previous_tasks:
            previous_question = (
                self._extract_previous_question(
                    previous
                )
            )

            previous_title = (
                self._extract_previous_title(
                    previous
                )
            )

            normalized_question = (
                self._normalize_for_comparison(
                    previous_question
                )
            )

            normalized_title = (
                self._normalize_for_comparison(
                    previous_title
                )
            )

            # ----------------------------------------------------
            # Exact normalized duplicate
            # ----------------------------------------------------

            if (
                current_question
                and current_question
                == normalized_question
            ):
                raise ContentValidationError(
                    "Generated task repeats a "
                    "previous question."
                )

            # ----------------------------------------------------
            # Same numeric example
            # ----------------------------------------------------

            current_numbers = (
                self._extract_numbers(
                    current_question
                )
            )

            previous_numbers = (
                self._extract_numbers(
                    normalized_question
                )
            )

            if (
                current_numbers
                and previous_numbers
                and current_numbers
                == previous_numbers
            ):
                raise ContentValidationError(
                    "Generated task reuses the "
                    "same numeric example as a "
                    "previous task."
                )

            # ----------------------------------------------------
            # Strong phrase overlap
            # ----------------------------------------------------

            similarity = (
                self._token_similarity(
                    current_question,
                    normalized_question,
                )
            )

            if similarity >= 0.85:
                raise ContentValidationError(
                    "Generated task is too similar "
                    "to a previous task."
                )

            # ----------------------------------------------------
            # Title repetition
            # ----------------------------------------------------

            if (
                current_title
                and normalized_title
                and current_title
                == normalized_title
            ):
                raise ContentValidationError(
                    "Generated task reuses a "
                    "previous task title."
                )

        return True

    # ============================================================
    # PREVIOUS TASK HANDLING
    # ============================================================

    def _summarize_previous_tasks(
        self,
        previous_tasks,
    ):
        if not previous_tasks:
            return []

        summaries = []

        for task in previous_tasks:
            if isinstance(
                task,
                dict,
            ):
                question = (
                    self._extract_previous_question(
                        task
                    )
                )

                title = (
                    self._extract_previous_title(
                        task
                    )
                )

                summaries.append({
                    "title": title,
                    "question": question,
                })

        # Keep prompts reasonably sized.
        return summaries[-5:]

    @staticmethod
    def _extract_previous_question(
        previous,
    ):
        if not isinstance(
            previous,
            dict,
        ):
            return ""

        if "question" in previous:
            return str(
                previous.get(
                    "question",
                    "",
                )
            )

        nested = previous.get(
            "task"
        )

        if isinstance(
            nested,
            dict,
        ):
            return str(
                nested.get(
                    "question",
                    "",
                )
            )

        return ""

    @staticmethod
    def _extract_previous_title(
        previous,
    ):
        if not isinstance(
            previous,
            dict,
        ):
            return ""

        if "title" in previous:
            return str(
                previous.get(
                    "title",
                    "",
                )
            )

        nested = previous.get(
            "task"
        )

        if isinstance(
            nested,
            dict,
        ):
            return str(
                nested.get(
                    "title",
                    "",
                )
            )

        return ""

    # ============================================================
    # TEXT COMPARISON
    # ============================================================

    @staticmethod
    def _normalize_for_comparison(
        text,
    ):
        text = str(
            text or ""
        ).lower()

        text = re.sub(
            r"```.*?```",
            " ",
            text,
            flags=re.DOTALL,
        )

        text = re.sub(
            r"[^a-z0-9%]+",
            " ",
            text,
        )

        return " ".join(
            text.split()
        )

    @staticmethod
    def _extract_numbers(
        text,
    ):
        return tuple(
            re.findall(
                r"(?<![a-z])\d+(?:\.\d+)?(?![a-z])",
                text,
            )
        )

    @staticmethod
    def _token_similarity(
        first,
        second,
    ):
        first_tokens = set(
            first.split()
        )

        second_tokens = set(
            second.split()
        )

        if not first_tokens or not second_tokens:
            return 0.0

        intersection = (
            first_tokens
            & second_tokens
        )

        union = (
            first_tokens
            | second_tokens
        )

        return (
            len(intersection)
            / len(union)
        )

    # ============================================================
    # DIFFICULTY
    # ============================================================

    def _choose_difficulty(
        self,
        mastery,
        confidence,
        action,
    ):
        if action == "teach":
            return "easy"

        if action == "review":
            return "medium"

        if action == "challenge":
            return "hard"

        if confidence < 40:
            return "easy"

        if mastery < 60:
            return "easy"

        if mastery < 80:
            return "medium"

        return "hard"

    # ============================================================
    # QUESTION TYPE
    # ============================================================

    def _choose_question_type(
        self,
        action,
        strategy,
        mastery,
    ):
        if action == "teach":
            if strategy == "worked_example":
                return "trace_execution"

            if strategy == "visual_explanation":
                return "explain_reasoning"

            return "short_answer"

        if action == "review":
            return "short_answer"

        if action == "challenge":
            return "transfer"

        if mastery >= 65:
            return "code_prediction"

        return "short_answer"

    # ============================================================
    # NOVELTY
    # ============================================================

    def _choose_novelty(
        self,
        action,
        mastery,
    ):
        if action == "teach":
            return "familiar"

        if action == "review":
            return "normal"

        if action == "challenge":
            return "transfer"

        if mastery >= 65:
            return "novel"

        return "normal"

    # ============================================================
    # OBJECTIVE
    # ============================================================

    def _build_objective(
        self,
        action,
        concept,
    ):
        if action == "teach":
            return (
                f"Build a reliable mental model "
                f"of {concept}."
            )

        if action == "review":
            return (
                f"Retrieve {concept} from memory "
                f"without fresh teaching."
            )

        if action == "challenge":
            return (
                f"Apply {concept} in an unfamiliar "
                f"and more demanding situation."
            )

        return (
            f"Strengthen practical use of "
            f"{concept}."
        )

    # ============================================================
    # TARGET SKILL
    # ============================================================

    def _build_target_skill(
        self,
        action,
        concept,
        question_type,
    ):
        mapping = {
            "trace_execution": (
                "Trace how the concept behaves "
                "during execution."
            ),

            "code_prediction": (
                "Predict program behavior "
                "before execution."
            ),

            "code_completion": (
                "Construct missing code using "
                "the concept."
            ),

            "debugging": (
                "Identify and repair an error "
                "related to the concept."
            ),

            "explain_reasoning": (
                "Explain why the concept behaves "
                "the way it does."
            ),

            "transfer": (
                "Transfer the concept to a "
                "new situation."
            ),

            "short_answer": (
                f"Explain or apply {concept} "
                "correctly."
            ),
        }

        return mapping.get(
            question_type,
            mapping["short_answer"],
        )

    # ============================================================
    # CONTEXT
    # ============================================================

    def _build_context(
        self,
        learner,
        concept,
        recommendation,
    ):
        return (
            f"Learner level: "
            f"{getattr(learner, 'current_level', 'Beginner')}. "
            f"Subject: "
            f"{getattr(learner, 'subject', '')}. "
            f"Learning purpose: "
            f"{getattr(learner, 'learning_purpose', 'Coursework')}. "
            f"Target concept: "
            f"{concept.name}. "
            f"Adaptive diagnosis: "
            f"{recommendation.get('diagnosis', '')}."
        )

    # ============================================================
    # MISCONCEPTION
    # ============================================================

    def _latest_misconception(
        self,
        concept,
    ):
        mistakes = getattr(
            concept,
            "mistakes",
            [],
        )

        if not mistakes:
            return None

        return mistakes[-1]

    # ============================================================
    # FALLBACK
    # ============================================================

    def _fallback_task(self, spec, previous_tasks=None):
        """Build deterministic, concept-specific teaching when the model is unavailable."""
        previous_tasks = previous_tasks or []
        variant = len(previous_tasks) + 1
        subject = str(spec.metadata.get("subject", "programming"))
        concept_key = str(spec.concept).strip().lower()

        lessons = {
            "stack": (
                "A stack follows LIFO: the last item pushed is the first item popped.",
                "If you push A, then B, then C, the next pop removes C because C is on top.",
                "Ask which item was added most recently and is therefore on top.",
            ),
            "queues": (
                "A queue follows FIFO: the first item added is the first item removed.",
                "If A, B, and C enter a queue in that order, removing one item removes A first.",
                "Find the item that has been waiting the longest.",
            ),
            "variables": (
                "A variable is a named reference to a value. A later assignment changes the current value associated with that name.",
                "If x = 3 and later x = 8, reading x after the second assignment gives 8.",
                "Track the current value after each assignment.",
            ),
            "functions": (
                "A function packages a reusable operation. Parameters receive inputs and a return statement can produce a result.",
                "A function double(n) returning n * 2 gives 8 when called with 4.",
                "Identify the input, operation, and returned result.",
            ),
            "modulo operator": (
                "The modulo operator % returns the remainder left after integer division.",
                "17 % 5 is 2 because 5 fits into 17 three full times, leaving 2.",
                "Find the largest number of complete groups first; the leftover is the remainder.",
            ),
            "loops": (
                "A loop repeats instructions according to its iteration or condition rule.",
                "A loop over [2, 4, 6] visits three values, so the body runs three times.",
                "Count the values that will actually be visited.",
            ),
            "recursion": (
                "Recursion solves a problem by calling the same function on a smaller version until a base case stops the calls.",
                "Factorial can reduce 4! to 4 × 3!, then continue until the base case.",
                "Find both the smaller recursive call and the stopping base case.",
            ),
            "binary search": (
                "Binary search repeatedly halves a sorted search space and discards the half that cannot contain the target.",
                "Checking the middle of a sorted list can eliminate roughly half the candidates after one comparison.",
                "Compare the middle value with the target, then keep only the possible half.",
            ),
        }
        explanation, example, hint = lessons.get(
            concept_key,
            (
                f"{spec.concept} is best understood by identifying its defining rule, "
                "then tracing that rule through a concrete example.",
                f"Worked example: start with a small {subject} situation involving {spec.concept}. "
                "State the starting point, apply the rule once, and explain the result.",
                f"State the defining rule of {spec.concept}, then apply it step by step.",
            ),
        )

        if concept_key == "modulo operator":
            scenarios = [(29, 6), (43, 7), (58, 9), (71, 8), (94, 11)]
            total, divisor = scenarios[(variant - 1) % len(scenarios)]
            question = (
                f"A batch job receives {total} records and puts {divisor} records in each "
                f"complete batch. What does {total} % {divisor} return, and what does the "
                "remainder mean?"
            )
            answer_type = "explanation"
        elif concept_key == "stack":
            question = (
                f"Variant {variant}: A stack starts empty. You push A, then B, then C, "
                "pop once, and push D. What item is on top now, and why?"
            )
            answer_type = "explanation"
        elif spec.question_type == "code_prediction":
            question = (
                f"Write a small Python example using {spec.concept} and explain what it "
                "will do, including the key state change."
            )
            answer_type = "code"
        elif spec.question_type == "transfer":
            question = (
                f"Apply {spec.concept} to a new {subject} situation. Describe the situation, "
                "apply the concept, and explain your reasoning."
            )
            answer_type = "explanation"
        else:
            question = (
                f"Variant {variant}: Explain how {spec.concept} behaves in a new {subject} "
                "situation and give one concrete example."
            )
            answer_type = "explanation"

        return {
            "title": f"{spec.concept}: {spec.target_skill}",
            "question": question,
            "context": spec.context,
            "hints": [hint],
            "success_signal": (
                f"The learner demonstrates the defining rule of {spec.concept} "
                "and applies it correctly."
            ),
            "expected_answer_type": answer_type,
            "difficulty": spec.difficulty,
            "question_type": spec.question_type,
            "concept": spec.concept,
            "strategy": spec.strategy,
            "action": spec.action,
            "learning_guide": {
                "explanation": explanation,
                "worked_example": example,
                "hint": hint,
            },
            "generation_fallback": True,
        }

