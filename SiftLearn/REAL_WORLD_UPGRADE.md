# Sift real-world learning upgrade

This build keeps the adaptive backend intact while making the learner experience more like an adaptive tutor than a fixed course.

## Product flow

Observe -> Diagnose -> Help -> Recheck -> Adapt -> Repeat

## Learner experience

- Home is a decision surface: today's real learning, streak, tracks, next action, and learner-created topics.
- Learn is the classroom: teaching guidance appears before the dynamic task when available.
- Progress shows actual activity and concept evidence rather than vanity numbers.
- History exposes the question, learner answer, evaluation evidence, and mastery movement.
- Resources are targeted support and return the learner to Learn for recheck.
- Built-in tracks remain independent.
- Learners can create a personal topic such as `Stack`, `Python decorators`, or `derivatives` without waiting for the preset syllabus.
- Personal topics persist and use the same adaptive engine and dynamic task validation as built-in concepts.
- Daily time is actual recorded learning time; the Learn page no longer uses a countdown slider.

## Safety and quality

- Dynamic task novelty and structural validation remain enabled.
- User-created topics do not bypass assessment; they create a zero-prerequisite focus node and gather evidence through the same learning loop.
- Existing SQLite data is migrated additively when possible.
- `.env`, local databases, caches and bytecode should not be committed to a public repository.
