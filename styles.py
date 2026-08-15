import streamlit as st


def inject_css():
    st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&family=Inter:wght@300;400;500;600&display=swap');

  /* ── VIBRANT LIGHT PLANNER THEME TOKENS ── */
  :root {
    --bg:          #FFF9F2;
    --bg2:         #FFFFFF;
    --bg3:         #FFF3E9;
    --card:        #FFFFFF;
    --card-hover:  #FFF6EE;
    --border:      rgba(45,42,50,0.09);
    --border-glow: rgba(255,107,74,0.45);
    --coral:       #FF6B4A;
    --coral-dark:  #E5573A;
    --teal:        #14B8A6;
    --purple:      #8B5CF6;
    --amber:       #F5A623;
    --pink:        #EC4899;
    --green:       #22C55E;
    --text:        #2D2A32;
    --text-muted:  #8B8594;
    --radius:      14px;
    --shadow:      0 6px 20px rgba(45,42,50,0.08);
  }

  /* ── Warm cream background everywhere ── */
  html, body,
  [data-testid="stAppViewContainer"],
  [data-testid="stMain"],
  [data-testid="stMainBlockContainer"],
  .main, .block-container,
  section[data-testid="stSidebar"] ~ div,
  [data-testid="stVerticalBlock"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Inter', sans-serif !important;
  }

  /* ── Override the root app container ── */
  .stApp {
    background-color: var(--bg) !important;
  }

  /* ── Block container padding ── */
  .block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 1100px !important;
  }

  /* ── Hide Streamlit chrome ── */
  #MainMenu, footer, [data-testid="stDecoration"],
  [data-testid="stToolbar"], [data-testid="stStatusWidget"] {
    display: none !important;
  }

  /* ── Global text overrides ── */
  p, span, li, td, th, label, div,
  [data-testid="stMarkdownContainer"] p {
    color: var(--text) !important;
  }
  h1, h2, h3, h4, h5, h6 {
    color: var(--text) !important;
    font-family: 'Poppins', sans-serif !important;
  }
  strong, b { color: var(--text) !important; }
  .stMarkdown a { color: var(--coral) !important; }

  /* ── Metric cards (main area) ── */
  [data-testid="stMain"] [data-testid="metric-container"],
  .main [data-testid="metric-container"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-top: 3px solid var(--coral) !important;
    border-radius: var(--radius) !important;
    padding: 1.1rem 1.4rem !important;
    box-shadow: var(--shadow) !important;
    transition: transform 0.18s ease, box-shadow 0.18s ease !important;
  }
  [data-testid="stMain"] [data-testid="metric-container"]:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 10px 28px rgba(255,107,74,0.18) !important;
  }
  [data-testid="stMain"] [data-testid="stMetricValue"] {
    color: var(--coral) !important;
    font-family: 'Poppins', sans-serif !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
  }
  [data-testid="stMain"] [data-testid="stMetricLabel"] p {
    color: var(--text-muted) !important;
    font-size: 0.75rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
  }

  /* ── Travel cards ── */
  .travel-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem 1.3rem;
    margin: 0.5rem 0;
    box-shadow: var(--shadow);
    transition: all 0.2s ease;
  }
  .travel-card:hover {
    background: var(--card-hover);
    border-color: var(--border-glow);
    transform: translateY(-2px);
    box-shadow: 0 10px 28px rgba(255,107,74,0.16);
  }
  .card-title {
    font-family: 'Poppins', sans-serif;
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--text) !important;
    margin-bottom: 0.35rem;
  }
  .card-meta { font-size: 0.82rem; color: var(--text-muted) !important; }

  /* ── Category tags ── */
  .tag {
    display: inline-block;
    padding: 0.15rem 0.6rem;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    margin-right: 0.3rem;
  }
  .tag-activity { background: rgba(20,184,166,0.13);  color: #0D9488 !important; border: 1px solid rgba(20,184,166,0.35); }
  .tag-city     { background: rgba(255,107,74,0.13);  color: #E5573A !important; border: 1px solid rgba(255,107,74,0.35); }
  .tag-cafe     { background: rgba(236,72,153,0.13);  color: #DB2777 !important; border: 1px solid rgba(236,72,153,0.35); }
  .tag-drive    { background: rgba(34,197,94,0.13);   color: #16A34A !important; border: 1px solid rgba(34,197,94,0.35); }
  .tag-default  { background: rgba(139,92,246,0.13);  color: #7C3AED !important; border: 1px solid rgba(139,92,246,0.35); }
  .nearby-chip  { background: var(--bg3); color: var(--text-muted) !important; border: 1px solid var(--border); font-weight: 500; }

  /* ── Section headings ── */
  .section-heading {
    font-family: 'Poppins', sans-serif !important;
    font-size: 1.25rem !important;
    font-weight: 600 !important;
    color: var(--text) !important;
    margin: 1.5rem 0 0.8rem !important;
    letter-spacing: 0.01em;
    border-left: 4px solid var(--coral);
    padding-left: 0.75rem;
  }

  /* ── Expanders ── */
  [data-testid="stExpander"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    margin-bottom: 0.55rem !important;
    box-shadow: var(--shadow) !important;
  }
  [data-testid="stExpander"]:hover {
    border-color: var(--border-glow) !important;
  }
  [data-testid="stExpander"] summary,
  [data-testid="stExpander"] summary p,
  [data-testid="stExpander"] summary span {
    color: var(--text) !important;
    font-weight: 500 !important;
    font-size: 0.95rem !important;
  }
  /* expander inner background */
  [data-testid="stExpander"] > div > div {
    background: var(--card) !important;
  }

  /* ── Inputs & selects ── */
  .stTextInput > div > div > input,
  .stTextArea > div > textarea,
  .stNumberInput > div > div > input {
    background: var(--bg3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: 'Inter', sans-serif !important;
  }
  .stTextInput > div > div > input::placeholder,
  .stTextArea > div > textarea::placeholder {
    color: var(--text-muted) !important;
  }
  .stTextInput > div > div > input:focus,
  .stTextArea > div > textarea:focus {
    border-color: var(--coral) !important;
    box-shadow: 0 0 0 2px rgba(255,107,74,0.2) !important;
  }
  /* selectbox */
  [data-testid="stSelectbox"] > div > div,
  [data-baseweb="select"] > div {
    background: var(--bg3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
  }
  [data-baseweb="select"] span { color: var(--text) !important; }
  /* dropdown options */
  [data-baseweb="popover"] ul, [data-baseweb="popover"] li {
    background: var(--bg2) !important;
    color: var(--text) !important;
  }
  [data-baseweb="popover"] li:hover {
    background: var(--bg3) !important;
  }

  /* ── Slider ── */
  [data-testid="stSlider"] > div > div > div {
    background: var(--coral) !important;
  }
  [data-testid="stSlider"] label { color: var(--text) !important; }
  [data-testid="stSlider"] [data-testid="stTickBarMin"],
  [data-testid="stSlider"] [data-testid="stTickBarMax"] {
    color: var(--text-muted) !important;
  }

  /* ── Main area buttons ── */
  [data-testid="stMain"] .stButton > button,
  [data-testid="stMainBlockContainer"] .stButton > button {
    background: var(--bg3) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    min-height: 2.75rem !important;
    transition: all 0.18s ease !important;
  }
  [data-testid="stMain"] .stButton > button:hover,
  [data-testid="stMainBlockContainer"] .stButton > button:hover {
    background: rgba(255,107,74,0.12) !important;
    border-color: var(--border-glow) !important;
    color: var(--coral-dark) !important;
  }

  /* ── Link buttons ── */
  [data-testid="stLinkButton"] a {
    background: var(--bg3) !important;
    color: #0D9488 !important;
    border: 1px solid rgba(20,184,166,0.35) !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
  }
  [data-testid="stLinkButton"] a:hover {
    background: rgba(20,184,166,0.12) !important;
  }

  /* ── Form submit ── */
  .stFormSubmitButton > button {
    background: linear-gradient(135deg, #FF6B4A, #E5573A) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    height: 3em !important;
  }
  .stFormSubmitButton > button:hover {
    background: linear-gradient(135deg, #FF8266, #FF6B4A) !important;
  }

  /* ── Alerts / info boxes ── */
  [data-testid="stAlert"] {
    background: var(--bg3) !important;
    border-radius: var(--radius) !important;
  }
  [data-testid="stAlert"] p { color: var(--text) !important; }

  /* ── Progress bar ── */
  .progress-wrap {
    background: var(--bg3);
    border-radius: 8px;
    height: 10px;
    overflow: hidden;
    margin: 0.4rem 0 1rem;
    border: 1px solid var(--border);
  }
  .progress-fill {
    height: 100%;
    border-radius: 8px;
    background: linear-gradient(90deg, var(--teal), var(--coral));
    transition: width 1s cubic-bezier(0.4,0,0.2,1);
  }

  /* ── Stat badge ── */
  .stat-badge {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.4rem 0.85rem;
    font-size: 0.82rem;
    color: var(--text) !important;
    font-weight: 500;
  }
  .stat-badge strong { color: var(--coral) !important; }

  /* ── Dividers ── */
  hr { border-color: var(--border) !important; margin: 1.5rem 0 !important; }
  [data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--bg) !important;
  }

  /* ── Checkbox ── */
  [data-testid="stCheckbox"] label span { color: var(--text) !important; }

  /* ── Page header ── */
  .page-header {
    background: linear-gradient(135deg, #FFE9DE 0%, #FFF3E9 45%, #E3F9F3 100%);
    border: 1px solid var(--border);
    border-top: 3px solid var(--coral);
    padding: 2rem 2.5rem;
    border-radius: var(--radius);
    color: var(--text);
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
  }
  .page-header::after {
    content: '';
    position: absolute;
    bottom: -60px; right: -60px;
    width: 180px; height: 180px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255,107,74,0.14) 0%, transparent 70%);
  }
  .page-header h1 {
    font-family: 'Poppins', sans-serif !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
    margin: 0 !important;
    color: var(--text) !important;
    letter-spacing: 0.01em;
  }
  .page-header p {
    margin: 0.4rem 0 0 !important;
    color: var(--text-muted) !important;
    font-size: 0.95rem !important;
  }

  /* ── Login page ── */
  .login-box {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 2.5rem;
    box-shadow: 0 10px 40px rgba(255,107,74,0.12);
  }

  /* ── Top Navbar ── */
  .topnav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #FFFFFF;
    border: 1px solid var(--border);
    border-top: 3px solid var(--coral);
    border-radius: 14px;
    padding: 0.75rem 1.5rem;
    margin-bottom: 0.5rem;
    box-shadow: var(--shadow);
  }
  .topnav-left {
    display: flex;
    align-items: center;
    gap: 0.6rem;
  }
  .topnav-logo {
    font-size: 1.5rem;
    filter: drop-shadow(0 0 8px rgba(255,107,74,0.35));
  }
  .topnav-brand {
    font-family: 'Poppins', sans-serif !important;
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text) !important;
    letter-spacing: 0.01em;
  }
  .topnav-right {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  .topnav-user {
    color: var(--text) !important;
    font-size: 0.83rem;
    font-weight: 600;
  }
  .topnav-stat {
    color: var(--text-muted) !important;
    font-size: 0.8rem;
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 0.2rem 0.7rem;
  }

  /* ── Nav buttons row ── */
  .nav-btn button,
  .nav-btn-active button {
    border-radius: 10px !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    height: auto !important;
    min-height: 2.75rem !important;
    padding: 0.5rem 0.75rem !important;
    transition: all 0.18s ease !important;
    width: 100% !important;
  }
  .nav-btn button {
    background: var(--bg3) !important;
    color: var(--text-muted) !important;
    border: 1px solid var(--border) !important;
  }
  .nav-btn button:hover {
    background: rgba(255,107,74,0.1) !important;
    color: var(--coral-dark) !important;
    border-color: var(--border-glow) !important;
  }
  .nav-btn-active button {
    background: linear-gradient(135deg, #FF6B4A, #E5573A) !important;
    color: #FFFFFF !important;
    border: 1px solid var(--coral-dark) !important;
  }

  /* Refresh + Logout buttons */
  .nav-divider {
    height: 1px;
    background: var(--border);
    margin: 0.5rem 0 1.5rem;
  }

  /* ── Mobile tuning ── */
  @media (max-width: 768px) {
    .topnav { flex-direction: column; gap: 0.5rem; padding: 1rem; align-items: stretch; }
    .topnav-left { justify-content: center; }
    .topnav-right { flex-wrap: wrap; justify-content: center; gap: 0.5rem; }
    .page-header { padding: 1.3rem 1.5rem; }
    .page-header h1 { font-size: 1.55rem !important; }
    .section-heading { font-size: 1.1rem !important; }
    .block-container { padding-left: 0.75rem !important; padding-right: 0.75rem !important; padding-top: 1rem !important; }
    [data-testid="stMain"] [data-testid="stMetricValue"] { font-size: 1.6rem !important; }
    [data-testid="stMain"] [data-testid="metric-container"] { padding: 0.85rem 1rem !important; }
    .nav-btn button, .nav-btn-active button { font-size: 0.78rem !important; padding: 0.5rem 0.4rem !important; }
    [data-testid="stMain"] .stButton > button,
    [data-testid="stMainBlockContainer"] .stButton > button { min-height: 2.9rem !important; }
    .js-plotly-plot { min-height: 220px !important; }
  }

</style>
""", unsafe_allow_html=True)
