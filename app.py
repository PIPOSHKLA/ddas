import streamlit as st
import pandas as pd

st.set_page_config(page_title="SET50 Shareholder Dashboard", layout="wide")

df = pd.read_csv("set50.csv")

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
shareholder_cols = ["shareholder_1", "percent_1", "shareholder_2", "percent_2",
                    "shareholder_3", "percent_3", "shareholder_4", "percent_4",
                    "shareholder_5", "percent_5"]

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
