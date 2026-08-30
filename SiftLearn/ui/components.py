import html
import streamlit as st


def esc(value):
    return html.escape("" if value is None else str(value))


def page_header(eyebrow, title, subtitle=None):
    subtitle_html = f'<div class="page-subtitle">{esc(subtitle)}</div>' if subtitle else ""
    st.markdown(
        f'<div class="page-eyebrow">{esc(eyebrow)}</div>'
        f'<div class="page-title">{esc(title)}</div>{subtitle_html}',
        unsafe_allow_html=True,
    )


def metric_card(label, value, note=""):
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{esc(label)}</div>'
        f'<div class="metric-value">{esc(value)}</div><div class="metric-note">{esc(note)}</div></div>',
        unsafe_allow_html=True,
    )


def mastery_bar(name, mastery, attempts=None, correct=None):
    try:
        value = max(0.0, min(100.0, float(mastery)))
    except (TypeError, ValueError):
        value = 0.0
    meta = []
    if attempts is not None:
        meta.append(f"{int(attempts)} attempts")
    if correct is not None:
        meta.append(f"{int(correct)} correct")
    st.markdown(
        f'<div class="progress-row"><div class="progress-head"><div>'
        f'<div class="progress-name">{esc(name)}</div><div class="progress-meta">{esc(" · ".join(meta))}</div>'
        f'</div><div class="progress-value">{value:.0f}%</div></div>'
        f'<div class="progress-track"><div class="progress-fill" style="width:{value:.1f}%"></div></div></div>',
        unsafe_allow_html=True,
    )


def focus_card(concept, description, reason=None, strategy=None):
    strategy_html = (
        f'<span class="badge blue">{esc(str(strategy).replace("_", " ").title())}</span>'
        if strategy else ""
    )
    reason_html = (
        f'<div class="focus-reason"><strong>Why Sift chose this</strong><br>{esc(reason)}</div>'
        if reason else ""
    )
    st.markdown(
        f'<div class="focus-card"><div class="focus-kicker">YOUR NEXT STEP</div>'
        f'<div class="focus-title">{esc(concept)}</div><div class="focus-copy">{esc(description)}</div>'
        f'<div class="focus-badge-row">{strategy_html}</div>{reason_html}</div>',
        unsafe_allow_html=True,
    )


def task_card(task):
    task = task if isinstance(task, dict) else {}
    strategy = task.get("strategy") or task.get("intervention_type") or "adaptive"
    concept = task.get("concept") or "Current concept"
    title = task.get("title") or "Your learning task"
    question = task.get("question") or task.get("task") or ""
    context = task.get("context") or task.get("example") or ""
    guide = task.get("learning_guide") if isinstance(task.get("learning_guide"), dict) else {}
    explanation = str(guide.get("explanation") or "").strip()
    worked_example = str(guide.get("worked_example") or "").strip()

    guide_html = ""
    if explanation or worked_example:
        worked = f'<div class="worked-example"><b>Worked example</b><br>{esc(worked_example)}</div>' if worked_example else ""
        guide_html = (
            '<div class="learn-first"><div class="learn-first-kicker">LEARN FIRST</div>'
            '<div class="learn-first-title">Build the idea before you prove it</div>'
            f'<div class="learn-first-copy">{esc(explanation)}</div>{worked}</div>'
        )
    context_html = f'<div class="task-context">{esc(context)}</div>' if context else ""
    st.markdown(
        f'<div class="task-card">{guide_html}<div class="task-head"><div>'
        f'<div class="task-kicker">{esc(str(strategy).replace("_", " "))} · {esc(concept)}</div>'
        f'<div class="task-title">{esc(title)}</div></div>'
        f'<span class="badge blue">{esc(concept)}</span></div>'
        f'<div class="task-question">{esc(question)}</div>{context_html}</div>',
        unsafe_allow_html=True,
    )


def empty_card(title, body):
    st.markdown(
        f'<div class="empty-card"><div class="empty-title">{esc(title)}</div>'
        f'<div class="empty-copy">{esc(body)}</div></div>',
        unsafe_allow_html=True,
    )


def resource_card(resource, featured=False):
    if isinstance(resource, str):
        resource = {"title": resource, "description": "External resource", "url": ""}
    if not isinstance(resource, dict):
        return
    title = resource.get("title") or resource.get("name") or "Learning resource"
    description = resource.get("description") or resource.get("snippet") or ""
    reason = resource.get("reason") or "Selected because it matches the concept you are working on."
    score = resource.get("quality_score")
    url = resource.get("url") or resource.get("link") or resource.get("video_url")
    channel = resource.get("channel") or ("YouTube" if resource.get("type") == "youtube" or resource.get("video_id") else resource.get("type")) or resource.get("source") or "Learning resource"
    try:
        score_html = f'<span class="badge green">Sift quality {float(score):.0f}</span>' if score is not None else ""
    except (TypeError, ValueError):
        score_html = ""
    featured_html = '<span class="badge blue">Recommended now</span>' if featured else ""
    action = (
        f'<a class="resource-action" href="{esc(url)}" target="_blank" rel="noopener noreferrer">Open resource ↗</a>'
        if url else '<span class="history-meta">Internal help · no external link needed</span>'
    )
    thumbnail = resource.get("thumbnail") or ""
    # Fallback for YouTube responses that omit thumbnail metadata.
    if not thumbnail and resource.get("video_id"):
        thumbnail = "https://i.ytimg.com/vi/" + str(resource.get("video_id")) + "/hqdefault.jpg"
    thumb_html = (
        f'<img class="resource-thumb" src="{esc(thumbnail)}" alt="" loading="lazy">'
        if thumbnail else '<div class="resource-thumb resource-thumb-placeholder">▶</div>'
    )
    st.markdown(
        f'<div class="resource-card card"><div class="resource-card-layout">{thumb_html}<div class="resource-card-main"><div class="resource-card-head"><div>'
        f'<div class="history-title">{esc(title)}</div><div class="history-meta">{esc(channel)}</div></div>'
        f'<div class="resource-meta-row">{featured_html}{score_html}</div></div>'
        f'<div class="resource-description">{esc(description)}</div>'
        f'<div class="resource-reason"><strong>Why Sift recommends this</strong><br>{esc(reason)}</div>'
        f'<div style="margin-top:13px">{action}</div></div></div></div>',
        unsafe_allow_html=True,
    )


def track_visual(subject):
    """Small deterministic visual used by the optional Home/track map."""
    icons = {
        "Python": "Py",
        "Data Structures & Algorithms": "DS",
        "SQL / DBMS": "DB",
        "Operating Systems": "OS",
        "Computer Networks": "NW",
        "Machine Learning": "ML",
        "Mathematics": "∑",
    }
    return f'<span class="track-icon">{esc(icons.get(subject, "✦"))}</span>'


def sidebar_brand():
    st.markdown(
        '<div class="sift-brand"><span class="sift-logo">S</span><div>'
        '<div class="sift-name">Sift</div><div class="sift-tagline">ADAPTIVE LEARNING</div></div></div>',
        unsafe_allow_html=True,
    )


def sidebar_profile(name, meta="Learner"):
    initial = esc((str(name).strip()[:1] or "L").upper())
    st.markdown(
        f'<div class="sidebar-profile"><span class="sidebar-avatar">{initial}</span>'
        f'<div class="sidebar-name">{esc(name or "Learner")}</div><div class="sidebar-meta">{esc(meta)}</div>'
        '<div style="clear:both"></div></div>',
        unsafe_allow_html=True,
    )
