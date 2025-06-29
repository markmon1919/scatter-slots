import atexit, hashlib, json, os,  platform, pyautogui, random, re, shutil, subprocess, sys, time, termios, threading#, csv
# import pandas as pd
from bs4 import BeautifulSoup
from dataclasses import dataclass
# from datetime import datetime
from queue import Queue, Empty
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
#from webdriver_manager.chrome import ChromeDriverManager
from pynput.keyboard import Listener as KeyboardListener, Key, KeyCode
# from pynput.mouse import Listener as MouseListener, Button
from config import (GAME_CONFIGS, DEFAULT_GAME_CONFIG, DATA_FILE, SCREEN_POS, LEFT_SLOT_POS, RIGHT_SLOT_POS, DEFAULT_VOICE, DELAY_RANGE, PROVIDERS, DEFAULT_PROVIDER_PROPS, URLS, CASINOS, 
                    LRED, LBLU, LCYN, LYEL, LMAG, LGRE, LGRY, RED, MAG, YEL, BLU, WHTE, BLRED, BLYEL, BLGRE, BLMAG, BLBLU, BLCYN, BYEL, BWHTE, DGRY, BLNK, CLEAR, RES)


@dataclass
class AutoState:
    game: str = None
    casino: str = None
    dual_slots: bool = False
    spin: bool = False
    auto_spin: bool = True
    turbo: bool = True
    feature: bool = None
    auto_play_menu: bool = False
    widescreen: bool = False
    provider: str = None
    
    auto_mode: bool = False
    # hotkeys: bool = True
    # running: bool = True
    # pressing: bool = False
    # clicking: bool = False
    # current_key: str = None
    # move: bool = False
    # auto_play: bool = False

    bet: int = 0
    last_spin: str = None
    last_trend: str = None
    last_pull: float = 0
    lowest_low: float = 0
    lowest_low_delta: float = 0
    is_breakout: bool = False
    is_breakout_delta: bool = False


@dataclass
class GameSettings:
    sleep_times: dict

def get_sleep_times(auto_play_menu):
    return {
        'q': 0.05,  # 20 cps
        'w': 0.02,  # 50 cps
        'e': 0.01,  # 100 cps
        'a': 0.005, # 200 cps
        's': 0.003, # 300 cps
        'd': 0.001,  # 400 cps
    } if not auto_play_menu else {
        'a': 0.005, # 200 cps
        's': 0.003, # 300 cps
        'd': 0.001  # 400 cps
    }

def configure_game(game, casino, dual_slots):
    state.game = game
    state.casino = casino
    state.dual_slots = dual_slots

    config = GAME_CONFIGS.get(game, DEFAULT_GAME_CONFIG)
    (
        state.spin,
        state.auto_spin,
        state.turbo,
        state.feature,
        state.auto_play_menu,
        state.widescreen,
        state.provider
    ) = config

    return GameSettings(get_sleep_times(state.auto_play_menu))

def setup_driver(session_id=None):
    options = Options()
    if platform.system() != "Darwin":
        options.binary_location = "/opt/google/chrome/chrome"  # Set explicitly
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--headless')
    options.add_argument(f"--user-data-dir=./chrome_profile_{session_id}")
    options.add_argument(f"--profile-directory=Profile_{game.lower()}")  # optional
    service = Service(shutil.which("chromedriver"))
    # service = Service("/opt/homebrew/bin/geckodriver") # Firefox
    return webdriver.Chrome(service=service, options=options)

def fetch_html_via_selenium(driver, game, url):
    driver.get(url)
    time.sleep(1)

    search_box = driver.find_element(By.CLASS_NAME, "gameSearch")
    search_box.send_keys(game)

    if "helpslot" in url:
        providers = driver.find_elements(By.CLASS_NAME, "provider-item")

        for provider in providers:
            try:
                text = provider.find_element(By.CLASS_NAME, "text").text.strip()
                if not state.provider == "JILI" and text == state.provider:
                    provider.click()
                    break
            except:
                continue

    time.sleep(1) # Let results update

    return driver.page_source

def extract_game_data(html):
    game_data = []
    # game_blocks = soup.select(".game")
    soup = BeautifulSoup(html, "html.parser")
    game_blocks = soup.select(".game")

    for block in game_blocks:
        name_tag = block.select_one(".gameName")
        if not name_tag:
            continue

        meter_tag = block.select_one(".meterBody")
        meter_color = None

        if meter_tag:
            classes = meter_tag.get("class", [])
            if "redMeter" in classes:
                meter_color = "red"
            elif "greenMeter" in classes:
                meter_color = "green"

        history_tags = block.select(".historyDetails.percentage div")
        if name_tag and meter_tag and len(history_tags) >= 2:
            game_data.append({
                "name": name_tag.text.strip(),
                "jackpot_meter": meter_tag.text.strip(),
                "color": meter_color,
                "history": {
                    "10m": history_tags[0].text.strip(),
                    "1h": history_tags[1].text.strip(),
                    "3h": history_tags[2].text.strip(),
                    "6h": history_tags[3].text.strip()
                }
            })

    return game_data

def load_previous_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_current_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    # create_log()

# def create_log():
#     sanitized = re.sub(r'\W+', '_', state.game.strip().lower())
#     output_csv = f"{'helpslot' if 'helpslot' in state.url else 'slimeserveahead'}_{sanitized}_log.csv"

#     raw_data = get_game_info()

#     # if not game_data:
#     #     raise ValueError(f"No data found for game: {game_key}")

#     # # Prepare one row from JSON
#     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     value = float(raw_data["jackpot_meter"].strip('%'))

#     history = raw_data.get("history", {})

#     # # Compose CSV row
#     row = {
#         "timestamp": timestamp,
#         "value": value,
#         "5s_change": "",  # No real-time tracking
#         "1m_change": "",  # No real-time tracking
        
#         "10m_change": history.get("10m", ""),
#         "1h_change": history.get("1h", ""),
#         "3h_change": history.get("3h", ""),
#         "6h_change": history.get("6h", ""),
#     }

#     # # Write to CSV
#     fieldnames = ["timestamp", "value", "5s_change", "1m_change", "10m_change", "1h_change", "3h_change", "6h_change"]

#     write_header = not os.path.exists(output_csv)

