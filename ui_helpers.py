import pandas as pd
import streamlit as st

from sheets_data import haversine_km


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
