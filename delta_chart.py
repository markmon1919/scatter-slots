#!/usr/bin/env .venv/bin/python

import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
import io, requests
from matplotlib.animation import FuncAnimation
from config import API_URL


# ---------- SETTINGS ----------
api_url = API_URL[0]  # localhost
# api_url = API_URL[2]  # local network
GAME = None
MAX_CANDLES = 60 # 1 candle : 10 secs / 6 candles : 1 min
REFRESH_INTERVAL = 500  # ms

# ---------- GET GAME INFO ----------    
def get_game_name_from_local_api():
    try:
        response = requests.get(f"{api_url}/file/game", timeout=5)
        if response.status_code == 200:
            data = response.text.strip()
            return data
        else:
            print(f"❌ Failed to fetch game file. Status: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌  Error calling /file/game API: {e}")
        return None
    
def get_games_csv_from_local_api():
    try:
        response = requests.get(f"{api_url}/file", timeout=5)
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
        print(f"❌  Error calling /file API: {e}")
        return None

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
def load_data(resample_rule: str | None = None):
    global GAME  # so we can update it if needed
    try:
        # Fetch CSV from API
        csv_buffer = get_games_csv_from_local_api()

        # If CSV is empty, try refreshing GAME and fetch again
        if not csv_buffer:
            print("⚠️ CSV buffer empty, fetching game name again...")
            GAME = get_game_name_from_local_api()
            csv_buffer = get_games_csv_from_local_api()
        
        if not csv_buffer:
            return pd.DataFrame()  # still empty
        # --- continue normal CSV loading ---
        df = pd.read_csv(
            csv_buffer,
            parse_dates=['timestamp'],
            date_format="%Y-%m-%d %I:%M:%S %p",
            skipinitialspace=True
        )
    except (pd.errors.EmptyDataError, FileNotFoundError) as e:
        print(f"⚠️ No CSV data available ({e}).")
        return pd.DataFrame()
    except Exception as e:
        print(f"⚠️ Unexpected CSV error: {e}")
        return pd.DataFrame()

    if "timestamp" not in df.columns or "10m_delta" not in df.columns:
        print("⚠️ Missing required columns in CSV")
        return pd.DataFrame()

    # Filter only today
    today = pd.Timestamp.now().date()
    df_today = df[df['timestamp'].dt.date == today].reset_index(drop=True)
    if df_today.empty:
        return pd.DataFrame()

    if resample_rule:
        ohlc = (
            df_today.set_index("timestamp")['10m_delta']
            .resample(resample_rule)
            .ohlc()
            .dropna()
        )
    else:
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
    title = GAME if GAME else "Unknown Game"

    if not ohlc.empty:
        mpf.plot(
            ohlc,
            type='candle',
            style=dark_style,
            ax=ax,
            ylabel='10m Delta Value',
            # show_nontrading=True
        )
        ax.set_title(f"{title} - [ 10 MIN DELTA CHART ] ({pd.Timestamp.now().date()})", color="white")
    else:
        ax.set_title(f"{title} - ⚠️ No data available", color="white")

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
print(f"📊 Live chart running {GAME}... refresh every {REFRESH_INTERVAL/1000:.0f}s")
plt.show()
