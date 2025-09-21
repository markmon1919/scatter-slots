#!/usr/bin/env .venv/bin/python

import pandas as pd
import mplfinance as mpf

# Load CSV
df = pd.read_csv("super_ace_log.csv", parse_dates=["timestamp"])

# Simulate synthetic price using 10m %
synthetic_price = [100.0]  # start at arbitrary base price
for pct in df["10m"]:
    next_price = synthetic_price[-1] * (1 + pct / 100)
    synthetic_price.append(next_price)

# Build OHLC from synthetic price
df = df.iloc[1:].copy()  # align with synthetic_price[1:]
df["Open"] = pd.Series(synthetic_price[:-1])
df["Close"] = pd.Series(synthetic_price[1:])
df["High"] = df[["Open", "Close"]].max(axis=1)
df["Low"] = df[["Open", "Close"]].min(axis=1)
df.set_index("timestamp", inplace=True)

# Plot using mplfinance
ohlc = df[["Open", "High", "Low", "Close"]]
mpf.plot(
    ohlc,
    type="candle",
    style="charles",
    title="Candlestick Chart from 10m % Change",
    ylabel="Synthetic Trend Price",
    figsize=(12, 6),
    tight_layout=True
)