# Sift UI/UX Patch

This patch updates the user-facing interaction layer without changing the adaptive-learning engine.

## Files to replace
- app.py
- ui/components.py
- ui/home.py
- ui/sidebar.py
- ui/styles.py

## UX changes
- Consistent primary/secondary/disabled button behavior.
- Better focus/hover/pressed states and touch targets.
- Active track is visibly disabled as `Current track`; other tracks use clearer `Continue this track` / `Add this track` actions.
- Resource page is now a targeted intervention surface rather than a generic library.
- Resource recommendations explain why Sift selected the resource.
- Quick tip is positioned as the first in-Sift intervention.
- External resource is limited to one featured vetted item by default.
- Clear return path from Resources to Learn.
- Mobile resource actions become full-width and task headers stack cleanly.
- Resource usage explicitly points the learner back to Learn for recheck.

## Validation
The five changed Python files pass `py_compile` syntax validation.

The full pytest suite could not be executed in this isolated runtime because the uploaded project does not include the project's installed Google GenAI environment. This is an environment limitation, not a syntax failure in the patch.
