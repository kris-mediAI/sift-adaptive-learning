# Sift — Adaptive Learning

> **Sift doesn't give every learner the same path. It builds the next step from what they actually demonstrate.**

Sift is an AI-powered adaptive learning tutor built for students who want focused, personalized study rather than a fixed lesson that treats everyone the same.

## The problem

Most learning tools are good at delivering content, but they often follow a predetermined sequence. A learner can already understand a concept and still receive the same explanation, or struggle with a concept and simply be given another question.

Sift takes a different approach:

**Observe → Understand → Adapt → Practice → Reassess**

The learner's answers become evidence that shapes what happens next.

## What Sift does

### 1. Start with the learner

A lightweight onboarding flow captures the learner's context and purpose, such as coursework, exams, interviews, projects, or personal learning.

This context helps Sift choose an appropriate starting point. It is not treated as a permanent label: demonstrated performance becomes the stronger signal over time.

### 2. Create a focused session

Learners choose a subject and can select a syllabus topic or describe what they actually want to learn.

Sift validates the input before creating the session, so vague inputs such as `idk` don't accidentally become learning topics.

### 3. Teach and assess

A session can contain explanations, examples, questions, practice, and checks for understanding.

The system evaluates the learner's response and records evidence about what they demonstrated.

### 4. Adapt in real time

Sift can respond to evidence by:

- increasing or reducing difficulty
- explaining a concept differently
- returning to a prerequisite
- adding targeted practice
- moving forward when understanding is strong
- recommending a contextual resource when it can help

The important part is the loop: the next learning turn is informed by the previous one.

### 5. Respect available time

A selected time budget is treated as a **learning budget**, not just a countdown.

A short session is scoped to a focused learning outcome. Longer sessions allow more diagnosis, practice, reinforcement, and challenge. The plan can change based on learner evidence while remaining within the available time.

### 6. Build evidence over time

Progress is based on demonstrated learning rather than simply counting opened lessons.

Sift keeps session, mastery, history, and learning evidence so that future sessions can start from a more informed position.

## Adaptive loop

```text
Learner context
      ↓
Starting point
      ↓
Learning turn
      ↓
Learner response
      ↓
AI evaluation
      ↓
Evidence + diagnosis
      ↓
Adapt the next step
      ↓
New learning turn
      ↺
```

This is the core of Sift.

## Contextual resources

Resources are not intended to be a generic content dump.

When a learner needs additional support, Sift can surface context-specific help such as:

- a concise explanation
- a worked example
- a useful reference
- a relevant YouTube explanation

A resource should have a reason for appearing. If no useful resource is available, Sift should continue teaching rather than filling the interface with unrelated recommendations.

## Progress and history

Sift separates **current learning progress** from the chronological record of what happened.

Progress helps answer:

> **Am I improving, and where?**

History helps answer:

> **What did I do, what changed, and what did Sift notice?**

This makes the adaptive process visible without turning the product into a collection of vanity metrics.

## Initial subject coverage

The prototype focuses on practical, high-value subjects for students, including areas such as:

- Python
- Data Structures & Algorithms
- Machine Learning
- Mathematics
- Database / SQL
- Operating Systems
- Computer Networks

The architecture is designed around topic-level learning, so a learner can go much deeper than the initial subject list.

## Technology

Sift is built as a Python/Streamlit application with a modular architecture for:

- learner modeling
- adaptive orchestration
- assessment and evaluation
- session management
- mastery/progression
- time-budget planning
- contextual resources
- persistence
- UI components

Gemini can provide the semantic intelligence for content generation, evaluation, topic interpretation, and adaptive decisions. The application also contains deterministic safeguards and persistence logic so core product behavior does not depend on blindly trusting one model response.

## Why AI is core

Sift is not simply an AI chatbot placed inside a learning interface.

AI participates in the learning loop:

**interpret → assess → diagnose → adapt → generate → reassess**

The same topic can therefore produce different learning experiences for different learners—or for the same learner at different points in their learning journey.

## Running locally

### Requirements

- Python 3.10+
- A Gemini API key for live AI functionality

### Install

```bash
pip install -r requirements.txt
```

### Configure

Create a `.env` file locally:

```text
GEMINI_API_KEY=your_key_here
```

**Never commit `.env` or API keys to the repository.**

### Run

```bash
streamlit run app.py
```

## Testing

Run the automated tests with:

```bash
python -m pytest -q
```

The test suite covers core learning behavior such as sessions, evaluation, persistence, progression, resources, and adaptive flows.

## Project structure

```text
app.py
ai/
core/
database/
ui/
tests/
requirements.txt
README.md
```

## Hackathon demo

The strongest way to experience Sift is to watch the adaptive loop:

1. Create a session.
2. Start with a learning topic.
3. Answer a question imperfectly.
4. Watch Sift evaluate the response.
5. Observe the next learning step change based on the evidence.
6. Give a stronger response.
7. See Sift increase the challenge or move forward.
8. Check the resulting mastery evidence.

**The product is the adaptation—not just the generated content.**

## Privacy and submission hygiene

Do not include:

- API keys
- `.env` files
- personal credentials
- local databases containing private learner data
- virtual environments
- Python caches
- unrelated development files

Keep secrets in local environment configuration and use a clean submission repository.

---

## Built for the August AI Challenge

Sift is an educational AI/ML prototype focused on making learning responsive to the learner rather than forcing every learner through the same path.