#     with open(output_csv, "a", newline="") as csvfile:
#         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#         if write_header:
#             writer.writeheader()
#         writer.writerow(row)

#     print(f"✅ Wrote data for {raw_data['name']} to {output_csv}")

def hash_data(data):
    return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

def compare_data(prev, current):
    slots = ["left", "right"]
    bet_level = None
    result = None
    bear_score = 0
    percent = f"{LGRY}%{RES}"
    game_name = f"{BLCYN}{current['name'].upper()}{RES}"
    current_jackpot = pct(current['jackpot_meter'])
    state.is_breakout = False
    state.is_breakout_delta = False

    if prev and 'jackpot_meter' in prev:
        # start_time = time.time()  # Start the timer
        # print(f"\t\nFunction started at: {time.strftime('%H:%M:%S')}")
        prev_jackpot = pct(prev['jackpot_meter'])
        delta = round(current_jackpot - prev_jackpot, 2)
        colored_delta = f"{LRED}{pct(delta)}{RES}" if delta < 0 else f"{LGRE}{delta}{RES}"
        sign = "+" if delta > 0 else ""
        diff = f"({YEL}Prev{RES}: {prev_jackpot}{percent} {LMAG}Δ{RES}: {sign}{colored_delta}{percent})"

        print(f'\n\n\t----------------------------------')
        print(f"\t\t[ {game_name} ] - {PROVIDERS.get(state.provider).provider}")
        print(f"\t\t@ ({state.casino})")
        print(f'\t----------------------------------')
        print(f"\n\t{BYEL}Jackpot Meter{RES}: {BLRED}{current_jackpot}{RES}{percent} {diff} ✅\n") if current_jackpot < prev_jackpot else \
            print(f"\n\t{BYEL}Jackpot Meter{RES}: {current_jackpot}{percent} {diff} ❌\n")
    else:
        print(f'\n\n\t----------------------------------')
        print(f"\t\t[ {game_name} ] - {PROVIDERS.get(state.provider).provider}")
        print(f"\t\t@ ({state.casino})")
        print(f'\t----------------------------------')
        print(f"\n\t{BYEL}Jackpot Meter{RES}: {current_jackpot}{percent}\n")

    for index, (period, value) in enumerate(current['history'].items()):
        old_value = prev['history'].get(period) if prev else None
        colored_value = f"{LRED}{pct(value)}{RES}" if pct(value) < 0 else f"{LGRE}{pct(value)}{RES}"
        diff = ""
        prev_bear_power = 0 if state.last_pull == 0 else state.last_pull

        if old_value is not None:
            colored_old_value = f"{LRED}{pct(old_value)}{RES}" if pct(old_value) < 0 else f"{LGRE}{pct(old_value)}{RES}"
            new_num = pct(value)
            old_num = pct(old_value)

            if new_num is not None and old_num is not None:
                delta = round(new_num - old_num, 2)
                colored_delta = f"{LRED}{pct(delta)}{RES}" if delta < 0 else f"{LGRE}{delta}{RES}"
                sign = "+" if delta > 0 else ""
                diff = f"({YEL}Prev{RES}: {colored_old_value}{percent}, {LMAG}Δ{RES}: {sign}{colored_delta}{percent})"

                if new_num < old_num and delta < 0:
                    bear_score += 1

                if index == 0:
                    new_num_10m = new_num
                    old_num_10m = old_num
                    delta_10m = delta

                    if state.lowest_low == 0:
                        state.lowest_low = round(new_num, 2)
                    elif state.lowest_low != 0 and new_num < state.lowest_low:
                        state.lowest_low = round(new_num, 2)
                        state.is_breakout = True
                        alert_queue.put((None, "break_out"))

                    if state.lowest_low_delta == 0:
                        state.lowest_low_delta = round(delta, 2)
                    elif state.lowest_low_delta !=0 and delta < state.lowest_low_delta:
                        state.lowest_low_delta = round(delta, 2)
                        state.is_breakout_delta = True
                        alert_queue.put((None, "delta_break_out"))
                elif index == 1 and new_num_10m is not None and old_num_10m is not None and delta_10m is not None:
                    h10, h1 = pct(new_num_10m), pct(new_num)
                    ph10, ph1 = pct(old_num_10m), pct(old_num)

                    current_bear_power = h10 - ph10
                    bear_power_analysis = h10 < ph10
                    bear_power_decision = current_bear_power < prev_bear_power
                    state.last_pull = current_bear_power

                    new_delta_10m_1h = h10 - h1
                    old_delta_10m_1h = ph10 - ph1

                    delta_shift = new_delta_10m_1h - old_delta_10m_1h
                    bear_analysis = new_delta_10m_1h < old_delta_10m_1h
                    # bear_decision = h10 < h1 < ph1 # this is mistake

                    score = 0
                    trend = []

                    # if not new_delta_10m_1h < old_delta_10m_1h or not delta_10m < -20:
                    # if not bear_power_analysis and not bear_power_decision or not delta_10m < -20:
                    #     print(f"\t{LYEL}{period}{RES}:  {colored_value}{percent} {diff}") if period == "10m" and pct(value) >= 0 else \
                    #         print(f"\t{LYEL}{period}{RES}: {colored_value}{percent} {diff}") if period == "10m" and pct(value) < 0 else \
                    #         print(f"\t{LYEL}{period}{RES}:   {colored_value}{percent} {diff}") if pct(value) >= 0 else \
                    #         print(f"\t{LYEL}{period}{RES}:  {colored_value}{percent} {diff}")
                    #     print(f"\n\t{LGRY}>>>> Skipping...{RES}\n")
                    #     break

                    # if h10 < 0 < h1 or h10 > 0 > h1:
                    #     trend.append("Reversal Potential")
                    #     score += 2

                    # if abs(delta_shift) > 20:
                    # # if delta_shift < -20:
                    #     trend.append("Strong Pull")
                    #     score += 3

                    # if abs(h10 - h1) < abs(ph10 - ph1):
                    # # if new_delta_10m_1h > old_delta_10m_1h:
                    #     trend.append("Weakening Pull")
                    #     score -= 1

                    # if abs(current_jackpot - prev_jackpot) < 0.05 and abs(delta_shift) > 15:
                    # # if abs(current_jackpot - prev_jackpot) < 0.05 and delta_shift < -15:
                    #     trend.append(f"Hidden Pull {LGRE}({RES}No visible jackpot {LMAG}Δ{RES}{LGRE}){RES}")
                    #     score += 1

                    # ✅ 1. Check for directional reversal: Strong signal
                    # if (h10 < 0 < h1) or (h10 > 0 > h1):
                        # trend.append("Reversal Potential")
                        # score += 3
                    if h10 < 0 < h1 or h10 > 0 > h1:
                        trend.append("Reversal Potential 👍👍")
                        score += 2

                    # ✅ 2. Sharp shift in pull momentum: Medium-strong signal
                    if abs(delta_shift) > 20:
                        trend.append("Strong Pull Surge 👍👍👍")
                        score += 3
                    # if abs(delta_shift) > 25:
                    #     trend.append("Very Strong Pull Surge")
                    #     score += 4
                    # elif abs(delta_shift) > 15:
                    #     trend.append("Moderate Pull Surge")
                    #     score += 2

                    # ✅ 3. Pull strength weakening: Negative signal
                    # if abs(new_delta_10m_1h) < abs(old_delta_10m_1h):
                    if abs(h10 - h1) < abs(ph10 - ph1):
                        trend.append(f"Weakening Pull {LMAG}Δ{RES} 👎")
                        # score -= 2
                        score -= 1

                    # ✅ 4. Low jackpot movement but big delta shift: Hidden pressure
                    # if abs(current_jackpot - prev_jackpot) < 0.03 and abs(delta_shift) > 12:
                    if abs(current_jackpot - prev_jackpot) < 0.05 and abs(delta_shift) > 15:
                        trend.append(f"Hidden Pull {LGRE}({RES}Low Jackpot, High {LMAG}Δ{RES}{LGRE}){RES} 👍")
                        # score += 2
                        score += 1                        

                    # ✅ 5. Confirm with consistent bear power
                    if current_bear_power < prev_bear_power and current_bear_power < 0:
                        trend.append("Consistent Bear Pressure 👍")
                        score += 1
                    elif current_bear_power >= prev_bear_power:
                        trend.append("Weak Pull 👎")
                        score -= 1

                    # ✅ 6. Very Strong Pull
                    if h10 <= -50 and delta_10m <= -50:
                        trend.append("Very Strong Bearish Pull 👍👍👍")
                        score += 3

                    # ✅ 7. Reversal
                    if prev['color'] == "green" and current['color'] == "red":
                        trend.append("Reversal 👍👍")
                        score += 2

                    # ✅ 8. Check for neutralization
                    if not trend:
                        trend.append("Neutral")

                    result = {
                        'current_bear_power': round(current_bear_power, 2),
                        'prev_bear_power': round(prev_bear_power, 2),
                        'bear_power_analysis': bear_power_analysis,
                        'bear_power_decision': bear_power_decision,
                        'current_delta_10m_1h': round(new_delta_10m_1h, 2),
                        'prev_delta_10m_1h': round(old_delta_10m_1h, 2),
                        'delta_shift': round(delta_shift, 2),
                        'pull_score': score,
                        'pull_trend': trend,
                        'bear_analysis': bear_analysis,
                        # 'bear_decision': bear_decision
                    }

                    if bear_power_analysis and bear_power_decision and bear_analysis:
                        if score >= 7 and h10 <= -50 and delta_10m <= -50 and round(new_delta_10m_1h, 2) <= -50 and delta_shift <= -50:
                            bet_level = "max"
                        elif score >= 5 and h10 < 0 and delta_10m < 0 and delta_shift < 0:
                            bet_level = "high"
                        elif score >= 2:
                            bet_level = "mid"
                        elif score >= 0:
                            bet_level = "low"
                        else:
                            bet_level = None

                    # AUTO SPIN
                    # if bet_level is not None and state.auto_mode:
                    if bet_level == "max" and state.auto_mode:
                        if state.dual_slots:
                            pyautogui.press('space')
                            # spin(bet_level=bet_level, chosen_spin=None, slot_position=slots[0])
                            # spin(bet_level=bet_level, chosen_spin=None, slot_position=slots[1])
                            spin_queue.put((bet_level, None, slots[0]))
                            spin_queue.put((bet_level, None, slots[1]))
                        else:
                            # pyautogui.press('space')
                            # time.sleep(3)
                            # spin(bet_level=bet_level, chosen_spin=None)
                            spin_queue.put((bet_level, None, None))
                            
                    # else:
                    #     print(f"\tAuto Mode is {state.auto_mode}")
                # else:
                #     new_num_10m = None
                #     delta_10m = None
                #     bet_level = None
        # else:
        #     diff = f"({YEL}Prev{RES}: {old_value})"

        print(f"\t{LYEL}{period}{RES}:  {colored_value}{percent} {diff}") if period == "10m" and pct(value) >= 0 else \
            print(f"\t{LYEL}{period}{RES}: {colored_value}{percent} {diff}") if period == "10m" and pct(value) < 0 else \
            print(f"\t{LYEL}{period}{RES}:   {colored_value}{percent} {diff}") if pct(value) >= 0 else \
            print(f"\t{LYEL}{period}{RES}:  {colored_value}{percent} {diff}")

    print(f"\n\t🐻 Bear Score: {BWHTE}{bear_score}{RES}")
    if bear_score >= 2:
        print("\n\t✅ Bearish Momentum Detected")
    else:
        print("\n\t❌ Not Enough Bearish Momentum")

    if result is not None:
        pull_score = result.get('pull_score', 0)

        if pull_score >= 8:
            trend_strength = "💥💥💥 Extreme Pull"
        elif pull_score >= 7:
            trend_strength = "🔥🔥 Intense Pull"
        elif pull_score >= 6:
            trend_strength = "☄️ Very Strong Pull"
        elif pull_score >= 5:
            trend_strength = "🔴 Stronger Pull"
        elif pull_score >= 4:
            trend_strength = "🟠 Strong Pull"
        elif pull_score >= 2:
            trend_strength = "🟡 Moderate Pull"
        elif pull_score >= 1:
            trend_strength = "🌀 Weak Pull"
        elif pull_score >= 0:
            trend_strength = "🌀 Neutral"
        else:
            trend_strength = "❓ Invalid"

        print(f"\n\t+++ Pull Score: {BLMAG}{trend_strength}{RES} [ {BLBLU}{pull_score}{RES} ]")
        state.last_trend = f"{re.sub(r'[^\x00-\x7F]+', '', trend_strength)} Score {pull_score}"
        alert_queue.put((None, "pull_trend_score")) if state.last_trend is not None else None

        for idx, pull_trend in enumerate(result.get('pull_trend')):
            print("\n\t+++ Pull Trend: ") if idx == 0 else None
            print(f"\t\t{BWHTE}{pull_trend}{RES}") if pull_trend else None
            
        print(f"\n\t+++ Delta{LMAG}Δ{RES} Shift: {BLRED}{result.get('delta_shift')}{RES}") if result.get('delta_shift') < 0 else \
            print(f"\n\t+++ Delta{LMAG}Δ{RES} Shift: {result.get('delta_shift')}")
        print(f"\t+++ Delta{LMAG}Δ{RES} Shift Decision: ✅") if result.get('delta_shift') <= -20 else \
            print(f"\t+++ Delta{LMAG}Δ{RES} Shift Decision: ❌")
        
        print(f"\n\t🐻 Bear Power ({LGRY}Current 10m{RES}): {BLRED}{result.get('current_bear_power')}{RES}") if result.get('current_bear_power') < 0 else \
            print(f"\n\t🐻 Bear Power ({LGRY}Current 10m{RES}): {result.get('current_bear_power')}")
        print(f"\t🐻 Bear Power ({LGRY}Prev 10m{RES}): {BLRED}{result.get('prev_bear_power')}{RES}") if result.get('prev_bear_power') < 0 else \
            print(f"\t🐻 Bear Power ({LGRY}Prev 10m{RES}): {result.get('prev_bear_power')}")
        print(f"\t🐻 Bear Power ({LGRY}Analysis 10m{RES}): ✅") if result.get('bear_power_analysis') else \
            print(f"\t🐻 Bear Power ({LGRY}Analysis 10m{RES}): ❌")
        print(f"\t🐻 Bear Power Decision: ✅") if result.get('bear_power_decision') else \
            print(f"\t🐻 Bear Power Decision: ❌")

        print(f"\n\t🐻 Bear Delta{LMAG}Δ{RES} Power ({LGRY}Current 10m_1h{RES}): {BLRED}{result.get('current_delta_10m_1h')}{RES}") if result.get('current_delta_10m_1h') < 0 else \
            print(f"\n\t🐻 Bear Delta{LMAG}Δ{RES} Power ({LGRY}Current 10m_1h{RES}): {result.get('current_delta_10m_1h')}")
        print(f"\t🐻 Bear Delta{LMAG}Δ{RES} Power ({LGRY}Previous 10m_1h{RES}): {BLRED}{result.get('prev_delta_10m_1h')}{RES}") if result.get('prev_delta_10m_1h') < 0 else \
            print(f"\t🐻 Bear Delta{LMAG}Δ{RES} Power ({LGRY}Previous 10m_1h{RES}): {result.get('prev_delta_10m_1h')}{RES}")
        print(f"\t🐻 Bear Delta{LMAG}Δ{RES} Power ({LGRY}Analysis 10m_1h{RES}): ✅") if result.get('bear_analysis') else \
            print(f"\t🐻 Bear Delta{LMAG}Δ{RES} Power ({LGRY}Analysis 10m_1h{RES}): ❌")
        # print(f"\t🐻 Bear Delta{LMAG}Δ{RES} Decision: ✅") if result.get('bear_decision') else \
        #     print(f"\t🐻 Bear Delta{LMAG}Δ{RES} Decision: ❌")
        print(f"\n\t>>> Break Out: {BLRED}{state.lowest_low}{RES}{percent} {"✅" if state.is_breakout else "❌"}") if state.lowest_low < 0 else \
            print(f"\n\t>>> Break Out: {state.lowest_low}{percent} {"✅" if state.is_breakout else "❌"}")
        print(f"\t>>> Break Out Delta{LMAG}Δ{RES}: {BLRED}{state.lowest_low_delta}{RES}{percent} {"✅" if state.is_breakout_delta else "❌"}") if state.lowest_low_delta < 0 else \
            print(f"\t>>> Break Out Delta{LMAG}Δ{RES}: {state.lowest_low_delta}{percent} {"✅" if state.is_breakout_delta else "❌"}")
        
    alert_queue.put((bet_level, None))
    alert_queue.put((None, game)) if bet_level is not None else None
    state.last_spin = None
    state.last_trend = None

    print(f"\n\t\t♦️ ♣️  {LYEL}Bet 💰 [{RES} {LRED if current['color'] == "red" else LBLU}{bet_level.upper()}{RES} {BLRED if current['color'] == "red" else BLGRE}{LYEL}]{RES} ♠️ ♥️  {BLCYN}{game.upper()}{RES}\n\n") if bet_level is not None else \
        print("\n\t\t⚠️  Don't Bet!\n\n")
    
    stop_event = threading.Event()
    countdown_thread = threading.Thread(target=countdown_timer, args=(bet_level,59, stop_event,), daemon=True)
    countdown_thread.start()
    # threading.Thread(target=countdown_timer, args=(bet_level,59), daemon=True).start()
    
    # if bet_level is not None:
    #     print(f"\n\t>>> Bet [ {BLYEL}{bet_level.upper()}{RES} ]\n\n")
    #     countdown_thread = threading.Thread(target=countdown_timer, args=(59,), daemon=True)
    #     countdown_thread.start()
    # else:
    #     print(f"\n\t❌ Don't Bet! ❌\n")
    # print('\t[2] - BET_LEVEL << ', bet_level)
    # alert_queue.put((bet_level, None))
    # state.last_spin = None
    # state.last_trend = None

