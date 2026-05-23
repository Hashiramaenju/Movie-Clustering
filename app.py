
import streamlit as st
import pandas as pd
import json
import plotly.express as px

st.set_page_config(
    page_title="Movie Cluster Explorer",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css');

html, body, [class*="css"] { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
.main { background: #f5f5f7; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* topbar */
.topbar {
    background: #4B3FBF;
    padding: 14px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.topbar-left { display: flex; align-items: center; gap: 12px; }
.logo-box {
    width: 40px; height: 40px;
    background: rgba(255,255,255,0.15);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
}
.topbar-title { color: #fff; font-size: 18px; font-weight: 600; margin: 0; }
.topbar-sub { color: rgba(255,255,255,0.6); font-size: 12px; margin: 0; }
.topbar-right { display: flex; gap: 8px; align-items: center; }
.tbadge {
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 8px;
    padding: 6px 14px;
    color: #fff;
    font-size: 12px;
}
.tbadge b { font-size: 14px; }

/* sidebar */
section[data-testid="stSidebar"] { background: #fff !important; border-right: 1px solid #e5e5e5; }
section[data-testid="stSidebar"] .block-container { padding: 1.5rem 1rem !important; }

/* cluster section */
.cluster-card {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    margin-bottom: 16px;
    overflow: hidden;
}
.cluster-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 18px;
    border-bottom: 1px solid #f0f0f0;
}
.cluster-num {
    width: 36px; height: 36px;
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 15px; font-weight: 600;
}
.cluster-name { font-size: 14px; font-weight: 600; color: #111; margin: 0; }
.cluster-meta { font-size: 11px; color: #888; margin: 0; }
.movie-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0; }
.movie-tile {
    padding: 12px;
    border-right: 1px solid #f0f0f0;
    cursor: pointer;
}
.movie-tile:last-child { border-right: none; }
.movie-poster {
    width: 100%;
    aspect-ratio: 2/3;
    border-radius: 8px;
    margin-bottom: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 28px;
    overflow: hidden;
    object-fit: cover;
}
.movie-title { font-size: 12px; font-weight: 600; color: #111; margin: 0 0 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.movie-meta { font-size: 11px; color: #888; }

/* dist bar */
.dist-row { margin-bottom: 12px; }
.dist-label { display: flex; justify-content: space-between; font-size: 12px; color: #333; margin-bottom: 4px; }
.dist-pct { color: #888; }
.bar-track { height: 5px; background: #f0f0f0; border-radius: 999px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 999px; }

h1, h2, h3 { color: #111 !important; }
</style>
""", unsafe_allow_html=True)

CLUSTER_COLORS = [
    {"bg":"#EEEDFE","text":"#3C3489","bar":"#7F77DD","label":"Action & Adventure"},
    {"bg":"#FBEAF0","text":"#72243E","bar":"#D4537E","label":"Drama & Romance"},
    {"bg":"#E6F1FB","text":"#0C447C","bar":"#378ADD","label":"Sci-Fi & Thriller"},
    {"bg":"#E1F5EE","text":"#085041","bar":"#1D9E75","label":"Comedy"},
    {"bg":"#FAECE7","text":"#712B13","bar":"#D85A30","label":"Horror & Mystery"},
    {"bg":"#FAEEDA","text":"#633806","bar":"#BA7517","label":"Animation & Family"},
    {"bg":"#F1EFE8","text":"#444441","bar":"#888780","label":"Documentary"},
    {"bg":"#EAF3DE","text":"#27500A","bar":"#639922","label":"War & History"},
]

@st.cache_data
def load_data():
    df = pd.read_csv("app_data/movies_clustered.csv")
    with open("app_data/cluster_labels.json") as f:
        labels = json.load(f)
    return df, {int(k): v for k, v in labels.items()}

df, cluster_labels = load_data()
K = df["cluster"].nunique()

# ── Topbar ────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="topbar">
  <div class="topbar-left">
    <div class="logo-box">🎬</div>
    <div>
      <p class="topbar-title">Movie Clusters</p>
      <p class="topbar-sub">Grouping movies by text similarity using K-Means clustering</p>
    </div>
  </div>
  <div class="topbar-right">
    <div class="tbadge">Movies: <b>{len(df):,}</b></div>
    <div class="tbadge">Clusters: <b>{K}</b></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Cluster distribution")

    cluster_sizes = df["cluster"].value_counts().sort_index()
    total = len(df)
    for c in range(K):
        count = cluster_sizes.get(c, 0)
        pct = count / total * 100
        col = CLUSTER_COLORS[c % len(CLUSTER_COLORS)]
        label = col["label"]
        st.markdown(f"""
        <div class="dist-row">
          <div class="dist-label"><span>{label}</span><span class="dist-pct">{count:,} ({pct:.0f}%)</span></div>
          <div class="bar-track"><div class="bar-fill" style="width:{pct}%;background:{col['bar']}"></div></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    min_rating = st.slider("Min rating", 0.0, 10.0, 5.0, step=0.5)
    year_min = int(df["year"].replace(0, pd.NA).dropna().min())
    year_max = int(df["year"].max())
    year_range = st.slider("Release year", year_min, year_max, (year_min, year_max))
    search_q = st.text_input("🔍 Search title / keyword", "")

    st.markdown("---")
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()

# ── Filter ────────────────────────────────────────────────────────────────
filt = (
    (df["vote_average"] >= min_rating) &
    (df["year"].between(*year_range) | (df["year"] == 0))
)
if search_q.strip():
    q = search_q.strip().lower()
    filt &= (
        df["title"].str.lower().str.contains(q, na=False) |
        df["overview"].str.lower().str.contains(q, na=False) |
        df["genres_text"].str.lower().str.contains(q, na=False)
    )
view = df[filt].copy()

# ── Summary metrics ───────────────────────────────────────────────────────
st.markdown("<div style='padding: 16px 24px 0'>", unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Movies shown", f"{len(view):,}")
c2.metric("Clusters", view["cluster"].nunique())
c3.metric("Avg rating", f"{view['vote_average'].mean():.2f}" if len(view) else "—")
c4.metric("Year range", f"{year_range[0]} – {year_range[1]}")
st.markdown("</div>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🗂 Cluster view", "📊 Scatter plot", "📈 Stats"])

# ── Tab 1: Cluster cards ──────────────────────────────────────────────────
with tab1:
    for c in sorted(view["cluster"].unique()):
        col = CLUSTER_COLORS[c % len(CLUSTER_COLORS)]
        group = view[view["cluster"] == c].sort_values("vote_average", ascending=False)
        kw = cluster_labels.get(c, "")
        avg_r = group["vote_average"].mean()

        st.markdown(f"""
        <div class="cluster-card">
          <div class="cluster-header">
            <div class="cluster-num" style="background:{col['bg']};color:{col['text']}">{len(group)}</div>
            <div>
              <p class="cluster-name">{col['label']}</p>
              <p class="cluster-meta">{len(group):,} movies &middot; avg rating {avg_r:.1f} &middot; {kw}</p>
            </div>
          </div>
          <div class="movie-grid">
        """, unsafe_allow_html=True)

        for _, row in group.head(4).iterrows():
            year_str = str(int(row.year)) if row.year > 0 else "—"
            st.markdown(f"""
            <div class="movie-tile">
              <div class="movie-poster" style="background:{col['bg']}">🎬</div>
              <p class="movie-title">{row.title}</p>
              <p class="movie-meta">⭐ {row.vote_average:.1f} · {year_str}</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div></div>", unsafe_allow_html=True)

# ── Tab 2: Scatter ────────────────────────────────────────────────────────
with tab2:
    if view.empty:
        st.warning("No movies match the current filters.")
    else:
        v2 = view.copy()
        v2["cluster_str"] = v2["cluster"].astype(str)
        PALETTE = [c["bar"] for c in CLUSTER_COLORS]
        fig = px.scatter(
            v2, x="x", y="y", color="cluster_str",
            hover_name="title",
            hover_data={"vote_average": True, "year": True, "genres_text": True,
                        "x": False, "y": False, "cluster_str": False},
            color_discrete_sequence=PALETTE,
            labels={"cluster_str": "Cluster", "vote_average": "Rating", "genres_text": "Genres"},
            template="plotly_white", height=560
        )
        fig.update_traces(marker=dict(size=6, opacity=0.75))
        fig.update_layout(xaxis=dict(showgrid=False, zeroline=False, title=""),
                          yaxis=dict(showgrid=False, zeroline=False, title=""))
        st.plotly_chart(fig, use_container_width=True)

# ── Tab 3: Stats ──────────────────────────────────────────────────────────
with tab3:
    ca, cb = st.columns(2)
    PALETTE = [c["bar"] for c in CLUSTER_COLORS]
    with ca:
        st.markdown("#### Movies per cluster")
        sizes = view.groupby("cluster").size().reset_index(name="count")
        fig_b = px.bar(sizes, x="cluster", y="count", color="cluster",
                       color_discrete_sequence=PALETTE, template="plotly_white",
                       labels={"cluster": "Cluster", "count": "# Movies"}, height=320)
        fig_b.update_layout(showlegend=False)
        st.plotly_chart(fig_b, use_container_width=True)
    with cb:
        st.markdown("#### Avg rating per cluster")
        avg_r = view.groupby("cluster")["vote_average"].mean().reset_index()
        fig_r = px.bar(avg_r, x="cluster", y="vote_average", color="cluster",
                       color_discrete_sequence=PALETTE, template="plotly_white",
                       labels={"cluster": "Cluster", "vote_average": "Avg Rating"}, height=320)
        fig_r.update_layout(showlegend=False)
        st.plotly_chart(fig_r, use_container_width=True)

    summary = (
        view.groupby("cluster")
            .agg(movies=("title","count"),
                 avg_rating=("vote_average", lambda x: round(x.mean(),2)),
                 avg_year=("year", lambda x: int(x[x>0].mean()) if (x>0).any() else 0),
                 top_keywords=("cluster_keywords","first"))
            .reset_index()
    )
    st.dataframe(summary, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("Dataset: TMDB 5000 · TF-IDF (8k terms, bigrams) → TruncatedSVD/LSA (100d) → KMeans++")
