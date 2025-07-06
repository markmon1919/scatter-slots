import streamlit as st
import pandas as pd
from datetime import timedelta
from streamlit_autorefresh import st_autorefresh
import time
import os

st.set_page_config(page_title="📊 Jackpot Monitor", layout="wide")  # MUST be first Streamlit call

INPUT_FILE = "slimeserveahead_aztec_priestess_log.csv"

# Extended timeframes
CHANGE_WINDOWS = {
    "5s_change": 5,
    "10s_change": 10,
    "30s_change": 30,
    "1m_change": 60,
    "2m_change": 120,
    "3m_change": 180,
    "4m_change": 240,
    "5m_change": 300,
    "10m_change": 600,
    "1h_change": 3600,
    "3h_change": 10800,
    "6h_change": 21600,
}

@st.cache_data(ttl=2)
def load_data():
    if not os.path.exists(INPUT_FILE):
        return pd.DataFrame()
    df = pd.read_csv(INPUT_FILE, parse_dates=["timestamp"])
    return df.sort_values("timestamp")

def compute_changes(df, row):
    for col, seconds in CHANGE_WINDOWS.items():
        past_time = row["timestamp"] - timedelta(seconds=seconds)
        past_rows = df[df["timestamp"] <= past_time]
        if not past_rows.empty:
            past_val = past_rows.iloc[-1]["value"]
            change = ((row["value"] - past_val) / past_val) * 100
            row[col] = f"{change:.2f}%"
        else:
            row[col] = ""
    return row

st.title("🎰 Live Jackpot Monitor")
st.markdown(f"Monitoring file: `{INPUT_FILE}`")

df = load_data()

if df.empty:
    st.warning("Waiting for data...")
    st.stop()

# Compute changes
processed_rows = []
for i, row in df.iterrows():
    row = compute_changes(df, row.copy())
    processed_rows.append(row)

df_processed = pd.DataFrame(processed_rows)

# Show latest 20 rows
st.dataframe(
    df_processed.tail(20),
    use_container_width=True,
    hide_index=True,
)

# Auto-refresh every 2 seconds
st_autorefresh(interval=2000, key="data_refresh")