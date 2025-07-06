#!/usr/bin/env python

import pandas as pd
from datetime import timedelta
import time
import os

# Path to your input and output files
input_csv = "slimeserveahead_aztec_priestess_log.csv"
output_csv = "updated_file.csv"

# Time intervals in seconds and their labels
intervals = {
    5: "5s_change",
    10: "10s_change",
    30: "30s_change",
    60: "1m_change",
    120: "2m_change",
    180: "3m_change",
    240: "4m_change",
    300: "5m_change",
    600: "10m_change",
    3600: "1h_change",
    10800: "3h_change",
    21600: "6h_change"
}

# Function to compute % change
def compute_change(df, time_delta_seconds, column_name):
    result = []
    for i, row in df.iterrows():
        current_time = row["timestamp"]
        current_value = row["value"]
        past_time = current_time - timedelta(seconds=time_delta_seconds)
        past_df = df[df["timestamp"] <= past_time]
        if not past_df.empty:
            past_value = past_df.iloc[-1]["value"]
            change = ((current_value - past_value) / past_value) * 100
            result.append(f"{change:.2f}%")
        else:
            result.append("")
    df[column_name] = result

# Monitoring loop
try:
    while True:
        if os.path.exists(input_csv):
            # Load and prepare the CSV
            df = pd.read_csv(input_csv, parse_dates=["timestamp"])
            df = df.sort_values("timestamp").reset_index(drop=True)

            # Recompute changes
            for seconds, column in intervals.items():
                compute_change(df, seconds, column)

            # Save updated file
            df.to_csv(output_csv, index=False)

            # Print latest snapshot
            print(f"\n📊 Updated at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            latest = df.iloc[-1]
            for label in ["timestamp", "value"] + list(intervals.values()):
                print(f"{label:>12}: {latest[label]}")

        else:
            print("❌ Input CSV not found. Waiting...")

        # Wait before next check
        time.sleep(30)  # Run every 30 seconds

except KeyboardInterrupt:
    print("\n🛑 Monitoring stopped by user.")
