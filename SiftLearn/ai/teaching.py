import json

from ai.gemini import generate


VALID_STRATEGIES = {
    "worked_example",
    "visual_explanation",
    "analogy",
    "socratic",
    "practice_first",
}


def generate_intervention(
    subject,
    concept,
    strategy,
    learner
):
    """
    Generate a personalized learning intervention.
    """

    if strategy not in VALID_STRATEGIES:
        strategy = "worked_example"

    strategy_instructions = {
        "worked_example": """
Teach the concept through a concrete worked example.
Show the reasoning step by step.
Then give the learner one similar problem.
""",

        "visual_explanation": """
Use a simple visual or ASCII-style mental model.
Focus on relationships, movement, structure, or state changes.
Then give the learner a small task based on the visualization.
""",

        "analogy": """
Explain the concept using a familiar real-world analogy.
Clearly connect each part of the analogy back to the actual concept.
Then give the learner a short application task.
""",

        "socratic": """
Guide the learner using a sequence of short questions.
Do not immediately reveal the answer.
Use the learner's reasoning to guide the explanation.
""",

        "practice_first": """
Start with a small problem.
Let the learner reason about it before explaining the concept.
Then provide a second targeted problem.
"""
    }

    prompt = f"""
You are Sift Learn's personalized teaching engine.

Student level context:
{learner.current_level}

Subject:
{subject}

Available time:
{learner.available_minutes} minutes

Concept:
{concept}

Teaching strategy:
{strategy}

Strategy instructions:
{strategy_instructions[strategy]}

Create a short, focused learning intervention.

Rules:
- Teach only the target concept.
- Match the student's level.
- Avoid unnecessary jargon.
- Make the student actively think.
- Do not assume mastery.
- End with exactly ONE task.
- Do not reveal the answer to the task.

Return ONLY valid JSON:

{{
    "title": "short title",
    "strategy": "{strategy}",
    "concept": "{concept}",
    "explanation": "teaching content",
    "task": "one task for the student",
    "success_signal": "what the answer should demonstrate"
}}
"""

    raw = generate(prompt).strip()

    if raw.startswith("```"):
        raw = raw.replace("```json", "", 1)
        raw = raw.replace("```", "", 1).strip()

    try:
        result = json.loads(raw)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Gemini returned invalid intervention JSON: {raw}"
        ) from error

    required_fields = {
        "title",
        "strategy",
        "concept",
        "explanation",
        "task",
        "success_signal"
    }

    missing = required_fields - result.keys()

    if missing:
        raise ValueError(
            "Intervention is missing fields: "
            + ", ".join(missing)
        )

    return result