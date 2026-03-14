import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials
import hmac
import re

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
  @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Inter:wght@300;400;500;600&display=swap');

  /* ── DARK TRAVEL THEME TOKENS ── */
  :root {
    --bg:          #0D1117;
    --bg2:         #151C26;
    --bg3:         #1C2535;
    --card:        #1C2535;
    --card-hover:  #232D40;
    --border:      rgba(255,255,255,0.08);
    --border-glow: rgba(232,172,80,0.35);
    --gold:        #E8AC50;
    --gold-light:  #F5CC7A;
    --teal:        #4ECDC4;
    --coral:       #FF6B6B;
    --text:        #E8EDF5;
    --text-muted:  #7A8BA0;
    --radius:      12px;
    --shadow:      0 4px 24px rgba(0,0,0,0.4);
  }

  /* ── Force dark background everywhere ── */
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
    font-family: 'Cormorant Garamond', serif !important;
  }
  strong, b { color: var(--text) !important; }
  .stMarkdown a { color: var(--gold) !important; }

  /* ── Metric cards (main area) ── */
  [data-testid="stMain"] [data-testid="metric-container"],
  .main [data-testid="metric-container"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 1.1rem 1.4rem !important;
    box-shadow: var(--shadow) !important;
  }
  [data-testid="stMain"] [data-testid="stMetricValue"] {
    color: var(--gold) !important;
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 2.2rem !important;
    font-weight: 600 !important;
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
    box-shadow: 0 8px 32px rgba(0,0,0,0.5);
  }
  .card-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.1rem;
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
    font-weight: 600;
    letter-spacing: 0.04em;
    margin-right: 0.3rem;
  }
  .tag-activity { background: rgba(78,205,196,0.15); color: #4ECDC4 !important; border: 1px solid rgba(78,205,196,0.3); }
  .tag-city     { background: rgba(232,172,80,0.15);  color: #E8AC50 !important; border: 1px solid rgba(232,172,80,0.3); }
  .tag-cafe     { background: rgba(255,107,107,0.15); color: #FF6B6B !important; border: 1px solid rgba(255,107,107,0.3); }
  .tag-drive    { background: rgba(130,200,130,0.15); color: #82C882 !important; border: 1px solid rgba(130,200,130,0.3); }
  .tag-default  { background: rgba(180,150,220,0.15); color: #C196E0 !important; border: 1px solid rgba(180,150,220,0.3); }

  /* ── Section headings ── */
  .section-heading {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 1.35rem !important;
    font-weight: 600 !important;
    color: var(--text) !important;
    margin: 1.5rem 0 0.8rem !important;
    letter-spacing: 0.01em;
    border-left: 3px solid var(--gold);
    padding-left: 0.75rem;
  }

  /* ── Expanders ── */
  [data-testid="stExpander"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    margin-bottom: 0.55rem !important;
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
    border-radius: 9px !important;
    color: var(--text) !important;
    font-family: 'Inter', sans-serif !important;
  }
  .stTextInput > div > div > input::placeholder,
  .stTextArea > div > textarea::placeholder {
    color: var(--text-muted) !important;
  }
  .stTextInput > div > div > input:focus,
  .stTextArea > div > textarea:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 2px rgba(232,172,80,0.2) !important;
  }
  /* selectbox */
  [data-testid="stSelectbox"] > div > div,
  [data-baseweb="select"] > div {
    background: var(--bg3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 9px !important;
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
    background: var(--gold) !important;
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
    border-radius: 9px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    transition: all 0.18s ease !important;
  }
  [data-testid="stMain"] .stButton > button:hover,
  [data-testid="stMainBlockContainer"] .stButton > button:hover {
    background: rgba(232,172,80,0.12) !important;
    border-color: var(--border-glow) !important;
    color: var(--gold) !important;
  }

  /* ── Link buttons ── */
  [data-testid="stLinkButton"] a {
    background: var(--bg3) !important;
    color: var(--teal) !important;
    border: 1px solid rgba(78,205,196,0.3) !important;
    border-radius: 9px !important;
    font-family: 'Inter', sans-serif !important;
  }
  [data-testid="stLinkButton"] a:hover {
    background: rgba(78,205,196,0.12) !important;
  }

  /* ── Form submit ── */
  .stFormSubmitButton > button {
    background: linear-gradient(135deg, #E8AC50, #D4922A) !important;
    color: #0D1117 !important;
    border: none !important;
    border-radius: 9px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    height: 3em !important;
  }
  .stFormSubmitButton > button:hover {
    background: linear-gradient(135deg, #F5CC7A, #E8AC50) !important;
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
    background: linear-gradient(90deg, var(--teal), var(--gold));
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
  .stat-badge strong { color: var(--gold) !important; }

  /* ── Dividers ── */
  hr { border-color: var(--border) !important; margin: 1.5rem 0 !important; }
  [data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--bg) !important;
  }

  /* ── Checkbox ── */
  [data-testid="stCheckbox"] label span { color: var(--text) !important; }

  /* ── Page header ── */
  .page-header {
    background: linear-gradient(135deg, #131E35 0%, #1A2840 50%, #0F2020 100%);
    border: 1px solid var(--border);
    border-top: 2px solid var(--gold);
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
    background: radial-gradient(circle, rgba(232,172,80,0.08) 0%, transparent 70%);
  }
  .page-header h1 {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 2.2rem !important;
    font-weight: 600 !important;
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
    border-radius: 16px;
    padding: 2.5rem;
    box-shadow: 0 8px 48px rgba(0,0,0,0.5);
  }
    .page-header h1 { font-size: 1.6rem !important; }
    .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
  }

  /* ── Top Navbar ── */
  .topnav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #0A0F18;
    border: 1px solid rgba(255,255,255,0.08);
    border-top: 2px solid #E8AC50;
    border-radius: 12px;
    padding: 0.75rem 1.5rem;
    margin-bottom: 0.5rem;
  }
  .topnav-left {
    display: flex;
    align-items: center;
    gap: 0.6rem;
  }
  .topnav-logo {
    font-size: 1.5rem;
    filter: drop-shadow(0 0 8px rgba(232,172,80,0.6));
  }
  .topnav-brand {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 1.2rem;
    font-weight: 600;
    color: #E8EDF5 !important;
    letter-spacing: 0.02em;
  }
  .topnav-right {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  .topnav-user {
    color: #E8EDF5 !important;
    font-size: 0.83rem;
    font-weight: 500;
  }
  .topnav-stat {
    color: #7A8BA0 !important;
    font-size: 0.8rem;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 0.2rem 0.7rem;
  }

  /* ── Nav buttons row ── */
  .nav-btn button,
  .nav-btn-active button {
    border-radius: 9px !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    font-family: 'Inter', sans-serif !important;
    height: auto !important;
    padding: 0.5rem 0.75rem !important;
    transition: all 0.18s ease !important;
    width: 100% !important;
  }
  .nav-btn button {
    background: rgba(255,255,255,0.04) !important;
    color: #7A8BA0 !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
  }
  .nav-btn button:hover {
    background: rgba(232,172,80,0.1) !important;
    color: #E8AC50 !important;
    border-color: rgba(232,172,80,0.3) !important;
  }
  .nav-btn-active button {
    background: rgba(232,172,80,0.15) !important;
    color: #E8AC50 !important;
    border: 1px solid rgba(232,172,80,0.4) !important;
  }

  /* Refresh + Logout buttons */
  .nav-divider {
    height: 1px;
    background: rgba(255,255,255,0.06);
    margin: 0.5rem 0 1.5rem;
  }

  /* ── Mobile: stack nav ── */
  @media (max-width: 768px) {
    .topnav { flex-direction: column; gap: 0.5rem; padding: 1rem; }
    .topnav-right { flex-wrap: wrap; justify-content: center; }
    .page-header { padding: 1.3rem 1.5rem; }
    .page-header h1 { font-size: 1.6rem !important; }
    .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
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


# ── Auth ─────────────────────────────────────────────────────────────────────
def check_password():
    def login_form():
        col_l, col_m, col_r = st.columns([1, 2, 1])
        with col_m:
            st.markdown("""
            <div style="text-align:center; padding: 2.5rem 0 1.5rem;">
              <div style="font-size:4rem; margin-bottom:0.6rem;
                          filter: drop-shadow(0 0 20px rgba(232,172,80,0.4));">✈️</div>
              <div style="font-family:'Cormorant Garamond',serif; font-size:2rem;
                          font-weight:600; color:#E8EDF5; margin-bottom:0.3rem;
                          letter-spacing:0.02em;">
                Travel Planner
              </div>
              <div style="color:#7A8BA0; font-size:0.9rem; margin-bottom:2rem;
                          letter-spacing:0.05em; text-transform:uppercase; font-size:0.75rem;">
                Your personal adventure tracker
              </div>
            </div>
            """, unsafe_allow_html=True)

            with st.form("Credentials"):
                st.text_input("👤  Username", key="username", placeholder="Enter username")
                st.text_input("🔑  Password", type="password", key="password",
                              placeholder="Enter password")
                st.form_submit_button("Sign In →", on_click=password_entered,
                                      use_container_width=True)

    def password_entered():
        if st.session_state["username"] in st.secrets["passwords"] and hmac.compare_digest(
            st.session_state["password"],
            st.secrets["passwords"][st.session_state["username"]],
        ):
            st.session_state["password_correct"] = True
            st.session_state["logged_in_user"] = st.session_state["username"]
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    login_form()
    if "password_correct" in st.session_state:
        st.error("😕 Incorrect username or password — please try again.")
    return False


# ── Data loading ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_travel_data():
    try:
        if "gsheets" not in st.secrets:
            st.error("Google Sheets credentials not found in secrets")
            return pd.DataFrame(), pd.DataFrame()

        scopes = ['https://www.googleapis.com/auth/spreadsheets',
                  'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(st.secrets["gsheets"], scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open("Our Travel List")

        to_visit_data = sh.worksheet("To Visit").get_all_records()
        visited_data  = sh.worksheet("Visited").get_all_records()

        to_visit_df = pd.DataFrame(to_visit_data) if to_visit_data else pd.DataFrame()
        visited_df  = pd.DataFrame(visited_data)  if visited_data  else pd.DataFrame()

        to_visit_df = clean_dataframe(to_visit_df, sheet_type="to_visit")
        visited_df  = clean_dataframe(visited_df,  sheet_type="visited")

        return to_visit_df, visited_df

    except gspread.exceptions.SpreadsheetNotFound:
        st.error("Spreadsheet 'Our Travel List' not found.")
        return pd.DataFrame(), pd.DataFrame()
    except gspread.exceptions.WorksheetNotFound:
        st.error("Required worksheets ('To Visit' or 'Visited') not found.")
        return pd.DataFrame(), pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()


def clean_dataframe(df, sheet_type="to_visit"):
    if df.empty:
        return df
    df = df.dropna(how='all')
    df.columns = [str(col).strip() for col in df.columns]
    column_mapping = {
        'Place Name': 'Place Name', 'PlaceName': 'Place Name', 'placename': 'Place Name',
        'Category': 'Category', 'City': 'City',
        'Area / Location': 'Area/Location', 'Area/Location': 'Area/Location', 'Area': 'Area/Location',
        'Country': 'Country',
        'Estimated Cost': 'Estimated Cost', 'EstimatedCost': 'Estimated Cost', 'Cost': 'Estimated Cost',
        'Distance(kms)': 'Distance(kms)', 'Distance': 'Distance(kms)',
        'Best Time to Visit': 'Best Time to Visit', 'BestTime': 'Best Time to Visit',
        'Ideal For': 'Ideal For', 'IdealFor': 'Ideal For',
        'Added By': 'Added By', 'AddedBy': 'Added By',
        'Google Maps Link': 'Google Maps Link', 'Maps Link': 'Google Maps Link',
        'Google Rating': 'Google Rating', 'Rating': 'Google Rating',
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
        if 'Date Visited'    in df.columns: df['Date Visited']    = pd.to_datetime(df['Date Visited'],    errors='coerce').dt.date
        if 'Rating (Aman)'   in df.columns: df['Rating (Aman)']   = df['Rating (Aman)'].apply(parse_rating)
        if 'Rating (Sandra)' in df.columns: df['Rating (Sandra)'] = df['Rating (Sandra)'].apply(parse_rating)
        if 'Notes'           in df.columns: df['Notes']           = df['Notes'].apply(lambda x: str(x).strip() if pd.notna(x) else '')
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
            except: pass
        try: return float(cost)
        except: return 0
    return 0


def parse_distance(distance):
    if pd.isna(distance) or distance == '': return 0
    if isinstance(distance, (int, float)): return float(distance)
    if isinstance(distance, str):
        distance = re.sub(r'[km\s]', '', distance.lower())
        try: return float(distance)
        except: return 0
    return 0


def parse_rating(rating):
    if pd.isna(rating) or rating == '': return 0.0
    if isinstance(rating, (int, float)): return min(float(rating), 5.0)
    if isinstance(rating, str):
        numbers = re.findall(r"[\d.]+", rating)
        if numbers:
            try: return min(float(numbers[0]), 5.0)
            except: pass
    return 0.0


def update_google_sheet(sheet_name, data):
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets',
                  'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(st.secrets["gsheets"], scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open("Our Travel List")
        worksheet = sh.worksheet(sheet_name)
        worksheet.batch_clear(['A2:ZZ'])
        if not data.empty:
            headers = data.columns.tolist()
            values  = data.values.tolist()
            worksheet.update([headers] + values)
        return True
    except Exception as e:
        st.error(f"Error updating Google Sheets: {str(e)}")
        return False


# ── Gate ─────────────────────────────────────────────────────────────────────
if not check_password():
    st.stop()

# ── Load data ─────────────────────────────────────────────────────────────────
to_visit_df, visited_df = load_travel_data()

# ── Session state defaults ────────────────────────────────────────────────────
if 'current_view' not in st.session_state:
    st.session_state.current_view = "dashboard"


# ── Top Navbar ───────────────────────────────────────────────────────────────
logged_user = st.session_state.get("logged_in_user", "Traveler")
to_visit_cnt_nav = len(to_visit_df) if not to_visit_df.empty else 0
visited_cnt_nav  = len(visited_df)  if not visited_df.empty  else 0

nav_items = [
    ("dashboard",  "🏠", "Dashboard"),
    ("to_visit",   "📍", "To Visit"),
    ("visited",    "✅", "Visited"),
    ("statistics", "📊", "Statistics"),
]

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
nav_cols = st.columns([1, 1, 1, 1, 0.6, 0.6])

nav_map = [
    ("dashboard",  "🏠 Dashboard"),
    ("to_visit",   "📍 To Visit"),
    ("visited",    "✅ Visited"),
    ("statistics", "📊 Statistics"),
]
for i, (key, label) in enumerate(nav_map):
    with nav_cols[i]:
        is_active = (active == key)
        btn_style = "nav-btn-active" if is_active else "nav-btn"
        st.markdown(f'<div class="{btn_style}">', unsafe_allow_html=True)
        if st.button(label, key=f"nav_{key}", use_container_width=True):
            st.session_state.current_view = key
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

with nav_cols[4]:
    if st.button("🔄 Refresh", use_container_width=True, key="refresh_btn"):
        st.cache_data.clear()
        st.rerun()

with nav_cols[5]:
    if st.button("🚪 Logout", use_container_width=True, key="logout_btn"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

st.markdown('<div class="nav-divider"></div>', unsafe_allow_html=True)


# ── Views ─────────────────────────────────────────────────────────────────────
view = st.session_state.current_view

# ════════════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════════════
if view == "dashboard":
    st.markdown("""
    <div class="page-header">
      <h1>🏠 Travel Dashboard</h1>
      <p>Track every adventure — places dreamed of and memories made.</p>
    </div>
    """, unsafe_allow_html=True)

    if to_visit_df.empty and visited_df.empty:
        st.warning("No travel data found. Check your Google Sheets connection.")
    else:
        total_places  = len(to_visit_df) + len(visited_df)
        visited_count = len(visited_df)
        progress_pct  = (visited_count / total_places * 100) if total_places > 0 else 0

        all_df         = pd.concat([to_visit_df, visited_df], ignore_index=True)
        unique_cities  = all_df['City'].nunique()      if 'City' in all_df.columns     else 0
        unique_cats    = all_df['Category'].nunique()  if 'Category' in all_df.columns else 0

        # Metric row
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📌 Total Places", total_places)
        c2.metric("✅ Visited",       visited_count)
        c3.metric("🏙️ Cities",        unique_cities)
        c4.metric("🗂️ Categories",    unique_cats)

        # Progress bar
        st.markdown(f"""
        <div style="margin: 1.5rem 0 0.5rem;">
          <div style="display:flex; justify-content:space-between;
                      font-size:0.82rem; color:#7A8BA0; margin-bottom:0.4rem;">
            <span>Adventure Progress</span>
            <span><strong style="color:#E8AC50;">{progress_pct:.1f}%</strong> explored</span>
          </div>
          <div class="progress-wrap">
            <div class="progress-fill" style="width:{progress_pct:.1f}%;"></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown('<div class="section-heading">🆕 Recently Added</div>', unsafe_allow_html=True)
            if not to_visit_df.empty:
                for _, row in to_visit_df.head(5).iterrows():
                    name = row.get('Place Name', 'Unknown')
                    city = row.get('City', '')
                    cat  = row.get('Category', '')
                    st.markdown(f"""
                    <div class="travel-card">
                      <div class="card-title">{name}</div>
                      <div class="card-meta">
                        {'📍 ' + city if city else ''}&nbsp;&nbsp;
                        {category_tag(cat)}
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No places in your 'To Visit' list yet!")

        with col2:
            st.markdown('<div class="section-heading">📊 Top Cities to Visit</div>', unsafe_allow_html=True)
            if not to_visit_df.empty and 'City' in to_visit_df.columns:
                city_counts = to_visit_df['City'].value_counts().head(6)
                if not city_counts.empty:
                    fig = px.bar(
                        x=city_counts.values, y=city_counts.index,
                        orientation='h',
                        labels={'x': 'Places', 'y': ''},
                        color=city_counts.values,
                        color_continuous_scale=["#2A3F5F", "#E8AC50"],
                    )
                    fig.update_layout(
                        showlegend=False,
                        coloraxis_showscale=False,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=0, r=0, t=10, b=0),
                        height=280,
                        yaxis=dict(tickfont=dict(family='Inter', size=12, color='#7A8BA0'), gridcolor='rgba(255,255,255,0.05)'),
                        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='#7A8BA0')),
                    )
                    fig.update_traces(marker_line_width=0)
                    st.plotly_chart(fig, use_container_width=True)


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
        # Filters
        with st.container():
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                categories     = ['All'] + sorted(to_visit_df['Category'].dropna().unique().tolist())
                category_filter = st.selectbox("🗂️ Category", categories)
            with fc2:
                cities      = ['All'] + sorted(to_visit_df['City'].dropna().unique().tolist())
                city_filter = st.selectbox("🏙️ City", cities)
            with fc3:
                if 'Distance(kms)' in to_visit_df.columns:
                    max_d = int(to_visit_df['Distance(kms)'].max()) if not to_visit_df['Distance(kms)'].isna().all() else 500
                    max_dist = st.slider("📏 Max Distance (km)", 0, max(max_d, 1), min(50, max_d))

        # Apply filters
        filtered_df = to_visit_df.copy()
        if category_filter != 'All':
            filtered_df = filtered_df[filtered_df['Category'] == category_filter]
        if city_filter != 'All':
            filtered_df = filtered_df[filtered_df['City'] == city_filter]
        if 'Distance(kms)' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Distance(kms)'] <= max_dist]

        st.markdown(f"""
        <div class="stat-badge" style="margin:0.75rem 0 1rem;">
          📋 &nbsp;<strong>{len(filtered_df)}</strong> places shown
        </div>
        """, unsafe_allow_html=True)

        for idx, row in filtered_df.iterrows():
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

                    if row.get('Added By'):
                        st.markdown(f"**🙋 Added By:** {row['Added By']}")

                    if row.get('Best Time to Visit'):
                        st.markdown(f"**🗓️ Best Time:** {row['Best Time to Visit']}")

                with d2:
                    g_rating = row.get('Google Rating', 0)
                    if g_rating and float(g_rating) > 0:
                        st.markdown(f"**⭐ Google Rating:** {star_rating(g_rating)} ({float(g_rating):.1f})")

                    maps_link = row.get('Google Maps Link', '')
                    if maps_link and str(maps_link).startswith(('http://', 'https://')):
                        st.link_button("🗺️ View on Maps", maps_link)

                    if st.button("✅ Mark as Visited", key=f"visit_{idx}"):
                        st.success(f"Marked **{name}** as visited!")
                        st.info("This will update Google Sheets in the full implementation.")


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
        st.markdown(f"""
        <div class="stat-badge" style="margin-bottom:1rem;">
          🗺️ &nbsp;<strong>{len(visited_df)}</strong> adventures completed
        </div>
        """, unsafe_allow_html=True)

        for idx, row in visited_df.iterrows():
            name = row.get('Place Name', 'Unknown')
            cat  = row.get('Category', '')
            with st.expander(f"✅  {name}  —  {cat}"):
                d1, d2 = st.columns([2, 1])
                with d1:
                    st.markdown(f"**🗂️ Category:** {cat or 'N/A'}")
                    st.markdown(f"**🏙️ City:** {row.get('City', 'N/A')}")
                    if row.get('Date Visited'):
                        st.markdown(f"**📅 Date Visited:** {row['Date Visited']}")
                    if row.get('Notes'):
                        st.markdown(f"**📝 Notes:** {row['Notes']}")

                with d2:
                    r_aman = row.get('Rating (Aman)', 0)
                    if r_aman and float(r_aman) > 0:
                        st.markdown(f"**Aman's Rating:** {star_rating(r_aman)} ({float(r_aman):.1f})")
                    r_sandra = row.get('Rating (Sandra)', 0)
                    if r_sandra and float(r_sandra) > 0:
                        st.markdown(f"**Sandra's Rating:** {star_rating(r_sandra)} ({float(r_sandra):.1f})")


# ════════════════════════════════════════════════════════════
# STATISTICS
# ════════════════════════════════════════════════════════════
elif view == "statistics":
    st.markdown("""
    <div class="page-header">
      <h1>📊 Travel Statistics</h1>
      <p>Numbers that tell your story — how far you've come and where you're headed.</p>
    </div>
    """, unsafe_allow_html=True)

    all_places = pd.concat([to_visit_df, visited_df], ignore_index=True)

    if all_places.empty:
        st.warning("No data available for statistics yet.")
    else:
        total         = len(all_places)
        visited_count = len(visited_df)
        to_visit_cnt  = len(to_visit_df)
        progress_pct  = (visited_count / total * 100) if total > 0 else 0

        # ── KPI row ──────────────────────────────
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("🗺️ Total Places",    total)
        k2.metric("✅ Visited",          visited_count)
        k3.metric("📍 To Visit",         to_visit_cnt)
        if 'Estimated Cost' in all_places.columns:
            total_cost = all_places['Estimated Cost'].sum()
            k4.metric("💰 Est. Budget",   f"₹{total_cost:,.0f}")
        else:
            k4.metric("💰 Est. Budget",   "N/A")

        # ── Progress gauge + breakdown ────────────
        st.markdown("---")
        g1, g2 = st.columns([1, 1])

        with g1:
            st.markdown('<div class="section-heading">🎯 Journey Progress</div>', unsafe_allow_html=True)
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=progress_pct,
                number={"suffix": "%", "font": {"family": "Cormorant Garamond", "size": 36, "color": "#E8AC50"}},
                delta={"reference": 50, "position": "bottom"},
                title={"text": "Places Explored", "font": {"family": "Inter", "size": 13, "color": "#7A8BA0"}},
                domain={"x": [0, 1], "y": [0, 1]},
                gauge={
                    "axis":  {"range": [0, 100], "tickwidth": 1, "tickcolor": "#7A8BA0", "tickfont": {"color": "#7A8BA0"}},
                    "bar":   {"color": "#E8AC50", "thickness": 0.25},
                    "bgcolor": "rgba(0,0,0,0)",
                    "borderwidth": 0,
                    "steps": [
                        {"range": [0, 33],  "color": "rgba(255,255,255,0.04)"},
                        {"range": [33, 66], "color": "rgba(255,255,255,0.07)"},
                        {"range": [66, 100],"color": "rgba(255,255,255,0.10)"},
                    ],
                    "threshold": {
                        "line":      {"color": "#FF6B6B", "width": 3},
                        "thickness": 0.75,
                        "value":     90,
                    },
                }
            ))
            fig_gauge.update_layout(
                height=280,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#E8EDF5",
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

        with g2:
            st.markdown('<div class="section-heading">🍩 Visited vs. To Visit</div>', unsafe_allow_html=True)
            donut_fig = go.Figure(go.Pie(
                labels=["Visited", "To Visit"],
                values=[visited_count, to_visit_cnt],
                hole=0.62,
                marker=dict(colors=["#E8AC50", "#1C2535"], line=dict(color="#0D1117", width=2)),
                textinfo="percent+label",
                textfont=dict(family="Inter", size=12, color="#E8EDF5"),
            ))
            donut_fig.update_layout(
                height=280,
                showlegend=False,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                annotations=[dict(
                    text=f"<b>{progress_pct:.0f}%</b>",
                    x=0.5, y=0.5, font_size=22,
                    font_family="Cormorant Garamond",
                    font_color="#E8AC50",
                    showarrow=False
                )],
            )
            st.plotly_chart(donut_fig, use_container_width=True)

        # ── Category + City ────────────────────────
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
                    color_continuous_scale=["#1C3A5E", "#E8AC50"],
                    labels={'Total': 'Places', 'Category': ''},
                )
                fig_cat.update_layout(
                    showlegend=False,
                    coloraxis_showscale=False,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=0, r=0, t=10, b=0),
                    height=280,
                    xaxis=dict(tickangle=-20, tickfont=dict(family='Inter', size=11, color='#7A8BA0'), gridcolor='rgba(255,255,255,0.05)'),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='#7A8BA0')),
                )
                fig_cat.update_traces(marker_line_width=0)
                st.plotly_chart(fig_cat, use_container_width=True)

        with cc2:
            if 'City' in all_places.columns:
                city_data = all_places['City'].value_counts().head(8).reset_index()
                city_data.columns = ['City', 'Count']

                fig_city = px.bar(
                    city_data, x='Count', y='City',
                    orientation='h',
                    color='Count',
                    color_continuous_scale=["#1A3A3A", "#4ECDC4"],
                    labels={'Count': 'Places', 'City': ''},
                )
                fig_city.update_layout(
                    showlegend=False,
                    coloraxis_showscale=False,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=0, r=0, t=10, b=0),
                    height=280,
                    yaxis=dict(tickfont=dict(family='Inter', size=11, color='#7A8BA0')),
                    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='#7A8BA0')),
                )
                fig_city.update_traces(marker_line_width=0)
                st.plotly_chart(fig_city, use_container_width=True)

        # ── Cost distribution ──────────────────────
        if 'Estimated Cost' in all_places.columns:
            cost_data = all_places[all_places['Estimated Cost'] > 0]['Estimated Cost']
            if not cost_data.empty:
                st.markdown("---")
                st.markdown('<div class="section-heading">💰 Cost Distribution</div>', unsafe_allow_html=True)

                fig_hist = px.histogram(
                    cost_data, nbins=25,
                    labels={'value': 'Estimated Cost (₹)', 'count': 'Places'},
                    color_discrete_sequence=["#4ECDC4"],
                )
                fig_hist.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=0, r=0, t=10, b=0),
                    height=260,
                    bargap=0.1,
                    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='#7A8BA0')),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='#7A8BA0')),
                )
                st.plotly_chart(fig_hist, use_container_width=True)

        # ── Visited: ratings over time ─────────────
        if not visited_df.empty and 'Rating (Aman)' in visited_df.columns and 'Date Visited' in visited_df.columns:
            dated = visited_df[visited_df['Date Visited'].notna()].sort_values('Date Visited')
            if not dated.empty:
                st.markdown("---")
                st.markdown('<div class="section-heading">⭐ Ratings Over Time</div>', unsafe_allow_html=True)

                fig_line = go.Figure()
                if 'Rating (Aman)' in dated.columns:
                    fig_line.add_trace(go.Scatter(
                        x=dated['Date Visited'], y=dated['Rating (Aman)'],
                        mode='lines+markers', name="Aman",
                        line=dict(color="#E8AC50", width=2),
                        marker=dict(size=7),
                    ))
                if 'Rating (Sandra)' in dated.columns:
                    fig_line.add_trace(go.Scatter(
                        x=dated['Date Visited'], y=dated['Rating (Sandra)'],
                        mode='lines+markers', name="Sandra",
                        line=dict(color="#4ECDC4", width=2),
                        marker=dict(size=7),
                    ))
                fig_line.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    legend=dict(font=dict(family='Inter', size=12, color='#E8EDF5'), bgcolor='rgba(0,0,0,0)'),
                    margin=dict(l=0, r=0, t=10, b=0),
                    height=260,
                    yaxis=dict(range=[0, 5.5], showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='#7A8BA0')),
                    xaxis=dict(showgrid=False, tickfont=dict(color='#7A8BA0')),
                )
                st.plotly_chart(fig_line, use_container_width=True)


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:2.5rem 0 1.5rem;
            color:#3A4A60; font-size:0.8rem; font-family:'Inter',sans-serif;
            border-top: 1px solid rgba(255,255,255,0.06); margin-top:2rem;">
  ✈️ &nbsp; Made with ❤️ for Aman &amp; Sandra
</div>
""", unsafe_allow_html=True)