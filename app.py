import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
import hmac
import re
import time
import requests
from math import radians, sin, cos, asin, sqrt
from urllib.parse import unquote_plus

# ── Constants ────────────────────────────────────────────────────────────────
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
]
SPREADSHEET_NAME = "Our Travel List"

# Page configuration
st.set_page_config(
    page_title="Travel Planner & Tracker",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
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


# ── Helpers ─────────────────────────────────────────────────────────────────
def category_tag(cat):
    cat_lower = (cat or "").lower()
    if "activity" in cat_lower:
        cls = "tag-activity"
    elif "city" in cat_lower:
        cls = "tag-city"
    elif "cafe" in cat_lower or "restaurant" in cat_lower:
        cls = "tag-cafe"
    elif "drive" in cat_lower:
        cls = "tag-drive"
    else:
        cls = "tag-default"
    return f'<span class="tag {cls}">{cat}</span>'


def star_rating(rating):
    full = int(rating)
    half = 1 if (rating - full) >= 0.5 else 0
    empty = 5 - full - half
    return "★" * full + ("½" if half else "") + "☆" * empty


def grouped_frame(df, group_by):
    """Split df into (label, sub_df) groups, largest group first. group_by='None' returns a single unlabeled group."""
    if group_by == "None" or group_by not in df.columns:
        return [(None, df)]
    groups = [(key, g) for key, g in df.groupby(group_by, sort=False) if key]
    groups.sort(key=lambda kv: (-len(kv[1]), str(kv[0])))
    return groups


def resolve_groups(df, group_choice):
    """Dispatch a 'Group by' selectbox choice to the right grouping strategy."""
    if group_choice == "Nearby Area":
        return cluster_by_proximity(df)
    return grouped_frame(df, {"City": "City", "Category": "Category", "Area/Location": "Area/Location"}.get(group_choice, "None"))


def cluster_by_proximity(df, precision=2):
    """Bucket rows into ~1km grid cells by (Latitude, Longitude), largest cluster first.
    Rows without coordinates are appended as a trailing 'Unmapped' group instead of being dropped."""
    has_coords = df['Latitude'].notna() & df['Longitude'].notna() if 'Latitude' in df.columns else pd.Series(False, index=df.index)
    mapped, unmapped = df[has_coords], df[~has_coords]
    groups = []
    if not mapped.empty:
        buckets = pd.Series(list(zip(mapped['Latitude'].round(precision), mapped['Longitude'].round(precision))), index=mapped.index)
        for bucket, g in mapped.groupby(buckets, sort=False):
            areas = g['Area/Location'][g['Area/Location'] != '']
            label = areas.mode().iat[0] if not areas.mode().empty else (g['City'].iat[0] or "Unknown area")
            groups.append((label, g))
        groups.sort(key=lambda kv: -len(kv[1]))
    if not unmapped.empty:
        groups.append(("Unmapped", unmapped))
    return groups


# ── Coordinate resolution (Google Maps Link → lat/lon) ───────────────────────
DIR_COORD_RE   = re.compile(r'!1d(-?\d+\.\d+)!2d(-?\d+\.\d+)')       # directions link: (lng, lat)
PLACE_COORD_RE = re.compile(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)')       # place link: (lat, lng)
VIEWPORT_RE    = re.compile(r'/place/[^/]+/@(-?\d+\.\d+),(-?\d+\.\d+),')  # place viewport: (lat, lng)
DADDR_RE       = re.compile(r'daddr=([^&]+)')


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * r * asin(sqrt(a))


@st.cache_data(show_spinner=False)
def _resolve_short_link(url):
    """Follow a maps.app.goo.gl short-link redirect and return the final long URL."""
    try:
        resp = requests.get(url, allow_redirects=True, timeout=6,
                             headers={"User-Agent": "Mozilla/5.0"}, stream=True)
        final_url = resp.url
        resp.close()
        return final_url
    except requests.RequestException:
        return None


def _extract_coords_from_url(url):
    m = DIR_COORD_RE.search(url)
    if m:
        lng, lat = m.groups()
        return float(lat), float(lng)
    m = PLACE_COORD_RE.search(url)
    if m:
        lat, lng = m.groups()
        return float(lat), float(lng)
    m = VIEWPORT_RE.search(url)
    if m:
        lat, lng = m.groups()
        return float(lat), float(lng)
    return None


@st.cache_data(show_spinner=False)
def _geocode_text(query):
    """Free OpenStreetMap/Nominatim lookup, used as a last resort when no coordinates are embedded."""
    if not query:
        return None
    try:
        time.sleep(1)  # respect Nominatim's 1 req/sec usage policy
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "json", "limit": 1},
            headers={"User-Agent": "TravelPlannerApp/1.0"},
            timeout=6,
        )
        results = resp.json()
        if results:
            return float(results[0]["lat"]), float(results[0]["lon"])
    except (requests.RequestException, ValueError, KeyError, IndexError):
        pass
    return None


