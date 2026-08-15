import streamlit as st
from auth import check_password
from sheets_data import load_travel_data
from styles import inject_css
from views import dashboard, to_visit, visited

# Page configuration
st.set_page_config(
    page_title="Travel Planner & Tracker",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

inject_css()

# ── Gate ─────────────────────────────────────────────────────────────────────
if not check_password():
    st.stop()

# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner("Loading your travel data…"):
    to_visit_df, visited_df, all_df = load_travel_data()

# ── Session state defaults ────────────────────────────────────────────────────
if 'current_view' not in st.session_state:
    st.session_state.current_view = "dashboard"


# ── Top Navbar ───────────────────────────────────────────────────────────────
logged_user = st.session_state.get("logged_in_user", "Traveler")
to_visit_cnt_nav = len(to_visit_df) if not to_visit_df.empty else 0
visited_cnt_nav  = len(visited_df)  if not visited_df.empty  else 0

# Build active-state highlighting
active = st.session_state.current_view

st.markdown(f"""
<div class="topnav">
  <div class="topnav-left">
    <span class="topnav-logo">✈️</span>
    <span class="topnav-brand">Travel Planner</span>
  </div>
  <div class="topnav-right">
    <span class="topnav-user">👤 {logged_user}</span>
    <span class="topnav-stat">📍 {to_visit_cnt_nav} to visit</span>
    <span class="topnav-stat">✅ {visited_cnt_nav} visited</span>
  </div>
</div>
""", unsafe_allow_html=True)

# Navigation row
nav_cols = st.columns([1, 1, 1, 0.6, 0.6])

nav_map = [
    ("dashboard", "🏠 Dashboard"),
    ("to_visit",  "📍 To Visit"),
    ("visited",   "✅ Visited"),
]
for i, (key, label) in enumerate(nav_map):
    with nav_cols[i]:
        is_active = (active == key)
        btn_style = "nav-btn-active" if is_active else "nav-btn"
        st.markdown(f'<div class="{btn_style}">', unsafe_allow_html=True)
        if st.button(label, key=f"nav_{key}", width="stretch"):
            st.session_state.current_view = key
        st.markdown('</div>', unsafe_allow_html=True)

with nav_cols[3]:
    if st.button("🔄 Refresh", width="stretch", key="refresh_btn"):
        load_travel_data.clear()

with nav_cols[4]:
    if st.button("🚪 Logout", width="stretch", key="logout_btn"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]

st.markdown('<div class="nav-divider"></div>', unsafe_allow_html=True)


# ── Views ─────────────────────────────────────────────────────────────────────
view = st.session_state.current_view

if view == "dashboard":
    dashboard.render(all_df, to_visit_df, visited_df)
elif view == "to_visit":
    to_visit.render(to_visit_df, all_df, logged_user)
elif view == "visited":
    visited.render(visited_df, all_df)


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:2.5rem 0 1.5rem;
            color:#B5AFB8; font-size:0.8rem; font-family:'Inter',sans-serif;
            border-top: 1px solid rgba(45,42,50,0.08); margin-top:2rem;">
  ✈️ &nbsp; Made with ❤️ for Aman &amp; Sandra
</div>
""", unsafe_allow_html=True)
