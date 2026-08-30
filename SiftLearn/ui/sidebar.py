import streamlit as st
from ui.components import sidebar_brand, sidebar_profile

NAV = [
    ("sessions", "▣  Sessions"),
    ("progress", "◒  Progress"),
    ("history", "◷  History"),
    ("resources", "▤  Resources"),
]


def initialize_navigation():
    st.session_state.setdefault("current_view", "sessions")


def render_sidebar(learner=None):
    initialize_navigation()
    with st.sidebar:
        sidebar_brand()
        st.markdown('<div class="sidebar-section-label">WORKSPACE</div>', unsafe_allow_html=True)
        active = st.session_state.current_view == "sessions"
        c1, c2 = st.columns([5, 1], gap="small")
        with c1:
            if st.button("▣  Sessions", key="sidebar_sessions", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.current_view = "sessions"
                st.rerun()
        with c2:
            if st.button("+", key="sidebar_new_session", use_container_width=True, help="New session"):
                st.session_state.current_view = "new_session"
                st.rerun()
        for view_id, label in NAV[1:]:
            active = st.session_state.current_view == view_id
            if st.button(label, key=f"sidebar_{view_id}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.current_view = view_id
                st.rerun()
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        if st.button("⚙  Settings", key="sidebar_settings", use_container_width=True,
                     type="primary" if st.session_state.current_view == "settings" else "secondary"):
            st.session_state.current_view = "settings"
            st.rerun()
        if learner:
            sidebar_profile(getattr(learner, "name", "Learner"), "Learner")


def get_current_view():
    initialize_navigation()
    return st.session_state.current_view
