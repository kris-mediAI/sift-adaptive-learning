import html
import time
from datetime import datetime, timezone

import streamlit as st

from core.orchestrator import SiftOrchestrator
from ui import inject_css
from ui.components import page_header, metric_card, task_card, resource_card
from ui.sidebar import render_sidebar, get_current_view
from ai.topic_validator import validate_learning_input

st.set_page_config(page_title="Sift — Adaptive Learning", page_icon="S", layout="wide", initial_sidebar_state="expanded")
inject_css()

@st.cache_resource
def get_orchestrator():
    return SiftOrchestrator()

sift = get_orchestrator()


def esc(v):
    return html.escape("" if v is None else str(v))


def init_state():
    defaults = {
        "current_view": "onboarding",
        "profile_name": "",
        "profile_goal": "",
        "learning_purpose": "Coursework",
        "session_registry": [],
        "active_learning_session": None,
        "active_learner_id": None,
        "last_result": None,
        "dynamic_answer_nonce": 0,
        "help_level": 0,
        "new_subject": None,
        "new_topic": "",
        "new_goal": "Understand",
        "new_level": "Let Sift assess me",
        "new_style": "Adaptive",
        "new_time": 30,
        "session_started_at": None,
        "resource_cache": {},
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


init_state()
subjects = list(sift.get_supported_subjects())
# Keep the launch catalog focused for the intended BTech/student audience.
preferred = ["Python", "Data Structures & Algorithms", "SQL / DBMS", "Operating Systems", "Computer Networks", "Machine Learning"]
subjects = [s for s in preferred if s in subjects]


def profile_ready():
    return bool(st.session_state.profile_name.strip())


def current_record():
    sid = st.session_state.get("active_learning_session")
    for item in st.session_state.get("session_registry", []):
        if item.get("id") == sid:
            return item
    return None


def current_learner():
    lid = st.session_state.get("active_learner_id")
    if not lid:
        rec = current_record()
        lid = rec.get("learner_id") if rec else None
    if not lid:
        return None
    try:
        return sift.repository.load_learner(lid)
    except Exception:
        return None


def current_backend_session():
    learner = current_learner()
    if not learner:
        return None
    return sift.get_session(st.session_state.active_learner_id)


def _friendly_datetime(value):
    """Turn stored ISO timestamps into a learner-friendly local date/time."""
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt.astimezone()
        return dt.strftime("%b %d, %Y · %I:%M %p").replace(" 0", " ")
    except (TypeError, ValueError):
        return str(value)


def refresh_session_registry():
    """Rebuild the session list from SQLite so History/Progress stay current."""
    name = st.session_state.get("profile_name", "").strip()
    if not name:
        return []
    records = []
    try:
        learners = sift.repository.list_learners_by_name(name)
        for learner in learners:
            learner_id = getattr(learner, "_db_id", None)
            if not learner_id:
                continue
            for row in sift.list_learning_sessions(learner_id):
                records.append({
                    "id": row.get("id"),
                    "learner_id": learner_id,
                    "subject": row.get("subject") or learner.subject,
                    "topic": row.get("topic") or getattr(learner, "focus_concept", "") or "Learning session",
                    "session_goal": row.get("session_goal") or learner.goal or "Understand",
                    "time_cap": row.get("time_cap") or row.get("available_minutes") or learner.available_minutes or 30,
                    "teaching_style": row.get("teaching_style") or "Adaptive",
                    "starting_point": row.get("starting_point") or "Let Sift assess me",
                    "created_at": row.get("created_at") or "",
                    "updated_at": row.get("updated_at") or row.get("created_at") or "",
                    "status": row.get("status") or "active",
                })
    except Exception:
        records = []

    records.sort(key=lambda r: (r.get("updated_at") or r.get("created_at") or "", int(r.get("id") or 0)), reverse=True)
    st.session_state.session_registry = records
    return records


def sessions():
    return refresh_session_registry()


def switch_session(item):
    st.session_state.active_learning_session = item["id"]
    st.session_state.active_learner_id = item["learner_id"]
    st.session_state.last_result = None
    st.session_state.help_level = 0
    st.session_state.dynamic_answer_nonce += 1
    st.session_state.session_started_at = time.time()
    try:
        sift.set_focus_concept(item["learner_id"], item.get("topic"))
    except Exception:
        pass


def mastery_for(learner_id, topic=None):
    try:
        session = sift.get_session(learner_id)
        if topic and topic in session.concepts:
            return float(getattr(session.concepts[topic], "mastery", 0) or 0)
        vals = [float(getattr(c, "mastery", 0) or 0) for c in session.concepts.values()]
        return sum(vals) / len(vals) if vals else 0.0
    except Exception:
        return 0.0


def create_profile_learner(subject):
    learner_id, _ = sift.get_or_create_learner(
        name=st.session_state.profile_name.strip(),
        goal=st.session_state.profile_goal.strip(),
        subject=subject,
        available_minutes=30,
        current_level="Beginner",
        target_days=30,
        learning_purpose=st.session_state.get("learning_purpose", "Coursework"),
    )
    return learner_id


def create_new_session():
    subject = st.session_state.new_subject
    topic = st.session_state.new_topic.strip()
    if not subject:
        st.error("Choose a subject first.")
        return False
    if not topic:
        st.warning("Tell Sift what you want to learn, or choose a syllabus topic above.")
        return False

    # Validate before creating anything in the database. This prevents inputs
    # such as "idk" from becoming permanent learning topics.
    validation = validate_learning_input(
        subject,
        topic,
        sift.get_subject_concepts(subject),
    )
    if not validation.get("accepted"):
        if validation.get("needs_clarification"):
            st.warning("That is not enough to start a session. Pick a topic above or tell Sift what you want to learn — for example, ‘recursion for tree problems’.")
        else:
            st.warning(validation.get("reason") or "That doesn't look like a learning topic yet.")
        return False

    topic = validation.get("normalized_topic") or topic
    st.session_state.new_topic = topic
    learner_id = create_profile_learner(subject)
    sid = sift.create_learning_session(
        learner_id=learner_id,
        subject=subject,
        topic=topic,
        session_goal=st.session_state.new_goal,
        available_minutes=st.session_state.new_time,
        teaching_style=st.session_state.new_style,
        starting_point=st.session_state.new_level,
    )
    record = {
        "id": sid,
        "learner_id": learner_id,
        "subject": subject,
        "topic": topic,
        "session_goal": st.session_state.new_goal,
        "time_cap": st.session_state.new_time,
        "teaching_style": st.session_state.new_style,
        "starting_point": st.session_state.new_level,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    st.session_state.session_registry = [r for r in st.session_state.session_registry if r.get("id") != sid] + [record]
    switch_session(record)
    st.session_state.current_view = "session"
    st.session_state.last_result = None
    st.rerun()
    return True


def active_task(session):
    active = getattr(session, "active_intervention", None)
    if not isinstance(active, dict):
        return None
    candidates = [active.get("intervention"), active.get("task"), active]
    task = next((x for x in candidates if isinstance(x, dict)), None)
    if not task:
        return None
    task = dict(task)
    for k in ("strategy", "concept", "title", "question", "action", "target_concept", "difficulty", "question_type"):
        if k not in task and k in active:
            task[k] = active[k]
    q = task.get("question") or task.get("task")
    if not q:
        return None
    task["question"] = q
    return task


def recommendation_for(session):
    if not session:
        return None
    try:
        return session.engine.recommend(
            learner=session.learner,
            concepts=list(session.concepts.values()),
            focus_concept=getattr(session, "focus_concept", None),
        )
    except Exception:
        return None


def start_or_generate(session, rec):
    lid = st.session_state.active_learner_id
    if not lid:
        return
    try:
        if rec:
            with st.spinner("Sift is preparing your next adaptive step…"):
                sift.generate_dynamic_task(learner_id=lid, recommendation=rec)
            st.session_state.last_result = None
            st.session_state.help_level = 0
            st.session_state.dynamic_answer_nonce += 1
            st.rerun()
    except Exception as exc:
        st.error("Sift could not prepare the next adaptive step.")
        with st.expander("Technical details"):
            st.code(str(exc))


def render_onboarding():
    st.markdown('<div class="onboard-shell"><div class="onboard-orbit orbit-a"></div><div class="onboard-orbit orbit-b"></div>', unsafe_allow_html=True)
    st.markdown('<div class="onboard-brand"><span class="sift-logo">S</span><div><b>Sift</b><small>Adaptive Learning</small></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="onboard-copy"><div class="page-eyebrow">Adaptive learning</div><h1>Learn smarter.<br><span>Sift adapts to you.</span></h1><p>Give Sift a little context. It uses your goal, purpose, and later answers to choose better explanations, questions, difficulty, and next steps.</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="onboard-signal-row"><div><span>✦</span><b>Personalized start</b><small>Your goal shapes the first step.</small></div><div><span>↗</span><b>Evidence-led</b><small>Your answers reshape what comes next.</small></div><div><span>◌</span><b>No fixed path</b><small>Sift adjusts as you learn.</small></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="onboard-proof"><span>✦</span><b>One starting point.</b><span>Then Sift learns from your evidence.</span></div>', unsafe_allow_html=True)
    with st.form("onboarding_form"):
        name = st.text_input("What should we call you?", value=st.session_state.profile_name, placeholder="Your name")
        purpose = st.radio("What are you here to achieve?", ["Coursework", "Exams", "Interviews / placements", "Projects / building", "Personal learning"], index=["Coursework", "Exams", "Interviews / placements", "Projects / building", "Personal learning"].index(st.session_state.learning_purpose), horizontal=True)
        goal = st.text_input("What are you hoping to achieve?", value=st.session_state.profile_goal, placeholder="e.g. Become confident with DSA for placements")
        submitted = st.form_submit_button("Start learning with Sift →", type="primary", use_container_width=True)
    if submitted:
        if not name.strip():
            st.error("Enter your name to continue.")
        else:
            st.session_state.profile_name = name.strip()
            st.session_state.profile_goal = goal.strip()
            st.session_state.learning_purpose = purpose
            st.session_state.current_view = "sessions"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def render_sessions():
    page_header("Sessions", f"Good evening, {esc(st.session_state.profile_name)} 👋", "Pick up where you left off, or start a focused learning session.")
    records = sessions()
    if records:
        active = current_record()
        if not active:
            active = records[0]
            switch_session(active)
        mastery = mastery_for(active["learner_id"], active.get("topic"))
        st.markdown('<div class="continue-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="session-kicker">CONTINUE</div><div class="session-title">{esc(active.get("subject"))} · {esc(active.get("topic"))}</div><div class="session-meta">{esc(active.get("session_goal"))} · {esc(active.get("teaching_style","Adaptive"))} · {int(active.get("time_cap",30))} min</div>', unsafe_allow_html=True)
        st.progress(min(max(mastery/100, 0), 1))
        st.markdown(f'<div class="session-adaptive-note">✦ Sift will use your latest evidence to choose the next useful step. <span>{mastery:.0f}% topic mastery</span></div>', unsafe_allow_html=True)
        if st.button("Continue session →", key="continue_session", type="primary"):
            switch_session(active); st.session_state.current_view="session"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Recent sessions</div>', unsafe_allow_html=True)
        for item in records:
            mastery = mastery_for(item["learner_id"], item.get("topic"))
            active_cls = " session-row-active" if item.get("id") == active.get("id") else ""
            c1, c2 = st.columns([10, 1], vertical_alignment="center")
            with c1:
                st.markdown(f'<div class="session-row{active_cls}"><div><b>{esc(item.get("subject"))}</b><span> · {esc(item.get("topic"))}</span><small>{esc(item.get("session_goal"))} · {int(item.get("time_cap",30))} min</small></div><strong>{mastery:.0f}%</strong></div>', unsafe_allow_html=True)
            with c2:
                if st.button("→", key=f"open_{item['id']}", help="Continue this session"):
                    switch_session(item); st.session_state.current_view="session"; st.rerun()
    else:
        st.markdown('<div class="empty-session"><div class="empty-icon">✦</div><h2>Start your first learning session</h2><p>Choose a subject, name the topic you need, and let Sift adapt the session to your level and available time.</p></div>', unsafe_allow_html=True)
    if st.button("＋  New session", key="new_session_main", type="primary", use_container_width=False):
        st.session_state.current_view="new_session"; st.rerun()


def render_new_session():
    page_header("New session", "What do you want to learn?", "Choose a learning area, then make the topic as specific as you need. Sift handles the adaptation.")
    if st.session_state.new_subject not in subjects:
        st.session_state.new_subject = subjects[0] if subjects else None
    cols = st.columns(3)
    for i, subject in enumerate(subjects):
        with cols[i % 3]:
            selected = subject == st.session_state.new_subject
            if st.button(("✓  " if selected else "") + subject, key=f"subject_{i}", use_container_width=True, type="primary" if selected else "secondary"):
                st.session_state.new_subject = subject; st.rerun()
    subject = st.session_state.new_subject
    if subject:
        concepts = sift.get_subject_concepts(subject)
        st.markdown(f'<div class="syllabus-card"><div class="session-kicker">{esc(subject.upper())} SYLLABUS</div><div class="syllabus-caption">Pick a starting topic or type your own below. Selecting a topic creates the session focus; Sift can still adapt beyond the syllabus.</div>', unsafe_allow_html=True)
        topic_cols = st.columns(4)
        for i, concept_name in enumerate(concepts[:12]):
            with topic_cols[i % 4]:
                selected_topic = concept_name == st.session_state.new_topic.strip()
                label = ("✓  " if selected_topic else "") + concept_name
                if st.button(label, key=f"syllabus_topic_{i}", use_container_width=True,
                             type="primary" if selected_topic else "secondary"):
                    st.session_state.new_topic = concept_name
                    st.session_state.topic_input = concept_name
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    # topic_input is the single UI source of truth; mirror it only after the widget exists.
    if "topic_input" not in st.session_state:
        st.session_state.topic_input = st.session_state.new_topic
    topic = st.text_input("What do you want to learn?", placeholder="e.g. Recursion for tree problems", key="topic_input")
    st.session_state.new_topic = topic.strip()
    c1, c2 = st.columns(2)
    with c1:
        goal = st.selectbox("Goal", ["Understand", "Practice", "Exam preparation", "Interview preparation", "Project"], index=["Understand", "Practice", "Exam preparation", "Interview preparation", "Project"].index(st.session_state.new_goal))
        level = st.selectbox("Starting point", ["Let Sift assess me", "I'm new to this", "I know the basics", "I'm comfortable"], index=["Let Sift assess me", "I'm new to this", "I know the basics", "I'm comfortable"].index(st.session_state.new_level))
    with c2:
        style = st.selectbox("Teaching", ["Adaptive", "Guided", "Balanced", "Challenge"], index=["Adaptive", "Guided", "Balanced", "Challenge"].index(st.session_state.new_style))
        cap = st.selectbox("Time available", [10,20,30,45,60], index=[10,20,30,45,60].index(st.session_state.new_time), format_func=lambda x:f"{x} min")
    st.session_state.new_goal, st.session_state.new_level, st.session_state.new_style, st.session_state.new_time = goal, level, style, cap
    st.markdown('<div class="adaptive-callout"><b>✦ Sift adapts this session</b><span>Your answers, difficulty, explanations and next step will change based on your evidence. The time cap is a budget, not a rigid lesson timer.</span></div>', unsafe_allow_html=True)
    if st.button("Create session →", key="create_session", type="primary", use_container_width=True):
        try:
            with st.spinner("Building your adaptive session…"):
                create_new_session()
        except Exception as exc:
            st.error("Sift could not create the session.")
            with st.expander("Technical details"): st.code(str(exc))


def render_session():
    rec = current_record(); session = current_backend_session()
    if not rec or not session:
        st.session_state.current_view="sessions"; st.rerun()
    mastery = mastery_for(rec["learner_id"], rec.get("topic"))
    st.markdown(f'<div class="session-top"><div><div class="breadcrumbs">Sessions / {esc(rec["subject"])}</div><h1>{esc(rec["topic"])}</h1><p>{esc(rec.get("session_goal"))} · {esc(rec.get("teaching_style","Adaptive"))} · {int(rec.get("time_cap",30))} min</p></div><div class="session-mastery"><b>{mastery:.0f}%</b><span>topic mastery</span></div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="mastery-line"><span>Starting point</span><span>Current evidence</span></div><div class="adaptive-track"><i style="width:{min(max(mastery,3),100):.1f}%"></i></div>', unsafe_allow_html=True)
    st.markdown('<div class="adaptive-banner"><b>✦ SIFT IS ADAPTING</b><span>Your responses shape the next explanation, difficulty and problem. Nothing here is a fixed lesson path.</span></div>', unsafe_allow_html=True)
    task = active_task(session)
    if task:
        task_card(task)
        answer = st.text_area("Your answer", placeholder="Write your reasoning here.", key=f"answer_{st.session_state.dynamic_answer_nonce}")
        if st.button("Check answer →", type="primary", use_container_width=True):
            if not answer.strip(): st.warning("Write an answer before checking it.")
            else:
                try:
                    with st.spinner("Sift is evaluating your reasoning…"):
                        # Dynamic tasks must go through the completion path so
                        # the generated task is evaluated, persisted, marked
                        # complete, and replaced only after evidence is recorded.
                        if isinstance(getattr(session, "active_intervention", None), dict) and getattr(session, "active_intervention", {}).get("dynamic"):
                            result = sift.complete_dynamic_task(
                                learner_id=rec["learner_id"],
                                question=task["question"],
                                answer=answer.strip(),
                            )
                        else:
                            result = sift.assess(rec["learner_id"], task["question"], answer.strip())
                    st.session_state.last_result = result
                    st.session_state.help_level = 0
                    st.rerun()
                except Exception as exc:
                    st.error("Sift could not evaluate this turn.")
                    with st.expander("Technical details"): st.code(str(exc))
    else:
        result = st.session_state.get("last_result")
        if result:
            assessment = result.get("assessment", {}) or {}; concept = result.get("concept", {}) or {}
            score = assessment.get("score"); gain = result.get("learning_gain"); new_mastery = concept.get("mastery")
            st.markdown('<div class="result-panel"><div class="result-kicker">✦ SIFT UPDATED YOUR PATH</div><h2>Here’s what changed</h2><p>' + esc(assessment.get("explanation") or assessment.get("feedback") or "Your evidence has been added to the session.") + '</p></div>', unsafe_allow_html=True)
            a,b,c=st.columns(3)
            with a: metric_card("Understanding", f"{float(score):.0f}%" if score is not None else "—", "Latest turn")
            with b: metric_card("Mastery", f"{float(new_mastery):.0f}%" if new_mastery is not None else "—", rec["topic"])
            with c: metric_card("Learning gain", f"{float(gain):+.1f}" if gain is not None else "—", "This turn")
            nxt = result.get("next_recommendation") or result.get("recommendation") or recommendation_for(session)
            if nxt:
                st.markdown('<div class="next-focus"><div class="session-kicker">NEXT BEST STEP</div><h3>'+esc(nxt.get("concept") or nxt.get("target_concept") or "Continue")+'</h3><p>'+esc(nxt.get("reason") or nxt.get("diagnosis") or "Chosen from your latest evidence.")+'</p></div>', unsafe_allow_html=True)
                if st.button("Continue with the next adaptive step →", type="primary", use_container_width=True):
                    start_or_generate(session,nxt)
        else:
            recm = recommendation_for(session)
            focus = rec.get("topic")
            st.markdown(f'<div class="start-session-panel"><div class="session-kicker">READY</div><h2>Sift will start with {esc(focus)}.</h2><p>We’ll use a short check to understand what you already know, then adjust the session around the evidence.</p><div class="session-plan-pills"><span>Adaptive</span><span>{int(rec.get("time_cap",30))} min budget</span><span>{esc(rec.get("session_goal"))}</span></div></div>', unsafe_allow_html=True)
            if st.button("Start adaptive session →", type="primary", use_container_width=True):
                if recm: start_or_generate(session,recm)
                else: st.warning("Sift needs a little more information before it can generate the first step.")
    st.markdown('<div class="session-footer-note">Session state is saved as you learn. Leaving now does not reset your progress.</div>', unsafe_allow_html=True)


def render_progress():
    page_header("Progress", "Evidence of improvement", "Sift tracks what you demonstrate, not just what you open.")
    recs = sessions()
    all_records = []
    total_minutes = 0.0
    for r in recs:
        try:
            learner = sift.repository.load_learner(r["learner_id"])
            records = getattr(learner, "learning_records", []) or []
            for x in records:
                all_records.append((r, x))
            streak = getattr(learner, "activity_streak", {}) or {}
            total_minutes += float((streak.get("daily_minutes", {}) or {}).get(datetime.now().astimezone().date().isoformat(), 0) or 0)
        except Exception:
            continue

    all_records.sort(key=lambda pair: str(getattr(pair[1], "created_at", "") or ""))
    a, b, c = st.columns(3)
    with a: metric_card("Sessions", str(len(recs)), "Learning journeys created")
    with b: metric_card("Learning turns", str(len(all_records)), "Completed evidence")
    with c: metric_card("Today", f"{total_minutes:.0f} min", "Active learning time")

    st.markdown('<div class="progress-grid">', unsafe_allow_html=True)
    st.markdown('<div class="chart-panel"><div class="session-kicker">MASTERY TREND</div><h3>Your mastery across completed learning turns</h3><p class="chart-caption">Each point is evidence Sift recorded after a completed turn.</p>', unsafe_allow_html=True)
    vals = []
    for _, x in all_records[-12:]:
        post = getattr(x, "post_mastery", None)
        if post is not None:
            vals.append(max(0.0, min(100.0, float(post))))
    if vals:
        st.markdown(f'<div class="trend-values">{" · ".join(f"{v:.0f}%" for v in vals)}</div><div class="mini-chart">'+''.join(f'<i title="{v:.0f}% mastery" style="height:{max(6,min(100,v))}%"></i>' for v in vals)+'</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="current-mastery">Current mastery <b>{vals[-1]:.0f}%</b><span> · latest recorded evidence</span></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-chart">Complete a learning turn and Sift will start plotting your demonstrated mastery.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="chart-panel"><div class="session-kicker">SESSION MASTERY</div><h3>Where you stand now</h3>', unsafe_allow_html=True)
    for r in recs[:8]:
        m = mastery_for(r["learner_id"], r.get("topic"))
        st.markdown(f'<div class="progress-row"><span><b>{esc(r["subject"])}</b> · {esc(r["topic"])}</span><strong>{m:.0f}%</strong></div><div class="progress-track"><i style="width:{m:.1f}%"></i></div>', unsafe_allow_html=True)
    if not recs:
        st.markdown('<div class="empty-chart">Your session progress will appear here.</div>', unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)


def _eval(record):
    value=getattr(record,"evaluation",{}) or {}
    return value if isinstance(value,dict) else {}

def render_history():
    page_header("History", "Your learning journey", "See what you demonstrated, what Sift noticed, and why it changed the next step.")
    rows = []
    for r in sessions():
        try:
            learner = sift.repository.load_learner(r["learner_id"])
            for x in (getattr(learner, "learning_records", []) or []):
                concept = getattr(x, "concept", None) or r.get("topic") or "Learning turn"
                # Keep the history attached to the session/topic it actually belongs to.
                if r.get("topic") and concept.casefold() != str(r.get("topic")).casefold():
                    continue
                rows.append((r, x))
        except Exception:
            continue

    # If a legacy learner record predates the study-session table, still show it.
    if not rows:
        for r in sessions():
            try:
                learner = sift.repository.load_learner(r["learner_id"])
                for x in (getattr(learner, "learning_records", []) or []):
                    rows.append((r, x))
            except Exception:
                continue

    rows.sort(key=lambda pair: str(getattr(pair[1], "created_at", "") or ""), reverse=True)
    if not rows:
        st.markdown('<div class="empty-session"><div class="empty-icon">◷</div><h2>Your learning journey starts here.</h2><p>Complete a learning turn and Sift will keep a transparent record of what you demonstrated, what needed work, and why it chose the next step.</p></div>', unsafe_allow_html=True)
        return

    for r, x in rows[:50]:
        ev = _eval(x)
        concept = getattr(x, "concept", None) or r.get("topic") or "Learning turn"
        gain = getattr(x, "learning_gain", None); pre = getattr(x, "pre_mastery", None); post = getattr(x, "post_mastery", None)
        created = _friendly_datetime(getattr(x, "created_at", ""))
        duration = int(getattr(x, "duration_seconds", 0) or 0)
        if duration >= 60:
            dur = f" · {duration // 60} min"
        elif duration:
            dur = f" · {duration}s"
        else:
            dur = ""
        intervention = str(getattr(x, "intervention_type", "learning") or "learning").replace("_", " ").title()
        feedback = ev.get("explanation") or ev.get("feedback") or ev.get("summary") or "Sift recorded your evidence and updated your learner model."
        mistake = ev.get("mistake_type") or ""; misconception = ev.get("misconception") or ""
        reason = ev.get("next_reason") or ev.get("recommendation_reason") or ev.get("reason") or "Sift used this evidence to choose the next useful learning step."
        try: gain_text = f"{float(gain):+.1f}" if gain is not None else "—"
        except (TypeError, ValueError): gain_text = "—"
        try: mastery_text = f"{float(post):.0f}%" if post is not None else "—"
        except (TypeError, ValueError): mastery_text = "—"
        st.markdown(f'<div class="history-card"><div class="history-card-top"><div><div class="session-kicker">{esc(intervention)} · {esc(r.get("subject"))}</div><div class="history-title">{esc(concept)}</div><div class="history-meta">{esc(created)}{dur}</div></div><div class="history-result"><span>Mastery</span><strong>{mastery_text}</strong><em>{esc(gain_text)} gain</em></div></div><div class="history-reason">{esc(feedback)}</div></div>', unsafe_allow_html=True)
        with st.expander("See what Sift noticed", expanded=False):
            if getattr(x, "question", None): st.markdown(f"**Question**\n\n{x.question}")
            if getattr(x, "answer", None): st.markdown(f"**Your answer**\n\n{x.answer}")
            if ev.get("understood"): st.markdown(f"**What you demonstrated**\n\n{ev['understood']}")
            if ev.get("missing"): st.markdown(f"**What still needs work**\n\n{ev['missing']}")
            if mistake and str(mistake).lower() != "none": st.markdown(f"**Learning signal** · {mistake}")
            if misconception: st.markdown(f"**Misconception to address**\n\n{misconception}")
            st.markdown(f"**Why Sift chose the next step**\n\n{reason}")
            if pre is not None and post is not None:
                st.markdown(f"**Mastery change** · {float(pre):.0f}% → {float(post):.0f}% ({gain_text})")


def render_resources():
    page_header("Resources", "Useful when you need them", "Sift brings help into the session context — the right explanation, situation, or video at the right time.")
    r = current_record(); session = current_backend_session()
    if not r or not session:
        st.markdown('<div class="empty-session"><div class="empty-icon">▤</div><h2>Start a session first.</h2><p>Resources are contextual to what you are learning, not a generic library.</p></div>', unsafe_allow_html=True)
        return

    topic = r.get("topic")
    if topic not in session.concepts:
        try: sift.create_custom_topic(r["learner_id"], topic)
        except Exception: pass

    latest = None
    try:
        records = getattr(session.learner, "learning_records", []) or []
        matching = [x for x in records if str(getattr(x, "concept", "")).casefold() == str(topic).casefold()]
        if matching:
            latest = sorted(matching, key=lambda x: str(getattr(x, "created_at", "") or ""))[-1]
    except Exception:
        latest = None
    ev = _eval(latest) if latest else {}
    recommendation = recommendation_for(session) or {}
    cache_key = "|".join(str(x or "") for x in (r["learner_id"], topic, recommendation.get("strategy"), ev.get("mistake_type"), ev.get("misconception")))
    cache = st.session_state.setdefault("resource_cache", {})
    payload = cache.get(cache_key)
    resource_error = None
    if payload is None:
        try:
            with st.spinner("Sift is finding help for this exact learning moment…"):
                payload = sift.recommend_resources(
                    r["learner_id"], concept=topic, recommendation=recommendation,
                    mistake_type=ev.get("mistake_type"), misconception=ev.get("misconception")
                ) or {}
            cache[cache_key] = payload
        except Exception as exc:
            resource_error = str(exc)
            payload = {}
    if not isinstance(payload, dict): payload = {}

    st.markdown(f'<div class="resource-context"><div><b>{esc(r["subject"])} · {esc(topic)}</b><span>Contextual help · {esc(recommendation.get("strategy", "adaptive").replace("_", " "))}</span></div></div>', unsafe_allow_html=True)
    tip = payload.get("quick_tip"); video = payload.get("youtube")
    if isinstance(tip, dict):
        title = tip.get("title") or "Quick help"; body = tip.get("body") or ""; example = tip.get("example"); reason = tip.get("reason") or "Sift selected this because it supports the current concept."
        situation = tip.get("situation") or tip.get("when_useful") or "Use this when you are trying to connect the idea to a problem."
        next_move = tip.get("next_move") or tip.get("watch_for") or "Try the next question without looking back at the explanation."
        extra = f'<div class="resource-example"><b>Example</b><br>{esc(example)}</div>' if example else ''
        st.markdown(f'<div class="resource-featured"><div class="session-kicker">QUICK HELP · FOR THIS MOMENT</div><h3>{esc(title)}</h3><p>{esc(body)}</p><div class="resource-situation"><b>When this helps</b><span>{esc(situation)}</span></div>{extra}<div class="resource-situation"><b>Next move</b><span>{esc(next_move)}</span></div><div class="resource-reason"><strong>Why Sift recommends this</strong><br>{esc(reason)}</div></div>', unsafe_allow_html=True)
    if isinstance(video, dict): resource_card(video, featured=True)
    candidates = payload.get("youtube_candidates", []) or []
    if len(candidates) > 1:
        st.markdown('<div class="section-title">More from YouTube</div>', unsafe_allow_html=True)
        for item in candidates[1:5]:
            if isinstance(item, dict): resource_card(item)
    if resource_error and not tip and not video:
        st.markdown('<div class="resource-fallback"><b>External resources are temporarily unavailable.</b><span>Sift is still ready to teach this concept directly. You can continue the session without losing progress.</span></div>', unsafe_allow_html=True)
    elif not tip and not video:
        st.markdown('<div class="empty-chart">No external resource passed Sift’s relevance check for this moment. That is intentional — Sift will not recommend unrelated material.</div>', unsafe_allow_html=True)


def render_settings():
    page_header("Settings", "Personalize Sift", "A few preferences that shape how your sessions feel.")
    with st.form("settings_form"):
        name=st.text_input("Name",value=st.session_state.profile_name)
        style=st.selectbox("Default teaching style",["Adaptive","Guided","Balanced","Challenge"],index=["Adaptive","Guided","Balanced","Challenge"].index(st.session_state.new_style))
        cap=st.selectbox("Default session time",[10,20,30,45,60],index=[10,20,30,45,60].index(st.session_state.new_time),format_func=lambda x:f"{x} min")
        if st.form_submit_button("Save changes",type="primary"):
            st.session_state.profile_name=name.strip() or st.session_state.profile_name
            st.session_state.new_style=style; st.session_state.new_time=cap
            st.success("Settings saved.")
    if st.button("Sign out", key="sign_out"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()


# Routing
if not profile_ready():
    render_onboarding(); st.stop()

refresh_session_registry()
render_sidebar(current_learner())
view=get_current_view()
if view=="sessions": render_sessions()
elif view=="new_session": render_new_session()
elif view=="session": render_session()
elif view=="progress": render_progress()
elif view=="history": render_history()
elif view=="resources": render_resources()
elif view=="settings": render_settings()
else: render_sessions()
