from datetime import date

import streamlit as st

from sheets_data import add_to_visit_place, mark_place_visited, load_travel_data
from ui_helpers import apply_text_search, resolve_groups, star_rating, render_nearby


def _render_add_place_form(to_visit_df, logged_user):
    with st.expander("➕ Add a Place"):
        with st.form("add_place_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                new_name = st.text_input("Place Name*")
                existing_cats = sorted(to_visit_df['Category'].dropna().unique().tolist()) if 'Category' in to_visit_df.columns else []
                cat_choice = st.selectbox("Category", existing_cats + ["Other"])
                new_cat = st.text_input("Custom category") if cat_choice == "Other" else cat_choice
                new_city = st.text_input("City*")
                new_area = st.text_input("Area / Location")
                new_country = st.text_input("Country", value="India")
            with c2:
                new_cost = st.number_input("Estimated Cost (₹)", min_value=0, value=0, step=100)
                new_best_time = st.text_input("Best Time to Visit", value="Anytime")
                new_ideal_for = st.text_input("Ideal For")
                new_link = st.text_input("Google Maps Link")
                new_rating = st.slider("Google Rating", 0.0, 5.0, 0.0, 0.1)

            submitted = st.form_submit_button("Add Place")
            if submitted:
                if not new_name or not new_city:
                    st.error("Place Name and City are required.")
                else:
                    data = {
                        'Place Name': new_name,
                        'Category': new_cat,
                        'City': new_city,
                        'Area / Location': new_area,
                        'Country': new_country,
                        'Estimated Cost': new_cost,
                        'Best Time to Visit': new_best_time,
                        'Ideal For': new_ideal_for,
                        'Added By': logged_user,
                        'Google Maps Link': new_link,
                        'Google Rating': new_rating,
                    }
                    success, error = add_to_visit_place(data)
                    if success:
                        load_travel_data.clear()
                        st.success(f"Added '{new_name}' to your To Visit list!")
                        st.rerun()
                    else:
                        st.error(f"Couldn't add place: {error}")


def _render_mark_visited(row, idx, logged_user):
    mv_key = f"mv_open_{idx}"
    if st.button("✅ Mark as Visited", key=f"mv_btn_{idx}"):
        st.session_state[mv_key] = True

    if not st.session_state.get(mv_key):
        return

    with st.form(f"mv_form_{idx}"):
        visited_date = st.date_input("📅 Date Visited", value=date.today())
        cc, cd = st.columns(2)
        with cc:
            total_cost = st.number_input("💰 Total Cost (₹)", min_value=0,
                                          value=int(row.get('Estimated Cost') or 0), step=100, key=f"mv_cost_{idx}")
        with cd:
            added_by = st.text_input("👤 Added By", value=row.get('Added By') or logged_user, key=f"mv_by_{idx}")
        ca, cb = st.columns(2)
        with ca:
            rating_aman = st.slider("Aman's Rating", 0.0, 5.0, 4.0, 0.5, key=f"mv_ra_{idx}")
        with cb:
            rating_sandra = st.slider("Sandra's Rating", 0.0, 5.0, 4.0, 0.5, key=f"mv_rs_{idx}")
        memory = st.text_area("🥰 Memory", key=f"mv_mem_{idx}")
        revisit_worthy = st.selectbox("🤔 Revisit Worthy", ["Yes", "No", "Maybe"], key=f"mv_rw_{idx}")

        if st.form_submit_button("Confirm move to Visited"):
            success, warning = mark_place_visited(row, {
                'date_visited': visited_date,
                'total_cost': total_cost,
                'added_by': added_by,
                'rating_aman': rating_aman,
                'rating_sandra': rating_sandra,
                'memory': memory,
                'revisit_worthy': revisit_worthy,
            })
            if success:
                st.session_state.pop(mv_key, None)
                load_travel_data.clear()
                st.success(f"🎉 Marked '{row.get('Place Name')}' as visited!")
                if warning:
                    st.warning(warning)
                st.rerun()
            else:
                st.error(f"Couldn't update Google Sheets: {warning}")


def render(to_visit_df, all_df, logged_user):
    st.markdown("""
    <div class="page-header">
      <h1>📍 Places To Visit</h1>
      <p>Your wishlist of destinations waiting to be explored.</p>
    </div>
    """, unsafe_allow_html=True)

    _render_add_place_form(to_visit_df, logged_user)

    if to_visit_df.empty:
        st.warning("No places in your 'To Visit' list yet. Add some places above to get started!")
        return

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
            has_distance = 'Distance (km)' in to_visit_df.columns and not to_visit_df['Distance (km)'].isna().all()
            if has_distance:
                max_d    = int(to_visit_df['Distance (km)'].max())
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
    if has_distance:
        filtered_df = filtered_df[filtered_df['Distance (km)'].fillna(0) <= max_dist]

    # Apply sort
    if tv_sort == "Distance (Nearest)" and 'Distance (km)' in filtered_df.columns:
        filtered_df = filtered_df.sort_values('Distance (km)', ascending=True, na_position='last')
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
        return

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

                    dist = row.get('Distance (km)')
                    if dist and dist > 0:
                        st.markdown(f"**📏 Distance:** {float(dist):.1f} km")

                    home_bits = []
                    for label in ("Aman", "Sandra"):
                        col = f"Distance {label} (km)"
                        val = row.get(col)
                        if val is not None and val == val:  # not NaN
                            home_bits.append(f"{label}: {val:.1f} km")
                    if home_bits:
                        st.markdown(f"**🏠 From home:** {' · '.join(home_bits)}")

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
                _render_mark_visited(row, idx, logged_user)