def pct(p): return float(p.strip('%')) if isinstance(p, str) and '%' in p else float(p)

def play_alert(bet_level=None, say=None):
    if platform.system() == "Darwin":
        while True:
            try:
                bet_level, say = alert_queue.get()

                sound_map = {
                    "max": "bet max",
                    "high": "bet high",
                    "mid": "bet mid",
                    "low": "bet low",
                    None: "do not bet"
                }

                sound_file = (
                    "break_out" if say is not None and say == "break_out" else \
                    f"{state.last_trend}" if say is not None and say == "pull_trend_score" else \
                    f"{state.last_spin}" if say is not None and say == "spin_type" else \
                    "auto mode disabled" if say is not None and say == "auto mode DISABLED" else \
                    "auto mode enabled" if say is not None and say == "auto mode ENABLED" else \
                    "hotkeys disabled" if say is not None and say == "hotkeys DISABLED" else \
                    "hotkeys enabled" if say is not None and say == "hotkeys ENABLED" else \
                    "turbo mode on" if say is not None and say == "turbo mode ON" else \
                    "normal speed on" if say is not None and say == "normal speed ON" else \
                    f"{say}" if say is not None else \
                    sound_map.get(bet_level)
                )

                # voices = [ "Trinoids", "Kanya", "Karen", "Kathy", "Nora" ]
                # voice = random.choice(voices) if not state.last_trend else DEFAULT_VOICE
                if state.casino == "JLJL9":
                    voice = DEFAULT_VOICE
                elif state.casino == "Bingo Plus":
                    voice = "Trinoids"
                elif state.casino == "Casino Plus":
                    voice = "Kathy"
                elif state.casino == "Rollem 88":
                    voice = "Karen"
                else:
                    voice = "Nora"
                subprocess.run(["say", "-v", voice, sound_file])
            except Empty:
                continue
            except Exception as e:
                print(f"\n\t[Alert Thread Error] {e}")
    else:
        pass

