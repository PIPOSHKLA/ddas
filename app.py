import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import tempfile

st.set_page_config(page_title="SET50 Shareholder Dashboard", layout="wide")

df = pd.read_csv("set50.csv")

tab1, tab2 = st.tabs(["Data", "Network"])

with tab1:
    st.title("SET50 Shareholder Dashboard")
    st.markdown(f"Data as of: {df['as_of_date'].iloc[0]}")

    sector = st.sidebar.selectbox("Filter by Sector", ["All"] + sorted(df["sector"].unique()))
    query = st.sidebar.text_input("Search by symbol or company name")

    filtered = df
    if sector != "All":
        filtered = filtered[filtered["sector"] == sector]
    if query:
        filtered = filtered[
            filtered["symbol"].str.contains(query, case=False)
            | filtered["company_name"].str.contains(query, case=False)
        ]

    st.subheader(f"{len(filtered)} stocks")
    cols = ["symbol", "company_name", "sector", "as_of_date"]
    st.dataframe(filtered[cols], use_container_width=True, hide_index=True)

    st.subheader("Top 5 Shareholders")
    for _, row in filtered.iterrows():
        with st.expander(f"{row['symbol']} - {row['company_name']}"):
            sh_data = []
            for i in range(1, 6):
                name = row[f"shareholder_{i}"]
                pct = row[f"percent_{i}"]
                if pd.notna(name):
                    sh_data.append({"Rank": i, "Shareholder": name, "Percent": pct})
            if sh_data:
                st.dataframe(pd.DataFrame(sh_data).set_index("Rank"), use_container_width=True)
            st.caption(f"Source: {row['source_url']}")

with tab2:
    st.title("Shareholder Network Graph")

    min_pct = st.sidebar.slider("Min ownership %", 0.0, 50.0, 2.0, 0.5)
    sector_net = st.sidebar.selectbox("Sector (Network)", ["All"] + sorted(df["sector"].unique()), key="sector_net")
    search_net = st.sidebar.text_input("Search node", key="search_net")

    net_df = df
    if sector_net != "All":
        net_df = net_df[net_df["sector"] == sector_net]

    G = nx.Graph()

    # Limit to top N common shareholders to keep graph readable
    shareholder_counts = {}
    for _, row in net_df.iterrows():
        for i in range(1, 6):
            name = row[f"shareholder_{i}"]
            pct = row[f"percent_{i}"]
            if pd.notna(name) and pct >= min_pct:
                shareholder_counts[name] = shareholder_counts.get(name, 0) + 1

    for _, row in net_df.iterrows():
        company = f"{row['symbol']} ({row['company_name'][:20]})"
        G.add_node(company, label=row["symbol"], title=row["company_name"], color="#4A90D9", shape="dot", size=15)

        for i in range(1, 6):
            name = row[f"shareholder_{i}"]
            pct = row[f"percent_{i}"]
            if pd.notna(name) and pct >= min_pct:
                G.add_node(name, label=name[:25], title=f"{name}\nOwns in {shareholder_counts.get(name, 0)} companies",
                           color="#E67E22", shape="dot", size=10 + min(shareholder_counts.get(name, 0) * 2, 20))
                G.add_edge(company, name, value=round(pct, 1), title=f"{pct:.1f}%")

    if search_net:
        keep = [n for n in G.nodes if search_net.lower() in n.lower()]
        G = G.subgraph(keep + [list(G.neighbors(n)) for n in keep])

    net = Network(height="700px", width="100%", bgcolor="#ffffff", font_color="#333333")
    net.from_nx(G)
    net.set_options("""
    {
      "physics": {
        "barnesHut": { "gravitationalConstant": -3000, "centralGravity": 0.3, "springLength": 200, "springConstant": 0.04 },
        "stabilization": { "iterations": 100 }
      },
      "edges": {
        "color": { "color": "#AAAAAA", "highlight": "#E67E22" },
        "smooth": { "type": "continuous" },
        "font": { "size": 10 }
      },
      "interaction": { "hover": true, "tooltipDelay": 100 }
    }
    """)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as f:
        net.save_graph(f.name)
        with open(f.name, "r", encoding="utf-8") as fh:
            html = fh.read()

    st.components.v1.html(html, height=700)
    st.caption(f"Nodes: {G.number_of_nodes()} | Edges: {G.number_of_edges()} | Min ownership: {min_pct}%")
