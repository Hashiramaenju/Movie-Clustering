
import streamlit as st
import pandas as pd
import json
import plotly.express as px

st.set_page_config(
    page_title="🎬 Movie Cluster Explorer",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.main { background: #0f0f13; color: #e8e8f0; }
.block-container { padding-top: 1.5rem; }
.movie-card {
    background: #1a1a24;
    border: 1px solid #2e2e42;
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 10px;
}
.movie-title { font-size: 1.05rem; font-weight: 700; color: #e8e8f0; }
.movie-meta  { font-size: 0.82rem; color: #888; margin-top: 4px; }
.movie-overview { font-size: 0.88rem; color: #bbb; margin-top: 8px; line-height: 1.55; }
h1, h2, h3 { color: #e8e8f0 !important; }
.stSidebar { background: #13131c !important; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv("app_data/movies_clustered.csv")
    with open("app_data/cluster_labels.json") as f:
        labels = json.load(f)
    return df, {int(k): v for k, v in labels.items()}

df, cluster_labels = load_data()
K = df["cluster"].nunique()
PALETTE = px.colors.qualitative.Bold + px.colors.qualitative.Vivid

# ── Sidebar ────────────────────────────────────────────────────────────────
st.sidebar.title("🎬 Movie Clusters")
st.sidebar.markdown(f"**{len(df):,} movies · {K} clusters**")

all_clusters = sorted(df["cluster"].unique())
selected_clusters = st.sidebar.multiselect(
    "Show clusters", options=all_clusters, default=all_clusters,
    format_func=lambda c: f"Cluster {c}"
)
year_min = int(df["year"].replace(0, pd.NA).dropna().min())
year_max = int(df["year"].max())
year_range   = st.sidebar.slider("Release year", year_min, year_max, (year_min, year_max))
rating_min   = st.sidebar.slider("Min rating", 0.0, 10.0, 5.0, step=0.5)
search_q     = st.sidebar.text_input("🔍 Search title / keyword", "")

# ── Filter ─────────────────────────────────────────────────────────────────
filt = (
    df["cluster"].isin(selected_clusters) &
    (df["year"].between(*year_range) | (df["year"] == 0)) &
    (df["vote_average"] >= rating_min)
)
if search_q.strip():
    q = search_q.strip().lower()
    filt &= (
        df["title"].str.lower().str.contains(q, na=False) |
        df["overview"].str.lower().str.contains(q, na=False) |
        df["genres_text"].str.lower().str.contains(q, na=False)
    )
view = df[filt].copy()

# ── Header ─────────────────────────────────────────────────────────────────
st.title("🎬 Movie Cluster Explorer")
st.caption("Movies clustered by description similarity — TF-IDF + LSA + KMeans")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Movies shown",   f"{len(view):,}")
c2.metric("Clusters shown", len(view["cluster"].unique()))
c3.metric("Avg rating",     f"{view[chr(39)+'vote_average'+chr(39)].mean():.2f}" if len(view) else "—")
c4.metric("Year range",     f"{year_range[0]} – {year_range[1]}")
st.divider()

tab1, tab2, tab3 = st.tabs(["📊 Scatter Plot", "📋 Movie Cards", "📈 Cluster Stats"])

# ── Tab 1 ──────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("#### Cluster map — 2-D LSA projection")
    if view.empty:
        st.warning("No movies match the current filters.")
    else:
        view2 = view.copy()
        view2["cluster_str"] = view2["cluster"].astype(str)
        fig = px.scatter(
            view2, x="x", y="y", color="cluster_str",
            hover_name="title",
            hover_data={"vote_average": True, "year": True,
                        "genres_text": True, "x": False, "y": False, "cluster_str": False},
            color_discrete_sequence=PALETTE,
            labels={"cluster_str": "Cluster", "vote_average": "Rating", "genres_text": "Genres"},
            template="plotly_dark", height=560
        )
        fig.update_traces(marker=dict(size=6, opacity=0.75))
        fig.update_layout(
            plot_bgcolor="#0f0f13", paper_bgcolor="#0f0f13",
            xaxis=dict(showgrid=False, zeroline=False, title=""),
            yaxis=dict(showgrid=False, zeroline=False, title=""),
        )
        st.plotly_chart(fig, use_container_width=True)

# ── Tab 2 ──────────────────────────────────────────────────────────────────
with tab2:
    sort_by = st.selectbox("Sort by",
        ["Cluster", "Rating (high→low)", "Popularity (high→low)", "Year (new→old)"])
    if sort_by == "Rating (high→low)":
        view = view.sort_values("vote_average", ascending=False)
    elif sort_by == "Popularity (high→low)":
        view = view.sort_values("popularity", ascending=False)
    elif sort_by == "Year (new→old)":
        view = view.sort_values("year", ascending=False)
    else:
        view = view.sort_values(["cluster", "vote_average"], ascending=[True, False])

    if view.empty:
        st.warning("No movies match the current filters.")
    else:
        PER_PAGE = 30
        total_pages = max(1, (len(view) - 1) // PER_PAGE + 1)
        page = st.number_input("Page", 1, total_pages, 1)
        page_df = view.iloc[(page-1)*PER_PAGE : page*PER_PAGE]
        st.caption(f"Showing {(page-1)*PER_PAGE+1}–{min(page*PER_PAGE, len(view))} of {len(view):,}")

        for cluster_id, group in page_df.groupby("cluster", sort=True):
            colour = PALETTE[cluster_id % len(PALETTE)]
            kw = cluster_labels.get(cluster_id, "")
            st.markdown(
                f"<div style='border-left:3px solid {colour}; padding-left:10px;'>" 
                f"<span style='color:{colour};font-weight:700;'>Cluster {cluster_id}</span>"
                f" <span style='color:#888;font-size:0.82rem;'>· {kw}</span></div>",
                unsafe_allow_html=True
            )
            cols = st.columns(3)
            for i, (_, row) in enumerate(group.iterrows()):
                with cols[i % 3]:
                    year_str = str(int(row.year)) if row.year > 0 else "—"
                    genres   = row.genres_text if isinstance(row.genres_text, str) else ""
                    st.markdown(
                        f"<div class='movie-card'>"
                        f"<div class='movie-title'>{row.title}</div>"
                        f"<div class='movie-meta'>⭐ {row.vote_average:.1f} &nbsp;·&nbsp; 📅 {year_str}</div>"
                        f"<div class='movie-meta'>{genres}</div>"
                        f"<div class='movie-overview'>{str(row.overview)[:180]}{'…' if len(str(row.overview))>180 else ''}</div>"
                        f"</div>", unsafe_allow_html=True
                    )
            st.markdown("<br>", unsafe_allow_html=True)

# ── Tab 3 ──────────────────────────────────────────────────────────────────
with tab3:
    ca, cb = st.columns(2)
    with ca:
        st.markdown("#### Movies per cluster")
        sizes = view.groupby("cluster").size().reset_index(name="count")
        fig_b = px.bar(sizes, x="cluster", y="count", color="cluster",
                       color_discrete_sequence=PALETTE, template="plotly_dark",
                       labels={"cluster": "Cluster", "count": "# Movies"}, height=320)
        fig_b.update_layout(plot_bgcolor="#0f0f13", paper_bgcolor="#0f0f13", showlegend=False)
        st.plotly_chart(fig_b, use_container_width=True)
    with cb:
        st.markdown("#### Avg rating per cluster")
        avg_r = view.groupby("cluster")["vote_average"].mean().reset_index()
        fig_r = px.bar(avg_r, x="cluster", y="vote_average", color="cluster",
                       color_discrete_sequence=PALETTE, template="plotly_dark",
                       labels={"cluster": "Cluster", "vote_average": "Avg Rating"}, height=320)
        fig_r.update_layout(plot_bgcolor="#0f0f13", paper_bgcolor="#0f0f13", showlegend=False)
        st.plotly_chart(fig_r, use_container_width=True)

    st.markdown("#### Summary table")
    summary = (
        view.groupby("cluster")
            .agg(movies=("title","count"),
                 avg_rating=("vote_average", lambda x: round(x.mean(),2)),
                 avg_year=("year", lambda x: int(x[x>0].mean()) if (x>0).any() else 0),
                 top_keywords=("cluster_keywords","first"))
            .reset_index()
    )
    st.dataframe(summary, use_container_width=True, hide_index=True)

st.divider()
st.caption("Dataset: TMDB 5000 · TF-IDF (8k terms, bigrams) → TruncatedSVD/LSA (100d) → KMeans++")
