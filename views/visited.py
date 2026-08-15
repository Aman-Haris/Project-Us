import pandas as pd
import streamlit as st

from ui_helpers import apply_text_search, resolve_groups, star_rating, render_nearby


def render(visited_df, all_df):
    st.markdown("""
    <div class="page-header">
      <h1>✅ Visited Places</h1>
      <p>Every place that shaped your journey — beautifully catalogued.</p>
    </div>
    """, unsafe_allow_html=True)

    if visited_df.empty:
        st.info("No visited places yet. Start exploring and mark them here!")
        return

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
        return

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
                    dv = row.get('Date Visited')
                    if pd.notna(dv):
                        date_str = dv.strftime("%d %b %Y") if hasattr(dv, 'strftime') else str(dv)
                        st.markdown(f"**📅 Date Visited:** {date_str}")
                    cost_val = row.get('Estimated Cost', 0)
                    cost_str = f"₹{float(cost_val):,.0f}" if cost_val and float(cost_val) > 0 else "Free / Unknown"
                    st.markdown(f"**💰 Total Cost:** {cost_str}")
                    st.markdown(f"**🤔 Revisit Worthy:** {row.get('Revisit Worthy') or 'N/A'}")

                    home_bits = []
                    for label in ("Aman", "Sandra"):
                        col = f"Distance {label} (km)"
                        val = row.get(col)
                        if val is not None and val == val:  # not NaN
                            home_bits.append(f"{label}: {val:.1f} km")
                    if home_bits:
                        st.markdown(f"**🏠 From home:** {' · '.join(home_bits)}")

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