@st.cache_data(show_spinner=False)
def resolve_coordinates(link, fallback_query):
    """(lat, lon) for a place derived from its Google Maps Link, or None if unresolvable."""
    link = (link or "").strip()
    if link.startswith(("http://", "https://")):
        url = link
        if "goo.gl" in url:
            url = _resolve_short_link(url) or url
        coords = _extract_coords_from_url(url)
        if coords:
            return coords
        m = DADDR_RE.search(url)
        if m:
            return _geocode_text(unquote_plus(m.group(1)))
        return None
    if link:
        return _geocode_text(f"{link}, {fallback_query}")
    return _geocode_text(fallback_query) if fallback_query else None


def enrich_coordinates(df):
    if df.empty:
        return df
    def _row_coords(row):
        fallback = ", ".join(p for p in [row.get('Area/Location', ''), row.get('City', ''), row.get('Country', '')] if p)
        return resolve_coordinates(row.get('Google Maps Link', ''), fallback) or (None, None)
    coords = df.apply(_row_coords, axis=1)
    df['Latitude']  = [c[0] for c in coords]
    df['Longitude'] = [c[1] for c in coords]
    return df


def _is_food_category(cat):
    c = (cat or '').lower()
    return 'cafe' in c or 'restaurant' in c


def find_nearby(all_places_df, row, n=3, max_km=5):
    """Closest other places — across both To Visit and Visited — within max_km by real distance
    when coordinates are available, else by shared Area/Location or City. Tries to include at
    least one complementary spot: a cafe/restaurant near a city/activity/drive spot, or vice versa."""
    if all_places_df.empty:
        return all_places_df.iloc[0:0]
    candidates = all_places_df[all_places_df['Place Name'] != row.get('Place Name')]
    lat, lng = row.get('Latitude'), row.get('Longitude')

    if pd.notna(lat) and pd.notna(lng) and 'Latitude' in candidates.columns:
        pool = candidates[candidates['Latitude'].notna() & candidates['Longitude'].notna()].copy()
        if not pool.empty:
            pool['_diff'] = pool.apply(lambda r: haversine_km(lat, lng, r['Latitude'], r['Longitude']), axis=1)
            pool = pool[pool['_diff'] <= max_km].sort_values('_diff')
        if not pool.empty:
            current_is_food = _is_food_category(row.get('Category', ''))
            result = pool.head(n)
            has_complement = (result['Category'].apply(_is_food_category) != current_is_food).any()
            if not has_complement:
                complement = pool[pool['Category'].apply(_is_food_category) != current_is_food].head(1)
                if not complement.empty:
                    result = pd.concat([result.head(n - 1), complement]).sort_values('_diff')
            return result.head(n)
        return pool  # coordinates present but nothing within max_km — no text fallback needed

    area = row.get('Area/Location', '')
    city = row.get('City', '')
    same_area = candidates[candidates['Area/Location'] == area] if area else candidates.iloc[0:0]
    same_city = candidates[candidates['City'] == city] if city else candidates.iloc[0:0]
    pool = pd.concat([same_area, same_city])
    pool = pool[~pool.index.duplicated(keep='first')]
    if pool.empty:
        return pool
    if 'Distance(kms)' in pool.columns:
        ref_dist = row.get('Distance(kms)', 0) or 0
        pool = pool.assign(_diff=(pool['Distance(kms)'].fillna(0) - ref_dist).abs()).sort_values('_diff')
    return pool.head(n)


def render_nearby(all_places_df, row):
    nearby = find_nearby(all_places_df, row)
    if nearby.empty:
        return
    has_dist = '_diff' in nearby.columns and pd.notna(row.get('Latitude')) and pd.notna(row.get('Longitude'))
    chips = []
    for _, r in nearby.iterrows():
        icon = "✅" if r.get('Visited') else "📍"
        label = f"{icon} {r['Place Name']}"
        if has_dist:
            label += f" · {r['_diff']:.1f} km"
        chips.append(f'<span class="tag nearby-chip">{label}</span>')
    st.markdown(
        f"<div class='card-meta' style='margin-top:0.7rem;'>🧭 <strong>Nearby (within 5 km):</strong> {' '.join(chips)}</div>",
        unsafe_allow_html=True,
    )


def apply_text_search(df, query, fields=('Place Name', 'City', 'Area/Location', 'Category')):
    if not query:
        return df
    q = query.strip().lower()
    mask = False
    for field in fields:
        if field in df.columns:
            mask = mask | df[field].astype(str).str.lower().str.contains(q, na=False)
    return df[mask] if mask is not False else df