def countdown_timer(bet_level, seconds, stop_event):
    while seconds > 0 and not stop_event.is_set():
        mins, secs = divmod(seconds, 60)
        text = "Betting Ends In" if bet_level is not None else "Waiting For Next Iteration"
        timer = f"\t⏳ {text}: {BLCYN}{mins:02d}:{BLRED if seconds <= 5 else BLCYN}{secs:02d}{RES}"
        print(f"\r{timer}{' ' * 10}", end="") # Add space padding to clear line
        time.sleep(1)
        seconds -= 1
        alert_queue.put((None, "5 seconds remaining")) if seconds == 5 else None
    print("\r" + " " * 50 + "\r", end="") # Clear the line when done

def spin(bet_level=None, chosen_spin=None, slot_position=None):
    while True:
        try:
            bet_level, chosen_spin, slot_position = spin_queue.get()
            spin_types = [ "normal", "board_spin", "board_spin_delay", "board_spin_turbo", "auto_spin", "turbo" ]
            chosen_spin = random.choice(spin_types) if chosen_spin is None else chosen_spin
            # chosen_spin = "normal"
            # bet_values = list()
            # extra_bet = False
            # bet_reset = False
            # lucky_bet_value = 1
            bet = 0

            if state.dual_slots:
                if slot_position == "left":
                    center_x, center_y = LEFT_SLOT_POS.get("center_x"), LEFT_SLOT_POS.get("center_y")
                elif slot_position == "right":
                    center_x, center_y = RIGHT_SLOT_POS.get("center_x"), RIGHT_SLOT_POS.get("center_y")
                
                # time.sleep(1) if state.auto_mode else None
                pyautogui.doubleClick(x=center_x, y=center_y) if state.auto_mode else None
            else:
                center_x, center_y = SCREEN_POS.get("center_x"), SCREEN_POS.get("center_y")

            cx, cy = center_x, center_y
            x1, x2, y1, y2 = 0, SCREEN_POS.get("right_x"), 0, SCREEN_POS.get("bottom_y")
            
            # print(f"POSITION during switching slots below coordinates: {slot_position}")
            # print(f"Y-axis (screen_height - 1): {y2}")

            # if is_lucky_bet and bet_level is None:
            #     print('\nDEBUG (SETTING BETS) ...\n')
            #     bet = lucky_bet_value
            # elif bet_level == "max":
            #     bet_values = [ 1, 2, 3, 5 ]
            #     bet = random.choice(bet_values)
            # elif bet_level == "high":
            #     bet_values = [ 1, 2, 3 ]
            #     bet = random.choice(bet_values)
            # elif bet_level == "mid":
            #     bet_values = [ 1, 2 ]
            #     bet = random.choice(bet_values)
            # elif bet_level == "low":
            #     bet_values = [ 1, 2 ]
            #     # bet = random.choice(bet_values)
            #     bet = 1

            # print('\nDEBUG (is_lucky_bet) ', is_lucky_bet)
            # print('DEBUG (bet_level) ', bet_level)
            # print('DEBUG (bet_reset) ', bet_reset)
            # print('\nDEBUG (bet) ', bet)

            # BETS
            # if not is_lucky_bet and not state.dual_slots:
            #     print('\nDEBUG (Changing bets)...\n')
            #     if bet == 1:
            #         pyautogui.click(x=random_x - 190, y=random_y + 325)
            #         pyautogui.click(x=random_x - 50, y=random_y + 250)
            #     elif bet == 2:
            #         pyautogui.click(x=random_x - 190, y=random_y + 325)
            #         pyautogui.click(x=random_x - 50, y=random_y + 150)
            #     elif bet == 3:
            #         pyautogui.click(x=random_x - 190, y=random_y + 325)
            #         pyautogui.click(x=random_x - 50, y=random_y + 50)
            #     elif bet == 5:
            #         pyautogui.click(x=random_x - 190, y=random_y + 325)
            #         pyautogui.click(x=random_x - 50, y=random_y)
                    
            #     time.sleep(1)
                
            if chosen_spin == "normal":  # optimize later for space or click dynamics
                if state.spin:
                    pyautogui.doubleClick(x=cx, y=cy + 315)
                else:
                    pyautogui.press('space')
            elif chosen_spin == "board_spin":  # Click confirm during first board spin    
                if state.provider in [ "JILI", "FC" ]:
                    pyautogui.click(x=cx, y=cy)
                elif state.provider in [ "PG", "PP" ]:
                    pyautogui.press('space')
                    time.sleep(1)
                    pyautogui.click(x=cx, y=cy)
            elif chosen_spin == "board_spin_delay":
                if state.provider in [ "JILI", "FC" ]:
                    pyautogui.click(x=cx, y=cy)
                elif state.provider in [ "PG", "PP" ]:
                    pyautogui.press('space')
                    time.sleep(random.randint(*DELAY_RANGE))
                    pyautogui.click(x=cx, y=cy)
            elif chosen_spin == "board_spin_turbo":
                if state.provider in [ "JILI", "FC" ]:
                    pyautogui.doubleClick(x=cx, y=cy)
                elif state.provider in [ "PG", "PP" ]:
                    pyautogui.press('space')
                    pyautogui.click(x=cx, y=cy)
            elif chosen_spin == "auto_spin":
                if not state.dual_slots and state.widescreen and state.provider == "JILI":
                    pyautogui.doubleClick(x=cx + 380, y=cy + 325)
                else:
                    pyautogui.press('space') if not state.spin else pyautogui.doubleClick(x=cx, y=cy + 315)
            elif chosen_spin == "turbo":
                if not state.dual_slots and state.widescreen and state.provider == "JILI":
                    pyautogui.doubleClick(x=cx + 450, y=cy + 325)
                else:
                    pyautogui.press('space') if not state.spin else pyautogui.doubleClick(x=cx, y=cy + 315)
                    
                time.sleep(2)
            
            # BET RESET
            # if bet_reset and not is_lucky_bet:
            #     print('\nDEBUG (BET RESET) ...\n')
            #     pyautogui.click(x=random_x - 190, y=random_y + 325)
            #     pyautogui.click(x=random_x - 50, y=random_y + 250)
            #     time.sleep(1)

            state.last_spin = chosen_spin
            alert_queue.put((None, "spin_type"))

            print(f"\n\t*** {state.last_trend} ***")
            print(f"\tBet: {bet} ({chosen_spin.replace('_', ' ').upper()})\n")
            print(f"\tSlot: {slot_position}\n") if state.dual_slots else None
        except Empty:
            continue

