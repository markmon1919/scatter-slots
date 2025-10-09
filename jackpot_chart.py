#!/usr/bin/env .venv/bin/python

import io, os, time, threading, requests, queue
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from config import VPS_DOMAIN, API_URL, LOGS_PATH, GAME_FILE


class ChartWatcher:
    def __init__(
        self,
        api_url: str,
        chart_refresh_interval_ms: int = 500,
        fetch_sec: float = 0.5,
        max_rows: int = 60,
        chart_title: str = "Untitled Chart",
        header: str = None
    ):
        self.api_url = api_url
        self.refresh_ms = chart_refresh_interval_ms
        self.fetch_sec = fetch_sec
        self.max_rows = max_rows
        self.chart_title = chart_title
        self.header = header

        # internal state
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.ohlc_df = pd.DataFrame()
        self.game_name = "Unknown"
        self.connected = True
        self.last_data_ts = 0
        self.last_game_ts = 0

        # safe UI updates
        self.ui_queue = queue.Queue()

        # setup chart style
        mc = mpf.make_marketcolors(up="lime", down="tomato", wick="white", edge="inherit")
        self.style = mpf.make_mpf_style(
            base_mpf_style="nightclouds",
            marketcolors=mc,
            facecolor="black",
            edgecolor="black",
            gridcolor="gray",
            rc={
                "axes.labelcolor": "white",
                "xtick.color": "white",
                "ytick.color": "white",
                "axes.edgecolor": "white",
                "grid.color": "gray",
                "grid.linestyle": "--",
            },
        )

    # ======= API Fetch =======
    def get_game_name(self):
        """Fetch the current game name."""
        try:
            with open(GAME_FILE, "r", encoding="utf-8") as f:
                name = f.read().strip()
                
            if name and name.lower() != "none":
                if self.game_name != name:
                    print(f"🎮 Game detected: {name}")
                    self.game_name = name
                    self.ui_queue.put(f"{self.chart_title} — {self.game_name}")
                self.last_game_ts = time.time()
            else:
                if self.game_name == "Unknown":
                    print("⌛ Waiting for valid game name...")
                    self.ui_queue.put(f"{self.chart_title} — Waiting...")
        except Exception as e:
            print(f"❌ Error getting game name: {e}")
            
        # try:
        #     res = requests.get(f"{self.api_url}/file/game", timeout=5)
        #     name = res.text.strip() if res.status_code == 200 else ""
        #     if name and name.lower() != "none":
        #         if self.game_name != name:
        #             print(f"🎮 Game detected: {name}")
        #             self.game_name = name
        #             self.ui_queue.put(f"{self.chart_title} — {self.game_name}")
        #         self.last_game_ts = time.time()
        #     else:
        #         if self.game_name == "Unknown":
        #             print("⌛ Waiting for valid game name...")
        #             self.ui_queue.put(f"{self.chart_title} — Waiting...")
        # except Exception as e:
        #     print(f"❌ Error getting game name: {e}")

    def fetch_csv(self):
        """Fetch CSV data."""
        try:
            csv_file = os.path.join(LOGS_PATH, f"{self.game_name.strip().replace(' ', '_').lower()}_log-hs.csv")
            
            if os.path.exists(csv_file):            
                with open(csv_file, "r", encoding="utf-8") as f:
                    csv_content = f.read()
                    self.last_data_ts = time.time()
                    return io.StringIO(csv_content)
            else:
                print(f"⚠️ CSV fille not found ({csv_file})")
                return None
        except Exception as e:
            print(f"❌ Error reading CSV: {e}")
            return None
        
        # if "scatter." in self.api_url:      
        #     try:
        #         csv_file = os.path.join(
        #             LOGS_PATH,
        #             f"{self.game_name.strip().replace('\"', '').replace(' ', '_').lower()}_log-hs.csv"
        #         )
        #         if os.path.exists(csv_file):
        #             with open(csv_file, "r", encoding="utf-8") as f:
        #                 csv_content = f.read()
        #                 self.last_data_ts = time.time()
        #                 return io.StringIO(csv_content)  # so pandas can read it
        #         else:
        #             print(f"⚠️ CSV file not found: {csv_file}")
        #             return None

        #     except Exception as e:
        #         print(f"❌ Error reading CSV: {e}")
        #         return None
        # else:
        #     try:
        #         res = requests.get(f"{self.api_url}/file/jackpot", timeout=5)
        #         if res.status_code == 200 and res.text.strip():
        #             self.last_data_ts = time.time()
        #             return io.StringIO(res.text)
        #         print(f"⚠️ CSV fetch failed ({res.status_code})")
        #     except Exception as e:
        #         print(f"❌ Error fetching CSV: {e}")
        #     return None

    def process_csv(self, buf):
        """Parse CSV into OHLC dataframe."""
        try:
            df = pd.read_csv(
                buf,
                parse_dates=["timestamp"],
                date_format="%Y-%m-%d %I:%M:%S %p",
                skipinitialspace=True
            )
            if self.header not in df.columns:
                print(f"⚠️ Missing {self.header} column.")
                return pd.DataFrame()

            today = pd.Timestamp.now().date()
            df = df[df['timestamp'].dt.date == today].reset_index(drop=True)

            if df.empty:
                return pd.DataFrame()

            df["Open"] = df[self.header].shift(1)
            df["Close"] = df[self.header]
            df["High"] = df[["Open", "Close"]].max(axis=1)
            df["Low"] = df[["Open", "Close"]].min(axis=1)
            df = df.dropna()
            ohlc = df[['timestamp', 'Open', 'High', 'Low', 'Close']].copy()
            ohlc.set_index('timestamp', inplace=True)
            return ohlc.tail(self.max_rows)
        except Exception as e:
            print(f"⚠️ CSV parse error: {e}")
            return pd.DataFrame()

    # ======= Threads =======
    def data_watcher(self):
        """Continuously fetch and update chart data."""
        while not self.stop_event.is_set():
            buf = self.fetch_csv()
            if buf:
                df = self.process_csv(buf)
                with self.lock:
                    self.ohlc_df = df
            time.sleep(self.fetch_sec)

    def poll_game_name(self):
        """Periodically check game name."""
        while not self.stop_event.is_set():
            self.get_game_name()
            time.sleep(2)

    # ======= Chart Update =======
    def update_chart(self, _):
        """Matplotlib animation frame update."""
        while not self.ui_queue.empty():
            title = self.ui_queue.get_nowait()
            try:
                self.fig.canvas.manager.set_window_title(title)
            except Exception:
                pass

        now = time.time()
        disconnected = (now - max(self.last_data_ts, self.last_game_ts)) > 10
        if disconnected and self.connected:
            self.connected = False
            print("⚠️ Lost connection (no updates for 10s)")
            self.ui_queue.put(f"{self.chart_title} — {self.game_name} (Disconnected)")
        elif not disconnected and not self.connected:
            self.connected = True
            print("✅ Connection restored")
            self.ui_queue.put(f"{self.chart_title} — {self.game_name}")

        self.ax.clear()
        self.ax.set_facecolor("black")

        with self.lock:
            df = self.ohlc_df.copy()

        if not df.empty:
            mpf.plot(
                df,
                ax=self.ax,
                style=self.style,
                type="candle",
                ylabel=self.header,
                show_nontrading=True
            )
            self.ax.set_title(
                f"{self.game_name} - {self.chart_title} ({pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')})",
                color="white",
            )
        else:
            self.ax.set_title("Waiting for data...", color="white")

        self.ax.set_xlabel("Time", color="white")
        self.ax.set_ylabel(self.header.title(), color="white")
        plt.setp(self.ax.get_xticklabels(), rotation=45, ha="right", color="white")
        plt.setp(self.ax.get_yticklabels(), color="white")
        self.ax.grid(True, linestyle="--", color="gray", alpha=0.5)

    # ======= Runner =======
    def run(self):
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.fig.patch.set_facecolor("black")
        self.fig.canvas.manager.set_window_title(f"{self.chart_title} — Waiting...")
        
        threading.Thread(target=self.poll_game_name, daemon=True).start()
        threading.Thread(target=self.data_watcher, daemon=True).start()

        ani = FuncAnimation(self.fig, self.update_chart, interval=self.refresh_ms, cache_frame_data=False)
        plt.tight_layout()

        print(f"📡 Chart running (refresh={self.refresh_ms/1000:.1f}s)")

        try:
            plt.show()
        except KeyboardInterrupt:
            print("🛑 Interrupted")
        finally:
            self.stop_event.set()
            print("✅ Clean exit")


# ======= Run Instance =======
if __name__ == "__main__":
    api_url = VPS_DOMAIN # vps
    # api_url = API_URL[0]  # localhost
    # api_url = API_URL[2]  # local network

    chart_refresh_interval_ms = 500
    fetch_sec = 0.5
    max_rows = 60

    watcher = ChartWatcher(
        api_url,
        chart_refresh_interval_ms,
        fetch_sec,
        max_rows,
        chart_title="Jackpot Pull Chart",
        header = "jackpot_delta"
    )
    watcher.run()
    