# ── Auth ─────────────────────────────────────────────────────────────────────
def check_password():
    def login_form():
        col_l, col_m, col_r = st.columns([1, 2, 1])
        with col_m:
            st.markdown("""
            <div style="text-align:center; padding: 2.5rem 0 1.5rem;">
              <div style="font-size:4rem; margin-bottom:0.6rem;
                          filter: drop-shadow(0 0 20px rgba(255,107,74,0.35));">✈️</div>
              <div style="font-family:'Poppins',sans-serif; font-size:1.9rem;
                          font-weight:700; color:#2D2A32; margin-bottom:0.3rem;
                          letter-spacing:0.01em;">
                Travel Planner
              </div>
              <div style="color:#8B8594; font-size:0.9rem; margin-bottom:2rem;
                          letter-spacing:0.05em; text-transform:uppercase; font-size:0.75rem;">
                Your personal adventure tracker
              </div>
            </div>
            """, unsafe_allow_html=True)

            with st.form("Credentials"):
                st.text_input("👤  Username", key="username", placeholder="Enter username")
                st.text_input("🔑  Password", type="password", key="password",
                              placeholder="Enter password")
                st.form_submit_button("Sign In →", on_click=password_entered, width="stretch")

    def password_entered():
        try:
            username = st.session_state["username"].strip()
            password = st.session_state["password"]
            stored   = st.secrets["passwords"]
            # Case-insensitive username lookup so "sandra" matches "Sandra"
            matched  = next((u for u in stored if u.lower() == username.lower()), None)
            if matched and hmac.compare_digest(password, str(stored[matched])):
                st.session_state["password_correct"] = True
                st.session_state["logged_in_user"]   = matched  # use canonical casing
                del st.session_state["password"]
                del st.session_state["username"]
            else:
                st.session_state["password_correct"] = False
        except Exception:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    login_form()
    if "password_correct" in st.session_state:
        st.error("😕 Incorrect username or password — please try again.")
    return False


# ── Google Sheets client (cached for the app session) ────────────────────────
@st.cache_resource
def get_gspread_client():
    return gspread.service_account_from_dict(st.secrets["gsheets"], scopes=SCOPES)


# ── Data loading ─────────────────────────────────────────────────────────────
def _fetch_chip_links(sh, worksheet_title, column_name, n_rows):
    """Google Sheets 'Smart Chip' cells (e.g. pasted Maps links) only expose their display
    text through get_all_records(); the real URI lives in chipRuns, reachable only via a raw
    Sheets API call. Returns a list of URIs (or None), positionally aligned with the sheet's
    data rows (index 0 = first row below the header). Returns [] on any failure."""
    if n_rows == 0:
        return []
    try:
        ws = sh.worksheet(worksheet_title)
        headers = ws.row_values(1)
        if column_name not in headers:
            return []
        col_letter = gspread.utils.rowcol_to_a1(1, headers.index(column_name) + 1).rstrip('0123456789')
        resp = sh.client.session.get(
            f"https://sheets.googleapis.com/v4/spreadsheets/{sh.id}",
            params={
                "ranges": f"'{worksheet_title}'!{col_letter}2:{col_letter}{n_rows + 1}",
                "includeGridData": "true",
                "fields": "sheets.data.rowData.values(chipRuns)",
            },
            timeout=10,
        )
        row_data = resp.json()["sheets"][0]["data"][0].get("rowData", [])
    except (requests.RequestException, KeyError, IndexError, ValueError):
        return []

    uris = []
    for r in row_data:
        vals = r.get("values", [])
        chip_runs = vals[0].get("chipRuns") if vals else None
        uri = None
        if chip_runs:
            uri = chip_runs[0].get("chip", {}).get("richLinkProperties", {}).get("uri")
        uris.append(uri)
    return uris


def _apply_chip_links(df, chip_uris, column_name="Google Maps Link"):
    if not chip_uris or column_name not in df.columns:
        return df
    originals = df[column_name].tolist()
    df[column_name] = [uri or original for uri, original in zip(chip_uris, originals)] + originals[len(chip_uris):]
    return df


