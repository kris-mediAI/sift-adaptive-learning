# SiftLearn Technical Upgrade

This patch implements the first coherent product/architecture pass for the Sift learning loop.

## What changed

- Evidence-backed concept progression with five learner-facing stages.
- Full syllabus nodes are available to the progression/UI without creating fake learner evidence.
- Completed concepts require sufficient mastery/confidence/evidence and a completed challenge before normal forward progression.
- Retention review can bring completed concepts back when the retention model says review is due.
- User-directed focus concept is persisted per learning track and ends when the focused concept is completed.
- Dynamic learning turns record question, answer, evaluation evidence and active-turn duration.
- Learning streaks now accumulate daily minutes, turns and concepts while counting a day only once.
- Existing learner time accuracy is updated from actual turn duration.
- Assessment persistence now includes the question/answer; learning events also retain evaluation metadata.
- Learn UI no longer uses a permanent time-budget slider; it shows live elapsed learning time.
- Completed results are shown before the next recommendation/task so the learning turn is not interrupted.
- Home shows today's actual activity, track completion, concept journey, weekly activity and an optional focused concept path.
- Progress shows syllabus completion, observed mastery, daily activity, streak and recent mastery movement.
- History exposes the learner's question, answer and persisted evaluation evidence.
- Resources are contextualized using the most recent assessed concept/misconception rather than blindly using the next recommendation.
- Teaching/content prompts no longer over-emphasize the learner's stated goal.

## Safety / compatibility

- Existing dynamic-task persistence and novelty validation are preserved.
- Existing assessment validation remains the gate before knowledge updates.
- Existing strategy evidence and retention engine remain in place.
- Database changes are additive migrations; existing SQLite data is not replaced.
- No Gemini or YouTube calls are made by the offline verification script.

## Verification

`python verify_technical_upgrade.py` passes offline syntax and product-flow checks.

The legacy closed-loop scripts used during development also passed with the project's test harness and a local Gemini stub. Live YouTube/Gemini calls were not required for these checks.
