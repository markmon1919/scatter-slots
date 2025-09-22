#!/usr/bin/env .venv/bin/python

import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
import io, requests
from matplotlib.animation import FuncAnimation
from config import API_URL


# api_url = API_URL[0]  # localhost
api_url = API_URL[2]  # local network

# ---------- GET GAME INFO ----------    
def get_games_data_from_local_api():
    try:
        response = requests.get(f"{api_url}/games", timeout=3)
        response.raise_for_status()
        json_data = response.json()
        data = json_data.get("registered_games", [])
        return data if data else None
    except Exception as e:
        print(f"❌ Error calling /games API: {e}")
        return None
    
def get_games_csv_from_local_api():
    try:
        response = requests.get(f"{api_url}/file/game", timeout=3)
        if response.status_code == 200:
            text = response.text.strip()
            if not text:
                print("⚠️ API returned empty CSV")
                return None
            return io.StringIO(text)
        else:
            print(f"❌ Failed to fetch CSV. Status: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌  Error calling /file/game API: {e}")
        return None

# ---------- SETTINGS ----------
GAME_LIST = get_games_data_from_local_api()
GAME = GAME_LIST[0] if GAME_LIST else None
GAME_LABEL = GAME if GAME else "⚠️  No game registered"

CSV_FILE = None
if GAME:
    CSV_FILE = f"{GAME.replace(' ', '_').lower()}_log.csv"

MAX_CANDLES = 45 # 1 candle : 10 secs / 6 candles : 1 min
REFRESH_INTERVAL = 2000  # ms

# Dark style with green up/red down
mc = mpf.make_marketcolors(up='lightgreen', down='tomato', wick='white', edge='inherit')
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
    try:
        # Always fetch fresh CSV each cycle
        csv_buffer = get_games_csv_from_local_api()
        if csv_buffer:
            df = pd.read_csv(
                csv_buffer,
                parse_dates=['timestamp'],
                date_format="%Y-%m-%d %I:%M:%S %p",
                skipinitialspace=True
            )
        elif CSV_FILE:
            df = pd.read_csv(
                CSV_FILE,
                parse_dates=['timestamp'],
                date_format="%Y-%m-%d %I:%M:%S %p",
                skipinitialspace=True
            )
        else:
            return pd.DataFrame()
    except (pd.errors.EmptyDataError, FileNotFoundError) as e:
        print(f"⚠️  No CSV data available ({e}).")
        return pd.DataFrame()
    except Exception as e:
        print(f"⚠️  Unexpected CSV error: {e}")
        return pd.DataFrame()

    if "timestamp" not in df.columns or "10m_delta" not in df.columns:
        print("⚠️  Missing required columns in CSV")
        return pd.DataFrame()

    # Filter only today
    today = pd.Timestamp.now().date()
    df_today = df[df['timestamp'].dt.date == today].reset_index(drop=True)
    if df_today.empty:
        return pd.DataFrame()

    # Build OHLC
    df_today['Open'] = df_today['10m_delta'].shift(1)
    df_today['Close'] = df_today['10m_delta']
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
            ylabel='10m Delta Value'
        )
        ax.set_title(f"{GAME_LABEL} - [ 10 MIN DELTA CHART ] ({pd.Timestamp.now().date()})", color="white")
    else:
        ax.set_title(f"{GAME_LABEL} - ⚠️  No data available", color="white")

    ax.set_xlabel("Time", color="white")
    ax.set_ylabel("10m Delta Value", color="white")
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right', color='white')
    plt.setp(ax.get_yticklabels(), color='white')
    ax.grid(True, linestyle="--", color="gray", alpha=0.5)

# ---------- MAIN ----------
fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor('black')

ani = FuncAnimation(fig, animate, interval=REFRESH_INTERVAL, cache_frame_data=False)

plt.tight_layout()
print(f"📊 Live chart running {GAME_LABEL}... refresh every {REFRESH_INTERVAL/1000:.0f}s")
plt.show()