@st.cache_data(ttl=300)
def load_travel_data():
    try:
        if "gsheets" not in st.secrets:
            st.error("Google Sheets credentials not found in secrets")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        gc = get_gspread_client()
        sh = gc.open(SPREADSHEET_NAME)

        to_visit_data = sh.worksheet("To Visit").get_all_records()
        visited_data  = sh.worksheet("Visited").get_all_records()

        to_visit_df = pd.DataFrame(to_visit_data) if to_visit_data else pd.DataFrame()
        visited_df  = pd.DataFrame(visited_data)  if visited_data  else pd.DataFrame()

        to_visit_df = _apply_chip_links(to_visit_df, _fetch_chip_links(sh, "To Visit", "Google Maps Link", len(to_visit_df)))
        visited_df  = _apply_chip_links(visited_df,  _fetch_chip_links(sh, "Visited",  "Google Maps Link", len(visited_df)))

        to_visit_df = clean_dataframe(to_visit_df, sheet_type="to_visit")
        visited_df  = clean_dataframe(visited_df,  sheet_type="visited")

        to_visit_df = enrich_coordinates(to_visit_df)
        visited_df  = enrich_coordinates(visited_df)

        if not to_visit_df.empty:
            to_visit_df = to_visit_df.assign(Visited=False)
        if not visited_df.empty:
            visited_df = visited_df.assign(Visited=True)
        all_df = pd.concat([to_visit_df, visited_df], ignore_index=True)
        return to_visit_df, visited_df, all_df

    except gspread.exceptions.SpreadsheetNotFound:
        st.error("Spreadsheet 'Our Travel List' not found.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    except gspread.exceptions.WorksheetNotFound:
        st.error("Required worksheets ('To Visit' or 'Visited') not found.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


def clean_dataframe(df, sheet_type="to_visit"):
    if df.empty:
        return df
    df = df.dropna(how='all')
    df.columns = [str(col).strip() for col in df.columns]
    column_mapping = {
        'Place Name': 'Place Name', 'PlaceName': 'Place Name', 'placename': 'Place Name',
        'Category': 'Category', 'City': 'City',
        'Area / Location': 'Area/Location', 'Area/Location': 'Area/Location', 'Area': 'Area/Location',
        'Location': 'Area/Location',
        'Country': 'Country',
        'Estimated Cost': 'Estimated Cost', 'EstimatedCost': 'Estimated Cost', 'Cost': 'Estimated Cost',
        'Total Cost': 'Estimated Cost',
        'Distance(kms)': 'Distance(kms)', 'Distance': 'Distance(kms)',
        'Best Time to Visit': 'Best Time to Visit', 'BestTime': 'Best Time to Visit',
        'Ideal For': 'Ideal For', 'IdealFor': 'Ideal For',
        'Added By': 'Added By', 'AddedBy': 'Added By',
        'Google Maps Link': 'Google Maps Link', 'Maps Link': 'Google Maps Link',
        'Google Rating': 'Google Rating', 'Rating': 'Google Rating',
        'Memory': 'Memory', 'Revisit Worthy': 'Revisit Worthy',
    }
    df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns}, inplace=True)

    dtype_handlers = {
        'Place Name':        lambda x: str(x).strip() if pd.notna(x) else '',
        'Category':          lambda x: str(x).strip() if pd.notna(x) else '',
        'City':              lambda x: str(x).strip() if pd.notna(x) else '',
        'Area/Location':     lambda x: str(x).strip() if pd.notna(x) else '',
        'Country':           lambda x: str(x).strip() if pd.notna(x) else 'India',
        'Estimated Cost':    parse_cost,
        'Distance(kms)':     parse_distance,
        'Best Time to Visit':lambda x: str(x).strip() if pd.notna(x) else 'Anytime',
        'Ideal For':         lambda x: str(x).strip() if pd.notna(x) else '',
        'Added By':          lambda x: str(x).strip() if pd.notna(x) else '',
        'Google Maps Link':  lambda x: str(x).strip() if pd.notna(x) and str(x).strip().startswith(('http://', 'https://')) else '',
        'Google Rating':     parse_rating,
    }
    for col, handler in dtype_handlers.items():
        if col in df.columns:
            df[col] = df[col].apply(handler)
        else:
            if col in ['Place Name', 'Category', 'City']:
                df[col] = ''
            else:
                df[col] = '' if col not in ['Estimated Cost', 'Distance(kms)', 'Google Rating'] else 0

    if sheet_type == "visited":
        if 'Date Visited'     in df.columns: df['Date Visited']     = pd.to_datetime(df['Date Visited'],    errors='coerce').dt.date
        if 'Rating (Aman)'    in df.columns: df['Rating (Aman)']    = df['Rating (Aman)'].apply(parse_rating)
        if 'Rating (Sandra)'  in df.columns: df['Rating (Sandra)']  = df['Rating (Sandra)'].apply(parse_rating)
        if 'Memory'           in df.columns: df['Memory']           = df['Memory'].apply(lambda x: str(x).strip() if pd.notna(x) else '')
        if 'Revisit Worthy'   in df.columns: df['Revisit Worthy']   = df['Revisit Worthy'].apply(lambda x: str(x).strip() if pd.notna(x) else '')
    return df


def parse_cost(cost):
    if pd.isna(cost) or cost == '': return 0
    if isinstance(cost, (int, float)): return float(cost)
    if isinstance(cost, str):
        cost = cost.strip().lower()
        if cost in ['free', '0', '']: return 0
        cost = re.sub(r'[₹$,]', '', cost)
        if '-' in cost:
            parts = cost.split('-')
            try:
                nums = [float(p.strip()) for p in parts if p.strip()]
                if nums: return sum(nums) / len(nums)
            except (ValueError, TypeError): pass
        try: return float(cost)
        except (ValueError, TypeError): return 0
    return 0


