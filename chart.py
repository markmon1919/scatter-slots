#!/usr/bin/env .venv/bin/python

import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
import requests
from matplotlib.animation import FuncAnimation
from config import API_URL

# ---------- GET GAME INFO ----------
def get_games_data_from_local_api():
    try:
        response = requests.get(
            f"{API_URL[0]}/games",
        )

        json_data = response.json()
        data = json_data.get("registered_games", [])
        return data if data else None

    except Exception as e:
        print(f"❌ Error calling API: {e}")
        return {"error": str(e)}

# ---------- SETTINGS ----------
GAME = None
CSV_FILE = None
GAME_LIST = get_games_data_from_local_api()

if GAME_LIST:
    GAME = GAME_LIST[0]  # take the first registered game
    CSV_FILE = f"{GAME.replace(' ', '_').lower()}_log.csv"
else:
    print("⚠️ No registered games found from API.")
    
MAX_CANDLES = 24
REFRESH_INTERVAL = 2000  # ms

# Dark style with green up/red down
mc = mpf.make_marketcolors(
    up='lime',
    down='red',
    wick='white',
    edge='inherit'
)

dark_style = mpf.make_mpf_style(
    base_mpf_style='nightclouds',
    marketcolors=mc,
    facecolor='black',
    edgecolor='black',
    gridcolor='gray',
    rc={
        'axes.labelcolor': 'white',
        'xtick.color': 'white',
        'ytick.color': 'white',
        'axes.edgecolor': 'white',
        'grid.color': 'gray',
        'grid.linestyle': '--'
    }
)

# ---------- DATA LOADING ----------
def load_data():
    df = pd.read_csv(
        CSV_FILE,
        parse_dates=['timestamp'],
        date_format="%Y-%m-%d %I:%M:%S %p",
        skipinitialspace=True
    )

    today = pd.Timestamp.now().date()
    df_today = df[df['timestamp'].dt.date == today].reset_index(drop=True)

    if df_today.empty:
        return pd.DataFrame()

    df_today['Open'] = df_today['10m'].shift(1)
    df_today['Close'] = df_today['10m']
    df_today['High'] = df_today[['Open', 'Close']].max(axis=1)
    df_today['Low'] = df_today[['Open', 'Close']].min(axis=1)
    df_today = df_today.dropna()

    ohlc = df_today[['timestamp', 'Open', 'High', 'Low', 'Close']].copy()
    ohlc.set_index('timestamp', inplace=True)

    return ohlc.tail(MAX_CANDLES)

# ---------- ANIMATION ----------
def animate(i):
    ohlc = load_data()
    ax.clear()
    ax.set_facecolor('black')

    if not ohlc.empty:
        mpf.plot(
            ohlc,
            type='candle',
            style=dark_style,
            ax=ax,
            ylabel='10m Value'
        )

        ax.set_title(f"{GAME} - [10 minute Chart] ({pd.Timestamp.now().date()})", color="white")
        ax.set_xlabel("Time", color="white")
        ax.set_ylabel("10m Value", color="white")
        
        # Rotate x-axis labels for better readability
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right', color='white')
        plt.setp(ax.get_yticklabels(), color='white')
        
        ax.grid(True, linestyle="--", color="gray", alpha=0.5)
    else:
        ax.set_title("⚠️  No data available for today", color="white")
        ax.set_xlabel("Time", color="white")
        ax.set_ylabel("10m Value", color="white")

# ---------- MAIN ----------
fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor('black')

ani = FuncAnimation(fig, animate, interval=REFRESH_INTERVAL, cache_frame_data=False)

plt.tight_layout()
print(f"📊 Live chart running {GAME}... refresh every {REFRESH_INTERVAL/1000:.0f}s")
plt.show()