# def on_key_press(key):
#     if key == Key.esc:
#         state.running = False
#         os._exit(0)

#     if key == Key.up:
#         state.auto_mode = not state.auto_mode
#         status = "ENABLED" if state.auto_mode else "DISABLED"
#         play_alert(say=f"auto mode {status}")
#         print(f"Auto Mode: {status}")

#     if key == Key.down:
#         state.hotkeys = not state.hotkeys
#         status = "ENABLED" if state.hotkeys else "DISABLED"
#         play_alert(say=f"hotkeys {status}")
#         print(f"Hotkeys: {status}")

#     if key == Key.right:
#         print("Turbo: ON")
#         play_alert(say="turbo mode ON")
#         pyautogui.PAUSE = 0
#         pyautogui.FAILSAFE = False

#     elif key == Key.left:
#         print("Normal Speed: ON")
#         play_alert(say="normal speed ON")
#         pyautogui.PAUSE = 0.1
#         pyautogui.FAILSAFE = True

#     if key == Key.space:
#         if state.spin:
#             state.pressing = True
#             state.current_key = 'space'
#             num_clicks = 1
#             state.move = True
#         else:
#             state.auto_play = False

#     if isinstance(key, KeyCode):
#         if key.char in [ 'q', 'w', 'e', 'a', 's', 'd' ]:
#             state.pressing = True
#             state.current_key = key.char
#             state.move = True if key.char not in [ 'a', 's', 'd' ] and state.turbo else False
#             if not state.auto_play_menu:
#                 num_clicks = { 'q': 20, 'w': 50, 'e': 100, 'a': 200, 's': 300, 'd': 400 }[ key.char ]
#                 state.auto_play = False
#             else:
#                 num_clicks = { 'q': 1, 'w': 1, 'e': 1, 'a': 200, 's': 300, 'd': 400 }[ key.char ]
#                 state.auto_play = False if key.char in [ 'a', 's', 'd' ] and state.turbo else state.auto_play
#         else:
#             state.pressing = True
#             state.current_key = key.char
#             num_clicks = 1
#             if key.char == 'r':
#                 state.move = True
#                 state.auto_play = False
#             elif key.char == 'v' and state.auto_spin:
#                 state.move = True
#                 state.auto_play = False
#             # elif key.char in [ '1', '2', '3' ] and turbo is True:
#             #     move = True
#             elif key.char == 'f' and state.feature:
#                 state.move = True
#                 state.auto_play = False
#             else:
#                 state.auto_play = False
#     elif key in [ Key.tab, Key.shift ]:
#         state.pressing = True
#         state.current_key = 'tab' if key == Key.tab else 'shift'
#         num_clicks = 1
#         state.move = True
#         state.auto_play = False
#     else:
#         return