def parse_distance(distance):
    if pd.isna(distance) or distance == '': return 0
    if isinstance(distance, (int, float)): return float(distance)
    if isinstance(distance, str):
        distance = re.sub(r'[km\s]', '', distance.lower())
        try: return float(distance)
        except (ValueError, TypeError): return 0
    return 0


def parse_rating(rating):
    if pd.isna(rating) or rating == '': return 0.0
    if isinstance(rating, (int, float)): return min(float(rating), 5.0)
    if isinstance(rating, str):
        numbers = re.findall(r"[\d.]+", rating)
        if numbers:
            try: return min(float(numbers[0]), 5.0)
            except (ValueError, TypeError): pass
    return 0.0


def _serialize(v):
    """Convert a cell value to a type gspread can safely write."""
    try:
        if pd.isna(v):
            return ''
    except (TypeError, ValueError):
        pass
    if hasattr(v, 'isoformat'):   # datetime.date / datetime.datetime
        return v.isoformat()
    return v


def update_google_sheet(sheet_name, data):
    try:
        gc = get_gspread_client()
        sh = gc.open(SPREADSHEET_NAME)
        worksheet = sh.worksheet(sheet_name)
        worksheet.batch_clear(['A2:ZZ'])
        if not data.empty:
            headers = data.columns.tolist()
            values  = [[_serialize(v) for v in row] for row in data.values.tolist()]
            worksheet.update([headers] + values)
        return True
    except Exception as e:
        st.error(f"Error updating Google Sheets: {str(e)}")
        return False


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

