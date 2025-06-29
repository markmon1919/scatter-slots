#!/usr/bin/env python

import streamlit as st
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Jackpot Monitor", layout="wide")

csv_file = "updated_file.csv"

st.title("🎰 Jackpot Monitor")

# Auto-refresh every 30s
st_autorefresh = st.experimental_rerun if st.button("🔄 Refresh Now") else None

# Load data
df = pd.read_csv(csv_file, parse_dates=["timestamp"])
df = df.sort_values("timestamp")

# Select how many recent records to show
num_points = st.slider("How many latest points?", 10, 100, 50)

recent_df = df.tail(num_points)

# Live line chart
st.subheader("📈 Jackpot Value Over Time")
st.line_chart(recent_df[["timestamp", "value"]].set_index("timestamp"))

# Change metrics
st.subheader("📊 % Change by Timeframe")
cols = st.columns(6)
intervals = ["5s_change", "1m_change", "10m_change", "1h_change", "3h_change", "6h_change"]

latest = recent_df.iloc[-1]

for col, interval in zip(cols, intervals):
    val = latest.get(interval, "")
    col.metric(label=interval, value=val)

# Show full table
with st.expander("📋 Raw Data"):
    st.dataframe(recent_df, use_container_width=True)