#     print(f"\nPressed [{ state.current_key }] ---> { num_clicks } {'click' if num_clicks == 1 else 'clicks'}")

# def on_key_release(key):
#     if key == Key.space:
#         if state.spin:
#             state.pressing = False
#             state.current_key = 'space'
#             num_clicks = 1
#             state.move = False
#         else:
#             state.auto_play = False

#     if isinstance(key, KeyCode):
#         state.pressing = False
#         state.current_key = key.char
#         if key.char in [ 'q', 'w', 'e' ] and state.turbo and state.auto_play_menu:
#             state.move = False
#         elif key.char == 'r':
#             state.move = False
#             state.auto_play = False
#         elif key.char == 'v' and state.auto_spin:
#             state.move = False
#             state.auto_play = False
#         # elif key.char in [ '1', '2', '3' ] and turbo is True:
#         #     move = False
#         elif key.char == 'f' and state.feature:
#             state.move = False
#             state.auto_play = False
#         else:
#             state.auto_play = False
#     elif key in [ Key.tab, Key.shift ]:
#         state.pressing = False
#         state.current_key = 'tab' if key == Key.tab else 'shift'
#         state.move = False
#         state.auto_play = False
#     else:
#         return

#     print(f"\nReleased ---> [{ state.current_key }]")

# def set_location(key):
#     x1, x2 = 0, 0
#     y1, y2 = 0, 0

#     random_x = center_x + random.randint(x1, x2)
#     random_y = center_y + random.randint(y1, y2)

