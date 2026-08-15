import re
import time
from math import radians, sin, cos, asin, sqrt
from urllib.parse import unquote_plus

import gspread
import pandas as pd
import requests
import streamlit as st

# ── Constants ────────────────────────────────────────────────────────────────
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
]
SPREADSHEET_NAME = "Our Travel List"


# ── Google Sheets client (cached for the app session) ────────────────────────
@st.cache_resource
def get_gspread_client():
    return gspread.service_account_from_dict(st.secrets["gsheets"], scopes=SCOPES)


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


# ── Home locations (private — configured in .streamlit/secrets.toml, never in code) ──
def get_home_locations():
    """{'Aman': (lat, lng), 'Sandra': (lat, lng)} for whichever homes are configured.
    Returns an empty dict if the [home] section is absent — the feature simply no-ops."""
    cfg = st.secrets.get("home", {})
    homes = {}
    if cfg.get("aman_lat") and cfg.get("aman_lng"):
        homes["Aman"] = (float(cfg["aman_lat"]), float(cfg["aman_lng"]))
    if cfg.get("sandra_lat") and cfg.get("sandra_lng"):
        homes["Sandra"] = (float(cfg["sandra_lat"]), float(cfg["sandra_lng"]))
    return homes


def enrich_home_distance(df, homes):
    """Adds a 'Distance <Name> (km)' column per configured home, plus a unified 'Distance (km)'
    (mean of whichever homes are configured), falling back per-row to the sheet's manually-typed
    'Distance(kms)' when a place has no resolved coordinates."""
    if df.empty:
        return df
    if homes:
        for name, (hlat, hlng) in homes.items():
            df[f"Distance {name} (km)"] = df.apply(
                lambda r: haversine_km(hlat, hlng, r['Latitude'], r['Longitude'])
                if pd.notna(r.get('Latitude')) and pd.notna(r.get('Longitude')) else float('nan'),
                axis=1,
            )
        computed = df[[f"Distance {name} (km)" for name in homes]].mean(axis=1, skipna=True)
    else:
        computed = pd.Series(float('nan'), index=df.index)
    manual = df['Distance(kms)'] if 'Distance(kms)' in df.columns else pd.Series(float('nan'), index=df.index)
    df['Distance (km)'] = computed.where(computed.notna(), manual)
    return df


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

        homes = get_home_locations()
        to_visit_df = enrich_home_distance(to_visit_df, homes)
        visited_df  = enrich_home_distance(visited_df, homes)

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


# ── Write-back (targeted, additive/surgical — never a full-sheet rewrite) ────
def _append_row_by_headers(ws, data):
    """Appends one row built from a dict, ordered to match the worksheet's actual current
    headers (so it's resilient to column reordering and never depends on our in-app schema)."""
    headers = ws.row_values(1)
    row = [_serialize(data.get(h, '')) for h in headers]
    ws.append_row(row, value_input_option="USER_ENTERED")


def add_to_visit_place(data):
    """data: dict keyed by the To Visit sheet's column names. Purely additive — appends one
    row, never touches existing rows. Returns (success, error_message)."""
    try:
        gc = get_gspread_client()
        sh = gc.open(SPREADSHEET_NAME)
        _append_row_by_headers(sh.worksheet("To Visit"), data)
        return True, None
    except Exception as e:
        return False, str(e)


def _find_row_numbers(ws, place_name, city, area):
    """1-indexed row numbers (matching the live sheet right now) whose Place Name/City/
    Area-or-Location match. Re-fetches fresh rather than trusting the cached dataframe,
    since row position must be exact before a delete."""
    headers = ws.row_values(1)
    area_key = 'Area / Location' if 'Area / Location' in headers else ('Location' if 'Location' in headers else None)
    matches = []
    for i, rec in enumerate(ws.get_all_records(), start=2):
        if (str(rec.get('Place Name', '')).strip() == place_name and
                str(rec.get('City', '')).strip() == city and
                (area_key is None or str(rec.get(area_key, '')).strip() == area)):
            matches.append(i)
    return matches


def mark_place_visited(place_row, visit_details):
    """place_row: a row (dict-like) from the cleaned To Visit dataframe.
    visit_details: {'date_visited', 'total_cost', 'added_by', 'rating_aman', 'rating_sandra',
    'memory', 'revisit_worthy'} — total_cost/added_by are user-editable in the form, defaulting
    to the To Visit row's values but not required to match them.
    Appends to Visited, then deletes the matching row from To Visit only if exactly one match
    is found in the live sheet — otherwise leaves To Visit untouched and returns a warning
    asking you to remove it by hand, rather than risk deleting the wrong row.
    Returns (success, warning_message_or_None)."""
    try:
        gc = get_gspread_client()
        sh = gc.open(SPREADSHEET_NAME)
        visited_ws  = sh.worksheet("Visited")
        to_visit_ws = sh.worksheet("To Visit")

        place_name = place_row.get('Place Name', '')
        city       = place_row.get('City', '')
        area       = place_row.get('Area/Location', '')

        data = {
            'Place Name': place_name,
            'Category': place_row.get('Category', ''),
            'City': city,
            'Location': area,
            'Country': place_row.get('Country', ''),
            'Total Cost': visit_details.get('total_cost', place_row.get('Estimated Cost', '')),
            'Distance': place_row.get('Distance(kms)', ''),
            'Date Visited': visit_details['date_visited'],
            'Rating (Aman)': visit_details['rating_aman'],
            'Rating (Sandra)': visit_details['rating_sandra'],
            'Added By': visit_details.get('added_by') or place_row.get('Added By', ''),
            'Google Maps Link': place_row.get('Google Maps Link', ''),
            'Memory': visit_details['memory'],
            'Revisit Worthy': visit_details['revisit_worthy'],
        }
        _append_row_by_headers(visited_ws, data)

        matches = _find_row_numbers(to_visit_ws, place_name, city, area)
        if len(matches) == 1:
            to_visit_ws.delete_rows(matches[0])
            return True, None
        if len(matches) == 0:
            return True, "Added to Visited, but couldn't find the matching row in To Visit to remove — please delete it by hand."
        return True, f"Added to Visited, but found {len(matches)} matching rows in To Visit — please delete the right one by hand to avoid removing the wrong place."
    except Exception as e:
        return False, str(e)
