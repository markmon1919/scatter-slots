#!/usr/bin/env python

import streamlit as st
import pandas as pd
from datetime import timedelta
from streamlit_autorefresh import st_autorefresh
import time
import os

INPUT_FILE = "slimeserveahead_aztec_priestess_log.csv"

CHANGE_WINDOWS = {
    "5s_change": 5,
    "1m_change": 60,
    "10m_change": 600,
    "1h_change": 3600,
    "3h_change": 10800,
    "6h_change": 21600,
}

# Caching keeps data available across Streamlit reruns
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

st.set_page_config(page_title="📊 Jackpot Monitor", layout="wide")

st.title("🎰 Live Jackpot Monitor")
st.markdown("Monitoring file: `helpslot_fortune_gems_log.csv")

# Main display loop (auto refreshes every few seconds)
df = load_data()

if df.empty:
    st.warning("Waiting for data...")
    st.stop()

# Compute changes for latest rows
processed_rows = []
for i, row in df.iterrows():
    row = compute_changes(df, row.copy())
    processed_rows.append(row)

df_processed = pd.DataFrame(processed_rows)

# Display most recent 20 rows
st.dataframe(
    df_processed.tail(20),
    use_container_width=True,
    hide_index=True,
)

# Auto-refresh every 2 seconds
st_autorefresh(interval=2000, key="data_refresh")