#     if key in [ 'r', 'u', 'i', 'o', 'p', 'j', 'k', 'l' 'm', ',', '.', '/' ]: # SLOT SCREEN
#         if state.game == "Fortune Goddess":
#             if key == 'r':
#                 pyautogui.doubleClick(x=random_x, y=random_y)
#         elif state.game == "Lucky Fortunes":
#             if key == 'r':
#                 pyautogui.doubleClick(x=random_x, y=random_y)
#             elif key in [ 'u', 'i', 'o', 'p', 'j', 'k', 'l' 'm', ',', '.', '/' ]:
#                 pyautogui.click(x=random_x, y=random_y)
#         elif state.auto_play_menu:
#             if key == 'r':
#                 pyautogui.moveTo(x=random_x, y=random_y)
#         else:
#             return
#     elif key == 'f' and state.feature: # FEATURE
#         if state.game == "Fortune Goddess":
#             pyautogui.click(x=random_x, y=random_y + 200)
#             pyautogui.doubleClick(x=random_x, y=random_y + 315)
#         elif state.game == "Lucky Fortunes":
#             pyautogui.click(x=random_x, y=random_y + 200)
#             pyautogui.doubleClick(x=random_x, y=random_y + 380)
#         elif state.auto_play_menu:
#             pyautogui.doubleClick(x=random_x - 600, y=random_y - 70)
#     elif key == 'v' and state.auto_spin: # AUTO SPIN
#         if state.game == "Fortune Goddess":
#             pyautogui.click(x=random_x - 150, y=random_y + 290)
#             pyautogui.doubleClick(x=random_x, y=random_y + 315)
#         elif state.game == "Lucky Fortunes":
#             pyautogui.click(x=random_x - 150, y=random_y + 365)
#             pyautogui.doubleClick(x=random_x, y=random_y + 380)
#         elif state.auto_play_menu:
#             pyautogui.click(x=random_x + 445, y=random_y + 455)
#             pyautogui.click(x=random_x, y=random_y + 180)
#     elif key == 'space' and state.spin: # SPIN BUTTON
#         if state.game == "Fortune Goddess":
#             pyautogui.moveTo(x=random_x, y=random_y + 315)
#         elif state.game == "Lucky Fortunes":
#             pyautogui.moveTo(x=random_x, y=random_y + 380)
#     elif key in [ 'tab', 'shift', 'q', 'w', 'e', 'a' ] and state.turbo: # TURBO BUTTON
#         if state.game == "Fortune Goddess":
#             if key == 'tab':
#                 pyautogui.doubleClick(x=random_x - 210, y=random_y + 350)
#             elif key == 'shift':
#                 pyautogui.click(x=random_x - 210, y=random_y + 350)
#             else:
#                 pyautogui.click(x=random_x - 210, y=random_y + 350)
#         elif state.game == "Lucky Fortunes":
#             if key == 'tab':
#                 pyautogui.doubleClick(x=random_x - 210, y=random_y + 415)
#             elif key == 'shift':
#                 pyautogui.click(x=random_x - 210, y=random_y + 415)
#             else:
#                 pyautogui.click(x=random_x - 210, y=random_y + 415)
#         elif state.auto_play_menu:
#             if not state.auto_play:
#                 pyautogui.click(x=random_x + 445, y=random_y + 455)
#                 state.auto_play = True

#             if key == 'q':
#                 pyautogui.click(x=random_x - 250, y=random_y - 120)
#             elif key == 'w':
#                 pyautogui.click(x=random_x - 60, y=random_y - 120)
#             elif key == 'e':
#                 pyautogui.click(x=random_x + 150, y=random_y - 120)

#             pyautogui.moveTo(x=random_x, y=random_y + 180)

# def keyboard(settings):
#     while state.running:
#         if state.hotkeys and state.pressing and state.current_key: #in settings.sleep_times:
#             if state.current_key == 'd':
#                 pyautogui.doubleClick()
#             else:
#                 if not state.move:
#                     pyautogui.click()
#                 # else:
#                 #     set_location(state.current_key)

#             time.sleep(settings.sleep_times.get(state.current_key, 0.001))
#         else:
#             time.sleep(0.001)

# def mouse():
#     while state.running:
#         if state.clicking and state.auto_play:
#             print("[ MOUSE ] Mouse clicked")
#             state.auto_play = False
#         time.sleep(0.02)

# def on_click(x, y, button, pressed):
#     if button == Button.left:
#         state.clicking = pressed

# def start_listeners(settings):
#     threading.Thread(target=keyboard, args=(settings,), daemon=True).start()
#     threading.Thread(target=mouse, daemon=True).start()

#     with KeyboardListener(on_press=on_key_press, on_release=on_key_release) as kb_listener:
#         kb_listener.join()
#         mouse_listener.join()
    # try:
    #     with KeyboardListener(on_press=on_key_press, on_release=on_key_release) as kb_listener:
    #         kb_listener.join()
    #         mouse_listener.join()
    # except KeyboardInterrupt:
    #     print("\n\n[!] Program interrupted by user. Exiting cleanly...\n")

def monitor_game_info(driver, game):
    previous_hash = None

    while True:
        html = driver.page_source
        data = extract_game_data(html)
        current_info = next((elem for elem in data if elem["name"].lower() == game.lower()), None)

        if current_info:
            current_hash = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
            if current_hash != previous_hash:
                print('NEW DATA')
                all_data = load_previous_data()
                previous_data = all_data.get(game.lower())
                compare_data(previous_data, current_info)
                all_data[game.lower()] = current_info
                save_current_data(all_data)
                previous_hash = current_hash
            # else:
            #     print('Waiting Data...')
        else:
            print(f"[WARN] Game '{game}' not found in current HTML")

        time.sleep(0.1)

