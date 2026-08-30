import streamlit as st
from datetime import datetime

from ui.components import page_header, focus_card, empty_card, track_visual, metric_card

DESCRIPTIONS = {
    "Python": "Build programming fluency through hands-on practice.",
    "Data Structures & Algorithms": "Master data structures and algorithmic thinking.",
    "Machine Learning": "Learn ML concepts and build intelligent systems.",
    "Mathematics": "Strengthen mathematical foundations and problem-solving.",
}

def _value(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)

def _mastery(session):
    concepts = _value(session, "concepts", {}) or {}
    vals=[]
    for c in concepts.values():
        try: vals.append(float(_value(c,"mastery",0) or 0))
        except (TypeError,ValueError): pass
    return sum(vals)/len(vals) if vals else 0.0

def _today_stats(learner):
    state=_value(learner,"activity_streak",{}) or {}
    today=datetime.now().astimezone().date().isoformat()
    minutes=float((state.get("daily_minutes",{}) or {}).get(today,0) or 0)
    turns=int((state.get("daily_turns",{}) or {}).get(today,0) or 0)
    concepts=list((state.get("daily_concepts",{}) or {}).get(today,[]) or [])
    return minutes,turns,len(concepts),state

def render_home(sift, subjects, active_subject, track_profiles, learner, session, recommendation=None):
    minutes, turns, concepts_today, streak = _today_stats(learner)
    target=int(_value(learner,"available_minutes",30) or 30)
    current_mastery=_mastery(session)
    focus=_value(session,"focus_concept",None)

    page_header("Sift", f"Your {active_subject} workspace.", "A calm command center for what you know, what needs attention, and what to do next.")

    # Today's momentum
    st.markdown('<div class="home-hero">', unsafe_allow_html=True)
    h1,h2,h3,h4=st.columns(4)
    with h1: metric_card("Learned today", f"{minutes:.0f} min", f"Target {target} min/day")
    with h2: metric_card("Learning turns", str(turns), "Completed learning evidence")
    with h3: metric_card("Concepts practiced", str(concepts_today), "Unique concepts today")
    with h4: metric_card("Streak", f"🔥 {int(streak.get('current',0) or 0)}", "Meaningful learning days")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">What should I do next?</div>', unsafe_allow_html=True)
    if recommendation and recommendation.get("concept"):
        concept=recommendation.get("concept")
        reason=recommendation.get("reason") or recommendation.get("diagnosis") or "Based on your current evidence in this track."
        focus_card(concept, "Sift picked the smallest useful next step. You can learn it, practice it, or focus on another topic.", reason, recommendation.get("strategy"))
        if st.button(f"Continue {concept} →", key="home_continue", type="primary", use_container_width=True):
            st.session_state.current_view="learn"; st.rerun()
    else:
        empty_card("Your next step is ready after a quick baseline", "Open Learn to give Sift its first useful evidence.")
        if st.button("Start learning →", key="home_start", type="primary", use_container_width=True):
            st.session_state.current_view="learn"; st.rerun()

    # Learner-directed topic entry
    st.markdown('<div class="section-title">Learn something you choose</div>', unsafe_allow_html=True)
    st.markdown('<div class="topic-intro">Sift does not require you to follow a fixed course. Type a concept, skill, exam topic, or question you want to work on. Sift will map it into an adaptive learning path.</div>', unsafe_allow_html=True)
    with st.form("personal_topic_form", clear_on_submit=True):
        topic=st.text_input("Your topic", placeholder="e.g. Stack, Python decorators, derivatives, transformers…", label_visibility="collapsed")
        c1,c2=st.columns([3,1])
        with c1: st.caption("Examples: a concept, interview topic, exam topic, or skill you want to build.")
        with c2: submit=st.form_submit_button("Focus on this →", type="primary", use_container_width=True)
    if submit:
        try:
            result=sift.create_custom_topic(st.session_state.track_profiles[active_subject],topic)
            st.session_state.current_view="learn"
            st.session_state.last_result=None
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    # Track map
    st.markdown('<div class="section-title">Your learning tracks</div>', unsafe_allow_html=True)
    cols=st.columns(min(4,max(1,len(subjects))))
    for col,subject in zip(cols,subjects):
        exists=subject in track_profiles; selected=subject==active_subject
        value=0.0
        if exists:
            try: value=_mastery(sift.get_session(track_profiles[subject]))
            except Exception: pass
        with col:
            st.markdown(
                f'<div class="track-card {"selected" if selected else ""}"><div class="track-visual">{track_visual(subject)}</div><div class="track-name">{subject}</div><div class="track-desc">{DESCRIPTIONS.get(subject,"Adaptive learning")}</div><div class="track-bottom"><span class="badge blue">{"Active" if selected else ("Ready" if exists else "Not started")}</span><span class="track-mastery">{value:.0f}%</span></div></div>',
                unsafe_allow_html=True)
            if not selected and exists and st.button("Switch →",key=f"home_switch_{subject}",use_container_width=True):
                st.session_state.active_track=subject; st.session_state.current_view="home"; st.session_state.last_result=None; st.session_state.resource_bundle=None; st.rerun()
            elif not exists and st.button("Add →",key=f"home_add_{subject}",use_container_width=True):
                st.session_state.add_track_subject=subject; st.session_state.current_view="add_track"; st.rerun()

    if focus:
        st.markdown(f'<div class="focus-pill">🎯 Focus path: <b>{focus}</b> · your main track remains intact</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Your week</div>', unsafe_allow_html=True)
    daily=(streak.get("daily_minutes",{}) or {})
    today=datetime.now().astimezone().date()
    cells=[]
    for offset in range(6,-1,-1):
        d=today.fromordinal(today.toordinal()-offset); key=d.isoformat(); val=float(daily.get(key,0) or 0)
        cells.append((d.strftime("%a"),val,d==today))
    html=''.join(f'<div class="week-cell {"today" if now else ""}"><b>{day}</b><span>{v:.0f}m</span><i style="opacity:{min(1,0.2+v/max(target,1)):.2f}"></i></div>' for day,v,now in cells)
    st.markdown(f'<div class="week-strip">{html}</div>',unsafe_allow_html=True)

    st.markdown('<div class="home-loop"><b>How Sift adapts</b><span>Observe</span><i>→</i><span>Diagnose</span><i>→</i><span>Help</span><i>→</i><span>Recheck</span><i>→</i><span>Adapt</span></div>',unsafe_allow_html=True)