# ════════════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════════════
if view == "dashboard":
    st.markdown("""
    <div class="page-header">
      <h1>🏠 Dashboard</h1>
      <p>Track every adventure — places dreamed of and memories made.</p>
    </div>
    """, unsafe_allow_html=True)

    if all_df.empty:
        st.warning("No travel data found. Check your Google Sheets connection.")
    else:
        all_places    = all_df
        total         = len(all_places)
        visited_count = len(visited_df)
        to_visit_cnt  = len(to_visit_df)
        progress_pct  = (visited_count / total * 100) if total > 0 else 0
        unique_cities = all_places['City'].nunique() if 'City' in all_places.columns else 0

        # ── Metrics (2 rows of 3 — reads as a card grid, stacks cleanly on mobile) ──
        m1, m2, m3 = st.columns(3)
        m4, m5, m6 = st.columns(3)
        m1.metric("📌 Total Places", total)
        m2.metric("✅ Visited",       visited_count)
        m3.metric("📍 To Visit",      to_visit_cnt)
        m4.metric("🏙️ Cities",        unique_cities)
        if 'Estimated Cost' in visited_df.columns:
            m5.metric("💸 Total Spent", f"₹{visited_df['Estimated Cost'].sum():,.0f}")
        else:
            m5.metric("💸 Total Spent", "N/A")
        if 'Estimated Cost' in to_visit_df.columns:
            m6.metric("💰 Planned",    f"₹{to_visit_df['Estimated Cost'].sum():,.0f}")
        else:
            m6.metric("💰 Planned",    "N/A")

        # ── Progress bar ─────────────────────────────
        st.markdown(f"""
        <div style="margin: 1.5rem 0 0.5rem;">
          <div style="display:flex; justify-content:space-between;
                      font-size:0.82rem; color:#8B8594; margin-bottom:0.4rem;">
            <span>Adventure Progress</span>
            <span><strong style="color:#FF6B4A;">{progress_pct:.1f}%</strong> explored</span>
          </div>
          <div class="progress-wrap">
            <div class="progress-fill" style="width:{progress_pct:.1f}%;"></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # ── Donut + Top Cities ────────────────────────
        ch1, ch2 = st.columns(2)

        with ch1:
            st.markdown('<div class="section-heading">🍩 Visited vs. To Visit</div>', unsafe_allow_html=True)
            donut_fig = go.Figure(go.Pie(
                labels=["Visited", "To Visit"],
                values=[visited_count, to_visit_cnt],
                hole=0.62,
                marker=dict(colors=["#FF6B4A", "#F0EAE2"], line=dict(color="#FFFFFF", width=2)),
                textinfo="percent+label",
                textfont=dict(family="Inter", size=12, color="#2D2A32"),
            ))
            donut_fig.update_layout(
                height=280,
                showlegend=False,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                annotations=[dict(
                    text=f"<b>{progress_pct:.0f}%</b>",
                    x=0.5, y=0.5, font_size=22,
                    font_family="Poppins",
                    font_color="#FF6B4A",
                    showarrow=False
                )],
            )
            st.plotly_chart(donut_fig, width="stretch")

        with ch2:
            st.markdown('<div class="section-heading">📊 Top Cities to Visit</div>', unsafe_allow_html=True)
            if not to_visit_df.empty and 'City' in to_visit_df.columns:
                city_counts = to_visit_df['City'].value_counts().head(6)
                if not city_counts.empty:
                    fig = px.bar(
                        x=city_counts.values, y=city_counts.index,
                        orientation='h',
                        labels={'x': 'Places', 'y': ''},
                        color=city_counts.values,
                        color_continuous_scale=["#FFD9C7", "#FF6B4A"],
                    )
                    fig.update_layout(
                        showlegend=False,
                        coloraxis_showscale=False,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=0, r=0, t=10, b=0),
                        height=280,
                        yaxis=dict(tickfont=dict(family='Inter', size=12, color='#8B8594'), gridcolor='rgba(45,42,50,0.08)'),
                        xaxis=dict(showgrid=True, gridcolor='rgba(45,42,50,0.08)', tickfont=dict(color='#8B8594')),
                    )
                    fig.update_traces(marker_line_width=0)
                    st.plotly_chart(fig, width="stretch")

        # ── Category + City distribution ─────────────
        st.markdown("---")
        st.markdown('<div class="section-heading">📂 Category Distribution</div>', unsafe_allow_html=True)

        cc1, cc2 = st.columns(2)
        with cc1:
            if 'Category' in all_places.columns:
                cat_data = all_places.groupby('Category').agg(
                    Total=('Category', 'count')
                ).reset_index().sort_values('Total', ascending=False)
                fig_cat = px.bar(
                    cat_data, x='Category', y='Total',
                    color='Total',
                    color_continuous_scale=["#F3D9FB", "#8B5CF6"],
                    labels={'Total': 'Places', 'Category': ''},
                )
                fig_cat.update_layout(
                    showlegend=False,
                    coloraxis_showscale=False,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=0, r=0, t=10, b=0),
                    height=280,
                    xaxis=dict(tickangle=-20, tickfont=dict(family='Inter', size=11, color='#8B8594'), gridcolor='rgba(45,42,50,0.08)'),
                    yaxis=dict(showgrid=True, gridcolor='rgba(45,42,50,0.08)', tickfont=dict(color='#8B8594')),
                )
                fig_cat.update_traces(marker_line_width=0)
                st.plotly_chart(fig_cat, width="stretch")

        with cc2:
            if 'City' in all_places.columns:
                city_data = all_places['City'].value_counts().head(8).reset_index()
                city_data.columns = ['City', 'Count']
                fig_city = px.bar(
                    city_data, x='Count', y='City',
                    orientation='h',
                    color='Count',
                    color_continuous_scale=["#B8ECE6", "#14B8A6"],
                    labels={'Count': 'Places', 'City': ''},
                )
                fig_city.update_layout(
                    showlegend=False,
                    coloraxis_showscale=False,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=0, r=0, t=10, b=0),
                    height=280,
                    yaxis=dict(tickfont=dict(family='Inter', size=11, color='#8B8594')),
                    xaxis=dict(showgrid=True, gridcolor='rgba(45,42,50,0.08)', tickfont=dict(color='#8B8594')),
                )
                fig_city.update_traces(marker_line_width=0)
                st.plotly_chart(fig_city, width="stretch")

        # ── Cost distribution ─────────────────────────
        if 'Estimated Cost' in all_places.columns:
            cost_data = all_places[all_places['Estimated Cost'] > 0]['Estimated Cost']
            if not cost_data.empty:
                st.markdown("---")
                st.markdown('<div class="section-heading">💰 Cost Distribution</div>', unsafe_allow_html=True)
                fig_hist = px.histogram(
                    cost_data, nbins=25,
                    labels={'value': 'Estimated Cost (₹)', 'count': 'Places'},
                    color_discrete_sequence=["#F5A623"],
                )
                fig_hist.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=0, r=0, t=10, b=0),
                    height=260,
                    bargap=0.1,
                    xaxis=dict(showgrid=True, gridcolor='rgba(45,42,50,0.08)', tickfont=dict(color='#8B8594')),
                    yaxis=dict(showgrid=True, gridcolor='rgba(45,42,50,0.08)', tickfont=dict(color='#8B8594')),
                )
                st.plotly_chart(fig_hist, width="stretch")


# ════════════════════════════════════════════════════════════
# TO VISIT
# ════════════════════════════════════════════════════════════
elif view == "to_visit":
    st.markdown("""
    <div class="page-header">
      <h1>📍 Places To Visit</h1>
      <p>Your wishlist of destinations waiting to be explored.</p>
    </div>
    """, unsafe_allow_html=True)

    if to_visit_df.empty:
        st.warning("No places in your 'To Visit' list yet. Add some places to get started!")
    else:
        # Search
        search_query = st.text_input("🔍 Search places", placeholder="Search by name, city, area, or category…",
                                     label_visibility="collapsed", key="tv_search")
        # Filters
        with st.container():
            fc1, fc2, fc3, fc4, fc5 = st.columns(5)
            with fc1:
                categories      = ['All'] + sorted(to_visit_df['Category'].dropna().unique().tolist())
                category_filter = st.selectbox("🗂️ Category", categories)
            with fc2:
                cities      = ['All'] + sorted(to_visit_df['City'].dropna().unique().tolist())
                city_filter = st.selectbox("🏙️ City", cities)
            with fc3:
                if 'Distance(kms)' in to_visit_df.columns:
                    max_d    = int(to_visit_df['Distance(kms)'].max()) if not to_visit_df['Distance(kms)'].isna().all() else 500
                    max_dist = st.slider("📏 Max Distance (km)", 0, max(max_d, 1), min(50, max_d))
            with fc4:
                tv_sort = st.selectbox("🔃 Sort by",
                                       ["Default", "Distance (Nearest)", "Cost (Lowest)", "Rating (Highest)"],
                                       key="tv_sort")
            with fc5:
                tv_group = st.selectbox("📁 Group by", ["None", "City", "Area/Location", "Category", "Nearby Area"], key="tv_group")

        # Apply filters
        filtered_df = apply_text_search(to_visit_df, search_query)
        if category_filter != 'All':
            filtered_df = filtered_df[filtered_df['Category'] == category_filter]
        if city_filter != 'All':
            filtered_df = filtered_df[filtered_df['City'] == city_filter]
        if 'Distance(kms)' in to_visit_df.columns:
            filtered_df = filtered_df[filtered_df['Distance(kms)'] <= max_dist]

        # Apply sort
        if tv_sort == "Distance (Nearest)" and 'Distance(kms)' in filtered_df.columns:
            filtered_df = filtered_df.sort_values('Distance(kms)', ascending=True, na_position='last')
        elif tv_sort == "Cost (Lowest)" and 'Estimated Cost' in filtered_df.columns:
            filtered_df = filtered_df.sort_values('Estimated Cost', ascending=True, na_position='last')
        elif tv_sort == "Rating (Highest)" and 'Google Rating' in filtered_df.columns:
            filtered_df = filtered_df.sort_values('Google Rating', ascending=False, na_position='last')

        st.markdown(f"""
        <div class="stat-badge" style="margin:0.75rem 0 1rem;">
          📋 &nbsp;<strong>{len(filtered_df)}</strong> of <strong>{len(to_visit_df)}</strong> places shown
        </div>
        """, unsafe_allow_html=True)

        if filtered_df.empty:
            st.info("No places match your search or filters.")
            if st.button("✖️ Clear filters", key="tv_clear"):
                for k in ("tv_search", "tv_group"):
                    st.session_state.pop(k, None)
                st.rerun()
        else:
            for group_label, group_df in resolve_groups(filtered_df, tv_group):
                if group_label is not None:
                    st.markdown(
                        f'<div class="section-heading">📁 {group_label} '
                        f'<span style="font-size:0.8rem;color:var(--text-muted);font-weight:500;">({len(group_df)})</span></div>',
                        unsafe_allow_html=True,
                    )
                for idx, row in group_df.iterrows():
                    name = row.get('Place Name', 'Unknown')
                    cat  = row.get('Category', '')
                    with st.expander(f"📍  {name}  —  {cat}"):
                        d1, d2 = st.columns([2, 1])

                        with d1:
                            location_parts = [p for p in [
                                row.get('Area/Location', ''), row.get('City', ''), row.get('Country', '')
                            ] if p]
                            st.markdown(f"**📍 Location:** {', '.join(location_parts)}")

                            cost_val = row.get('Estimated Cost', 0)
                            cost_str = f"₹{cost_val:,.0f}" if cost_val and float(cost_val) > 0 else "Free / Unknown"
                            st.markdown(f"**💰 Cost:** {cost_str}")

                            dist = row.get('Distance(kms)', 0)
                            if dist and float(dist) > 0:
                                st.markdown(f"**📏 Distance:** {float(dist):.1f} km")

                            if row.get('Ideal For'):
                                st.markdown(f"**👥 Ideal For:** {row['Ideal For']}")

                            if row.get('Best Time to Visit'):
                                st.markdown(f"**🗓️ Best Time:** {row['Best Time to Visit']}")

                        with d2:
                            g_rating = row.get('Google Rating', 0)
                            if g_rating and float(g_rating) > 0:
                                st.markdown(f"**⭐ Google Rating:** {star_rating(g_rating)} ({float(g_rating):.1f})")

                            maps_link = row.get('Google Maps Link', '')
                            if maps_link and str(maps_link).startswith(('http://', 'https://')):
                                st.link_button("🗺️ View on Maps", maps_link)

                        render_nearby(all_df, row)


# ════════════════════════════════════════════════════════════
# VISITED
# ════════════════════════════════════════════════════════════
elif view == "visited":
    st.markdown("""
    <div class="page-header">
      <h1>✅ Visited Places</h1>
      <p>Every place that shaped your journey — beautifully catalogued.</p>
    </div>
    """, unsafe_allow_html=True)

    if visited_df.empty:
        st.info("No visited places yet. Start exploring and mark them here!")
    else:
        # Search
        search_query_v = st.text_input("🔍 Search places", placeholder="Search by name, city, area, or category…",
                                       label_visibility="collapsed", key="v_search")
        # Filters
        vc1, vc2, vc3, vc4 = st.columns(4)
        with vc1:
            v_cats       = ['All'] + sorted(visited_df['Category'].dropna().unique().tolist())
            v_cat_filter = st.selectbox("🗂️ Category", v_cats, key="v_cat")
        with vc2:
            v_cities      = ['All'] + sorted(visited_df['City'].dropna().unique().tolist())
            v_city_filter = st.selectbox("🏙️ City", v_cities, key="v_city")
        with vc3:
            sort_by = st.selectbox("🔃 Sort by", ["Default", "Date (Newest First)", "Date (Oldest First)"],
                                   key="v_sort")
        with vc4:
            v_group = st.selectbox("📁 Group by", ["None", "City", "Area/Location", "Category", "Nearby Area"], key="v_group")

        # Apply filters
        v_filtered = apply_text_search(visited_df, search_query_v)
        if v_cat_filter != 'All':
            v_filtered = v_filtered[v_filtered['Category'] == v_cat_filter]
        if v_city_filter != 'All':
            v_filtered = v_filtered[v_filtered['City'] == v_city_filter]
        if sort_by == "Date (Newest First)" and 'Date Visited' in v_filtered.columns:
            v_filtered = v_filtered.sort_values('Date Visited', ascending=False, na_position='last')
        elif sort_by == "Date (Oldest First)" and 'Date Visited' in v_filtered.columns:
            v_filtered = v_filtered.sort_values('Date Visited', ascending=True, na_position='last')

        st.markdown(f"""
        <div class="stat-badge" style="margin:0.75rem 0 1rem;">
          🗺️ &nbsp;<strong>{len(v_filtered)}</strong> of <strong>{len(visited_df)}</strong> adventures shown
        </div>
        """, unsafe_allow_html=True)

        if v_filtered.empty:
            st.info("No places match your search or filters.")
            if st.button("✖️ Clear filters", key="v_clear"):
                for k in ("v_search", "v_group"):
                    st.session_state.pop(k, None)
                st.rerun()
        else:
            for group_label, group_df in resolve_groups(v_filtered, v_group):
                if group_label is not None:
                    st.markdown(
                        f'<div class="section-heading">📁 {group_label} '
                        f'<span style="font-size:0.8rem;color:var(--text-muted);font-weight:500;">({len(group_df)})</span></div>',
                        unsafe_allow_html=True,
                    )
                for idx, row in group_df.iterrows():
                    name = row.get('Place Name', 'Unknown')
                    cat  = row.get('Category', '')
                    with st.expander(f"✅  {name}  —  {cat}"):
                        d1, d2 = st.columns([2, 1])
                        with d1:
                            st.markdown(f"**🏙️ City:** {row.get('City') or 'N/A'}")
                            st.markdown(f"**📍 Location:** {row.get('Area/Location') or 'N/A'}")
                            if row.get('Date Visited'):
                                dv = row['Date Visited']
                                date_str = dv.strftime("%d %b %Y") if hasattr(dv, 'strftime') else str(dv)
                                st.markdown(f"**📅 Date Visited:** {date_str}")
                            cost_val = row.get('Estimated Cost', 0)
                            cost_str = f"₹{float(cost_val):,.0f}" if cost_val and float(cost_val) > 0 else "Free / Unknown"
                            st.markdown(f"**💰 Total Cost:** {cost_str}")
                            st.markdown(f"**🤔 Revisit Worthy:** {row.get('Revisit Worthy') or 'N/A'}")

                        with d2:
                            r_aman = row.get('Rating (Aman)', 0)
                            if r_aman and float(r_aman) > 0:
                                st.markdown(f"**Aman's Rating:** {star_rating(r_aman)} ({float(r_aman):.1f})")
                            else:
                                st.markdown("**Aman's Rating:** *Not rated yet*")
                            r_sandra = row.get('Rating (Sandra)', 0)
                            if r_sandra and float(r_sandra) > 0:
                                st.markdown(f"**Sandra's Rating:** {star_rating(r_sandra)} ({float(r_sandra):.1f})")
                            else:
                                st.markdown("**Sandra's Rating:** *Not rated yet*")
                            st.markdown(f"**🥰 Memory:** {row.get('Memory') or 'N/A'}")

                        render_nearby(all_df, row)


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:2.5rem 0 1.5rem;
            color:#B5AFB8; font-size:0.8rem; font-family:'Inter',sans-serif;
            border-top: 1px solid rgba(45,42,50,0.08); margin-top:2rem;">
  ✈️ &nbsp; Made with ❤️ for Aman &amp; Sandra
</div>
""", unsafe_allow_html=True)