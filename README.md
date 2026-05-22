# 🎬 Movie Cluster Explorer

Interactive Streamlit app clustering **4,800 TMDB movies** by description similarity.

## Algorithm
| Step | Method | Details |
|------|--------|---------|
| Feature extraction | TF-IDF | 8 000 terms, bigrams, overview + genres + keywords |
| Dim reduction | TruncatedSVD (LSA) | 100 dims for clustering, 2D for scatter plot |
| Clustering | KMeans++ | k chosen by silhouette analysis |