def game_selector():
    this = {
        "typed": "",
        "selected_idx": None,
        "blinking": True
    }

    lock = threading.Lock()

    def blink_loop():
        blink_on = True
        while this["blinking"]:
            with lock:
                print(f"{CLEAR}", end="")
                blink_id = int(this["typed"]) if this["typed"].isdigit() and 1 <= int(this["typed"]) <= len(GAME_CONFIGS) else None
                print(render_games(blink_idx=blink_id, blink_on=blink_on))
                print(f"\n\t{DGRY}>>> Select Game: {WHTE}{this['typed']}{RES}", end='', flush=True)
            blink_on = not blink_on
            time.sleep(0.5)

    def on_input(key):
        with lock:
            if key == Key.backspace:
                this["typed"] = this["typed"][:-1]
            elif key == Key.esc:
                print("\nCancelled.")
                this["blinking"] = False
                return False
            elif key == Key.enter:
                if this["typed"].isdigit() and 1 <= int(this["typed"]) <= len(GAME_CONFIGS):
                    this["selected_idx"] = int(this["typed"])
                    this["blinking"] = False
                    return False
                else:
                    this["typed"] = ""
            elif hasattr(key, 'char') and key.char and key.char.isdigit():
                this["typed"] += key.char

    # def render_games(blink_idx=None, blink_on=True):
    #     print(f"\n\n\t>>> {MAG}SCATTER JACKPOT MONITOR{RES} <<<\n\n")
    #     games = list(GAME_CONFIGS.items())
    #     half = (len(games) + 1) // 2
    #     lines = []

    #     for idx, (left_game, left_conf) in enumerate(games[:half], start=1):
    #         left_color = PROVIDERS.get(left_conf.provider).color
    #         left_text = " " * len(left_game) if blink_idx == idx and not blink_on else left_game
    #         left_str = f"[{WHTE}{idx}{RES}] - {left_color}{left_text}{RES}\t"

    #         right_index = idx - 1 + half
    #         if right_index < len(games):
    #             right_game, right_conf = games[right_index]
    #             right_color = PROVIDERS.get(right_conf.provider).color
    #             right_text = " " * len(right_game) if blink_idx == right_index + 1 and not blink_on else right_game
    #             right_str = f"[{WHTE}{right_index + 1:>2}{RES}] - {right_color}{right_text}{RES}"
    #         else:
    #             right_str = ""

    #         lines.append(f"\t{left_str:<50}\t{right_str}")
    #     return "\n".join(lines)

    # Start inner function in thread
    blink_thread = threading.Thread(target=blink_loop, daemon=True)
    blink_thread.start()

    with KeyboardListener(on_press=on_input) as kb_listener:
        kb_listener.join()

    print(f"{CLEAR}", end="")
    print(render_games())
    if this["selected_idx"]:
        game_name = list(GAME_CONFIGS.keys())[this["selected_idx"] - 1]
        print(f"\n\tSelected: {WHTE}{game_name.upper()}{RES}")
        return game_name
    
def render_games(blink_idx=None, blink_on=True):
    print(f"\n\n\t>>> {MAG}SCATTER JACKPOT MONITOR{RES} <<<\n\n")
    games = list(GAME_CONFIGS.items())
    half = (len(games) + 1) // 2
    lines = []

    for idx, (left_game, left_conf) in enumerate(games[:half], start=1):
        left_color = PROVIDERS.get(left_conf.provider).color
        left_text = " " * len(left_game) if blink_idx == idx and not blink_on else left_game
        left_str = f"[{WHTE}{idx}{RES}] - {left_color}{left_text}{RES}\t"

        right_index = idx - 1 + half
        if right_index < len(games):
            right_game, right_conf = games[right_index]
            right_color = PROVIDERS.get(right_conf.provider).color
            right_text = " " * len(right_game) if blink_idx == right_index + 1 and not blink_on else right_game
            right_str = f"[{WHTE}{right_index + 1:>2}{RES}] - {right_color}{right_text}{RES}"
        else:
            right_str = ""

        lines.append(f"\t{left_str:<50}\t{right_str}")
    return "\n".join(lines)


if __name__ == "__main__":
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)

    print(f"{CLEAR}", end="")

    if platform.system() == "Darwin":
        game = game_selector() 
    else:
        print(render_games())
        games = list(GAME_CONFIGS)
        while True:
            try:
                choice = int(input("\n\tEnter the Fame of your choice: "))
                if 1 <= choice <= len(games):
                    game = games[choice - 1]
                    print(f"\n\tSelected: {WHTE}{game}{RES}")
                    break
                else:
                    print("\tInvalid choice. Try again.")
            except ValueError:
                print("\tPlease enter a valid number.")

    # print(f"\n\t>>> {RED}Select Source URL{RES} <<<\n")

    # source_urls = list(URLS)

    # for i, url in enumerate(source_urls, start=1):
    #     print(f"\t[{WHITE}{i}{RES}] - {"":>1} {'helpslot' if 'helpslot' in url else 'slimeserveahead'} ({url})")

    # while True:
    #     try:
    #         choice = int(input("\n\tEnter the source URL of your choice: "))
    #         if 1 <= choice <= len(source_urls):
    #             url = source_urls[choice - 1]
    #             print(f"\n\tSelected: {url}")
    #             break
    #         else:
    #             print("\tInvalid choice. Try again.")
    #     except ValueError:
    #         print("\tPlease enter a valid number.")
    
    url = next((url for url in URLS if 'helpslot' in url), None)
    termios.tcflush(sys.stdin, termios.TCIFLUSH)

    print(f"\n\n\t{BLNK}{DGRY}>>> Select Casino <<<{RES}\n")

    casinos = list(CASINOS)

    for i, casino in enumerate(casinos, start=1):
        print(f"\t[{WHTE}{i}{RES}]  - {casino}")

    while True:
        try:
            choice = int(input("\n\tEnter the Casino of your choice: "))
            if 1 <= choice <= len(casinos):
                casino = casinos[choice - 1]
                print(f"\n\tSelected: {WHTE}{casino}{RES}")
                break
            else:
                print("\tInvalid choice. Try again.")
        except ValueError:
            print("\tPlease enter a valid number.")

    dual_slots = int(input(f"\n\n\tEnter number of slots: "))

    print("\n\n\t...Starting real-time jackpot monitor. Press Ctrl+C to stop.\n")
    
    state = AutoState()
    settings = configure_game(game=game, casino=casino, dual_slots=dual_slots)

    spin_queue = Queue()
    spin_thread = threading.Thread(target=spin, daemon=True)
    spin_thread.start()

    session_id = 1 if casino == "JLJL9" else 2 if casino == "Bingo Plus" else 3 if casino == "Casino Plus" else 4

    alert_queue = Queue()
    alert_thread = threading.Thread(target=play_alert, daemon=True)
    alert_thread.start()
    alert_queue.put((None, game))

    driver = setup_driver(session_id)
    fetch_html_via_selenium(driver, game, url) # Load once at the start
    atexit.register(driver.quit)

    monitor_thread = threading.Thread(target=monitor_game_info, args=(driver,game,), daemon=True)
    monitor_thread.start()
    # threading.Thread(target=monitor_game_info, args=(driver,game,), daemon=True).start()
    # threading.Thread(target=keyboard, args=(settings,), daemon=True).start()
    # threading.Thread(target=mouse, daemon=True).start()
    
    try:
        while True:
            # your main thread logic, e.g., key listeners or UI updates
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\t[EXIT] Main program interrupted.")