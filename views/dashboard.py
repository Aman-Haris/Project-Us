import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def render(all_df, to_visit_df, visited_df):
    st.markdown("""
    <div class="page-header">
      <h1>🏠 Dashboard</h1>
      <p>Track every adventure — places dreamed of and memories made.</p>
    </div>
    """, unsafe_allow_html=True)

    if all_df.empty:
        st.warning("No travel data found. Check your Google Sheets connection.")
        return

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
