#!/usr/bin/env .venv/bin/python

import json, os, platform, pyautogui, random, re, requests, subprocess, sys, time, threading
from dataclasses import dataclass, field
from datetime import datetime
from queue import Queue as ThQueue, Empty
from pynput.keyboard import Listener as KeyboardListener, Key, KeyCode
# from pynput.mouse import Listener as MouseListener, Button
from config import (datetime_now, GAME_CONFIGS, DEFAULT_GAME_CONFIG, API_CONFIG, API_URL, VPS_IP, BREAKOUT_FILE, DATA_FILE, SCREEN_POS, LEFT_SLOT_POS, RIGHT_SLOT_POS, DEFAULT_VOICE, SPIN_DELAY_RANGE, TIMEOUT_DELAY_RANGE, PROVIDERS, DEFAULT_PROVIDER_PROPS, URLS, CASINOS, 
                    LRED, LBLU, LCYN, LYEL, LMAG, LGRE, LGRY, RED, MAG, YEL, CYN, BLU, WHTE, BLRED, BLYEL, BLGRE, BLMAG, BLBLU, BLCYN, BYEL, BMAG, BCYN, BWHTE, DGRY, BLNK, CLEAR, RES)


@dataclass
class AutoState:
    spin: bool = False
    auto_spin: bool = True
    turbo: bool = True
    feature: bool = None
    auto_play_menu: bool = False
    widescreen: bool = False
    provider: str = None

    auto_mode: bool = False
    dual_slots: bool = False
    split_screen: bool = False
    left_slot: bool = False
    right_slot: bool = False
    forever_spin: bool = False
    # hotkeys: bool = True
    # running: bool = True
    # pressing: bool = False
    # clicking: bool = False
    # current_key: str = None
    # move: bool = False
    # auto_play: bool = False

    breakout: dict = field(default_factory=dict)
    is_breakout: bool = False
    is_delta_breakout: bool = False
    is_reversal: bool = False
    bet: int = 0
    bet_lvl: str = None
    last_spin: str = None
    last_trend: str = None
    last_pull_delta: float = 0.0
    prev_pull_delta: float = 0.0
    curr_color: str = None
    prev_jackpot_val: float = 0.0
    prev_10m: float = 0.0
    prev_1hr: float = 0.0
    last_slot: str = None
    non_stop: bool = False
    elapsed: int = 0
    last_time: int = 0
    new_10m: float = 0.0
    new_jackpot_val: float = 0.0


@dataclass
class GameSettings:
    sleep_times: dict

def get_sleep_times(auto_play_menu: bool=False):
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

def configure_game(game: str, api_server: str, breakout: dict, auto_mode: bool=False, dual_slots: bool=False, split_screen: bool=False, left_slot: bool=False, right_slot: bool=False, forever_spin: bool=False):
    state.breakout = breakout
    state.auto_mode = auto_mode
    state.dual_slots = dual_slots
    state.split_screen = split_screen
    state.left_slot = left_slot
    state.right_slot = right_slot
    state.forever_spin = forever_spin

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

def extract_game_data(data: dict) -> dict:
    return {
        "name": data.get("name"),
        "jackpot_meter": data.get("value"),
        "color": "green" if data.get("up") else "red",
        "history": {
            "10m": data.get("min10"),
            "1h": data.get("hr1"),
            "3h": data.get("hr3"),
            "6h": data.get("hr6")
        }
    }

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

def compare_data(prev: dict, current: dict):
    state.curr_color = current['color']

    slots = ["left", "right"]
    bet_level = None
    result = None
    bear_score = 0
    percent = f"{LGRY}%{RES}"

    border = f"{'-' * 32}"
    margin_left = len(str(border).expandtabs().strip()) - 2
    padding = margin_left - len(str(PROVIDERS.get(provider).provider).expandtabs().strip()) - 1
    slot_mode = f"{RED}dual{RES}" if state.dual_slots else f"{LBLU}split screen{RES}" if state.split_screen else f"{BLU}left{RES}" if state.left_slot else f"{MAG}right{RES}" if state.right_slot else f"{DGRY}single{RES}"

    banner = f'''\t♦️  {border}  ♠️
        \t{BCYN}{game.upper()}{RES}
        🃏\t{LGRY}{PROVIDERS.get(provider).provider}{RES}{' ' * padding}🎰
        \t{BLGRE}Slot{RES}: {slot_mode}
        \t{BLGRE}Mode{RES}: {CYN}{'auto' if state.auto_mode else 'manual'}{RES}
        ♣️  {border}  ♥️'''
    
    current_jackpot = pct(current['jackpot_meter'])
    jackpot_bar = get_jackpot_bar(current_jackpot, current['color'])
    is_breakout = False
    is_breakout_delta = False
    state.is_breakout = False
    state.is_delta_breakout = False
    lowest_low = state.breakout["lowest_low"]
    lowest_low_delta = state.breakout["lowest_low_delta"]

    if prev and 'jackpot_meter' in prev: 
        prev_jackpot = pct(prev['jackpot_meter'])
        delta = round(current_jackpot - prev_jackpot, 2)
        colored_delta = f"{LRED}{pct(delta)}{RES}" if delta < 0 else f"{LGRE}{delta}{RES}"
        sign = "+" if delta > 0 else ""
        diff = f"({YEL}Prev{RES}: {prev_jackpot}{percent} {LMAG}Δ{RES}: {sign}{colored_delta}{percent})"

        print(f"\n\n\t\t⏰ {f"{LBLU}{datetime_now().strftime('%I:%M:%S %p')}{LGRY} {datetime_now().strftime('%a')}{RES}"}")
        print(f"{banner}")
        print(f"\n\t🎰 {BLMAG}Jackpot Meter{RES}: {BLRED if current_jackpot < prev_jackpot else BLGRE}{current_jackpot}{percent} {diff}")
        print(f"\n\t{jackpot_bar} {BLRED}{current_jackpot}{RES}{percent}  ✅\n") if current_jackpot < prev_jackpot else \
            print(f"\n\t{jackpot_bar} {BLGRE}{current_jackpot}{RES}{percent}  ❌\n")
    else:
        print(f"\n\n\t\t⏰ {f"{LBLU}{datetime_now().strftime('%I:%M:%S %p')}{LGRY} {datetime_now().strftime('%a')}{RES}"}")
        print(f"{banner}")
        print(f"\n\t🎰 {BLMAG}Jackpot Meter{RES}: {current_jackpot}{percent}")
        print(f"\n\t{jackpot_bar} {current_jackpot}{percent}\n")

    for index, (period, value) in enumerate(current['history'].items()):
        old_value = prev['history'].get(period) if prev else None
        state.prev_jackpot_val = pct(prev['jackpot_meter']) if prev else None
        state.prev_10m = pct(prev['history'].get('10m')) if prev else None
        state.prev_1hr = pct(prev['history'].get('1h')) if prev else None
        colored_value = f"{LRED}{pct(value)}{RES}" if pct(value) < 0 else f"{LGRE}{pct(value)}{RES}"
        diff = ""

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
                    new_delta_10m = delta

                    updated = False

                    if lowest_low <= 0 and new_num < lowest_low:
                        lowest_low = round(new_num, 2)
                        state.breakout["lowest_low"] = lowest_low
                        is_breakout = True
                        state.is_breakout = True
                        alert_queue.put((None, "break_out"))
                        updated = True

                    if lowest_low_delta <= 0 and delta < lowest_low_delta:
                        lowest_low_delta = round(delta, 2)
                        state.breakout["lowest_low_delta"] = lowest_low_delta
                        is_breakout_delta = True
                        state.is_delta_breakout = True
                        alert_queue.put((None, "delta_break_out"))
                        updated = True

                    if updated:
                        save_breakout_memory(game, lowest_low, lowest_low_delta)
                elif index == 1 and new_num_10m is not None and old_num_10m is not None and new_delta_10m is not None:
                    h10, h1 = pct(new_num_10m), pct(new_num)
                    ph10, ph1 = pct(old_num_10m), pct(old_num)

                    old_delta_10m = state.last_pull_delta
                    state.last_pull_delta = new_delta_10m
                    new_delta_10m_1h = h10 - h1
                    old_delta_10m_1h = ph10 - ph1

                    delta_shift = new_delta_10m - old_delta_10m
                    delta_shift_analysis = new_delta_10m < old_delta_10m and old_delta_10m != 0
                    delta_shift_decision = new_delta_10m < 0
                    delta_shift_10m_1h = new_delta_10m_1h - old_delta_10m_1h
                    delta_shift_analysis_10m_1h = new_delta_10m_1h < old_delta_10m_1h and old_delta_10m_1h != 0
                    delta_shift_decision_10m_1h = new_delta_10m_1h < 0

                    score = 0
                    trend = list()
                    reversal = False
                    state.is_reversal = False

                    # ✅ 1. Check for directional reversal: Strong signal
                    # if (h10 < 0 < h1) or (h10 > 0 > h1):
                    if h10 < 0 < h1 or h10 > 0 > h1:
                        trend.append("Reversal Potential")
                        score += 2

                    # ✅ 2. Sharp shift in pull momentum: Medium-strong signal
                    if abs(delta_shift_10m_1h) > 20:
                        trend.append("Strong Pull Surge")
                        score += 2

                    # ✅ 3. Pull strength weakening: Negative signal
                    if abs(new_delta_10m_1h) < abs(old_delta_10m_1h) and old_delta_10m_1h != 0:
                        trend.append(f"Weakening Pull {LMAG}Δ{RES} 👎")
                        score -= 1
                        bear_score -= 1 if h10 < ph10 and new_delta_10m < 0 else bear_score

                    # ✅ 4. Low jackpot movement but big delta shift: Hidden pressure
                    if abs(current_jackpot - prev_jackpot) < 0.05 and abs(delta_shift_10m_1h) > 15:
                        trend.append(f"Hidden Pull {LGRE}({RES}No Visible/Low Jackpot, High {LMAG}Δ{RES}{LGRE}){RES}")
                        score += 1

                    # ✅ 5. Confirm with consistent bear power
                    if old_delta_10m != 0 and new_delta_10m < old_delta_10m and new_delta_10m < 0 and h10 < ph10:
                        new_delta_10m
                        trend.append("Consistent Bear Pressure")
                        score += 1
                        bear_score += 1 if h10 < ph10 and new_delta_10m < 0 else bear_score
                    elif old_delta_10m!= 0 and new_delta_10m >= old_delta_10m:
                        trend.append("Weak Pull 👎")
                        score -= 1
                        bear_score -= 1 if h10 < ph10 and new_delta_10m < 0 else bear_score

                    # ✅ 6. Very Strong Pull
                    if h10 <= -50 or new_delta_10m <= -50 or delta_shift <= -50 and h10 < ph10:
                        trend.append("Very Strong Bearish Pull")
                        score += 3
                        bear_score += 2 if h10 < ph10 and new_delta_10m < 0 else bear_score

                    # ✅ 7. Reversal
                    if prev['color'] == 'green' and current['color'] == 'red': #and current_jackpot - prev_jackpot
                        trend.append(f"{BLNK}{BLRED}R {WHTE}E {BLBLU}V {BLYEL}E {BLMAG}R {BLGRE}S {LGRY}A {BLCYN}L  🚀🚀{RES}")
                        reversal = True
                        state.is_reversal = True
                        score += 2
                        bear_score += 1 if h10 < ph10 and new_delta_10m < 0 else bear_score

                    # ✅ 8. Check for bet high
                    if current['color'] == 'red' and current_jackpot <= prev_jackpot and h10 < ph10:
                        trend.append("Intense Bearish Pull")
                        score += 2

                    # ✅ 0. Check for bet max
                    if current['color'] == 'red' and current_jackpot < prev_jackpot and (current_jackpot - prev_jackpot) < -0.03 and h10 < ph10:
                        trend.append("Extreme Bearish Pull")
                        score += 3

                    # ✅ 10. Check for neutralization
                    if not trend:
                        trend.append("Neutral")

                    alert_queue.put((None, "Reversal!")) if reversal else None

                    result = {
                        'new_delta_10m': round(new_delta_10m, 2),
                        'old_delta_10m': round(old_delta_10m, 2),
                        'new_delta_10m_1h': round(new_delta_10m_1h, 2),
                        'old_delta_10m_1h': round(old_delta_10m_1h, 2),
                        'delta_shift': round(delta_shift, 2),
                        'delta_shift_analysis': delta_shift_analysis,
                        'delta_shift_decision': delta_shift_decision,
                        'delta_shift_10m_1h': round(delta_shift_10m_1h, 2),
                        'delta_shift_analysis_10m_1h': delta_shift_analysis_10m_1h,
                        'delta_shift_decision_10m_1h': delta_shift_decision_10m_1h,
                        'pull_score': score,
                        'pull_trend': trend
                    }

                    if old_delta_10m != 0 and h10 < ph10 and delta_shift_decision:
                        if score >= 7 and h10 <= -50 and new_delta_10m <= -50 and delta_shift <= -50 and delta_shift_10m_1h <= -50:
                            bet_level = "max"
                        elif score >= 5 and h10 <= -20 and new_delta_10m <= -20 and delta_shift <= -20 and delta_shift_10m_1h <= -20:
                            bet_level = "high"
                        elif score >= 2:
                            bet_level = "mid"
                        elif score >= 0:
                            bet_level = "low"
                        else:
                            bet_level = None

                        # AUTO SPIN
                        # if state.auto_mode and bet_level in [ "max", "high" ] and score >= 5:
                        #     if state.dual_slots:
                        #         pyautogui.press('space')
                        #         spin_queue.put((bet_level, None, slots[0]))
                        #         spin_queue.put((bet_level, None, slots[1]))
                        #         time.sleep(random.randint(*SPIN_DELAY_RANGE))
                        #         spin_queue.put((bet_level, None, slots[0]))
                        #         time.sleep(random.randint(*SPIN_DELAY_RANGE))
                        #         spin_queue.put((bet_level, None, slots[1]))
                        #     elif state.left_slot:
                        #         spin_queue.put((bet_level, None, slots[0]))
                        #         time.sleep(random.randint(*SPIN_DELAY_RANGE))
                        #         if score >= 6:
                        #             spin_queue.put((bet_level, None, slots[0]))
                        #             time.sleep(random.randint(*SPIN_DELAY_RANGE))
                        #         if score >= 7:
                        #             bet_queue.put((bet_level, True, slots[0]))
                        #             time.sleep(random.randint(*SPIN_DELAY_RANGE))
                        #             spin_queue.put((bet_level, None, slots[0]))
                        #             time.sleep(random.randint(*SPIN_DELAY_RANGE))
                        #         if score >= 8:
                        #             bet_queue.put((bet_level, True, slots[0]))
                        #             time.sleep(random.randint(*SPIN_DELAY_RANGE))
                        #             spin_queue.put((bet_level, None, slots[0]))
                        #     elif state.right_slot:
                        #         spin_queue.put((bet_level, None, slots[1]))
                        #         time.sleep(random.randint(*SPIN_DELAY_RANGE))
                        #         if score >= 6:
                        #             spin_queue.put((bet_level, None, slots[1]))
                        #             time.sleep(random.randint(*SPIN_DELAY_RANGE))
                        #         if score >= 7:
                        #             bet_queue.put((bet_level, True, slots[1]))
                        #             time.sleep(random.randint(*SPIN_DELAY_RANGE))
                        #             spin_queue.put((bet_level, None, slots[1]))
                        #             time.sleep(random.randint(*SPIN_DELAY_RANGE))
                        #         if score >= 8:
                        #             bet_queue.put((bet_level, True, slots[1]))
                        #             time.sleep(random.randint(*SPIN_DELAY_RANGE))
                        #             spin_queue.put((bet_level, None, slots[1]))
                        #     else:
                        #         # pyautogui.press('space')
                        #         # time.sleep(3)
                        #         # spin(bet_level=bet_level, chosen_spin=None)
                        #         spin_queue.put((bet_level, None, None))
                        # elif score < 5 and state.auto_mode:
                        #     if state.dual_slots:
                        #         bet_queue.put((bet_level, True, slots[0]))
                        #         time.sleep(random.randint(*SPIN_DELAY_RANGE))
                        #         bet_queue.put((bet_level, True, slots[1]))
                        #     elif state.left_slot:
                        #         bet_queue.put((bet_level, True, slots[0]))
                        #     elif state.right_slot:
                        #         bet_queue.put((bet_level, True, slots[1]))
                        

        print(f"\t{CYN}⏱{RES} {LYEL}{period}{RES}:  {colored_value}{percent} {diff}") if period == "10m" and pct(value) >= 0 else \
            print(f"\t{CYN}⏱{RES} {LYEL}{period}{RES}: {colored_value}{percent} {diff}") if period == "10m" and pct(value) < 0 else \
            print(f"\t{CYN}⏱{RES} {LYEL}{period}{RES}:   {colored_value}{percent} {diff}") if pct(value) >= 0 else \
            print(f"\t{CYN}⏱{RES} {LYEL}{period}{RES}:  {colored_value}{percent} {diff}")

    print(f"\n\t🐻 Bear Score: {BWHTE}{bear_score}{RES}")
    if bear_score >= 2:
        print("\n\t✅ Bearish Momentum Detected")
    else:
        print("\n\t❌ Not Enough Bearish Momentum")

    if result is not None:
        state.prev_pull_delta = result.get('old_delta_10m')

        pull_score = result.get('pull_score', 0)

        if pull_score >= 8 and bet_level == "max":
            trend_strength = "💥💥💥 Extreme Pull"
        elif pull_score >= 7 and bet_level in [ "max", "high" ]:
            trend_strength = "🔥🔥 Intense Pull"
        elif pull_score >= 6 and bet_level in [ "max", "high" ]:
            trend_strength = "☄️ Very Strong Pull"
        elif pull_score >= 5:
            trend_strength = "🔴 Stronger Pull"
        elif pull_score >= 4:
            trend_strength = "🟠 Strong Pull"
        elif pull_score >= 2:
            trend_strength = "🟡 Moderate Pull"
        elif pull_score >= 1:
            trend_strength = "🟤 Weak Pull"
        elif pull_score >= 0:
            trend_strength = "⚪ Neutral"
        else:
            trend_strength = "❓ Invalid"

        print(f"\n\t💤 Pull Score: {BLCYN}{trend_strength}{RES} [ {BMAG}{pull_score}{RES} ]")
        state.last_trend = f"{re.sub(r'[^\x00-\x7F]+', '', trend_strength)} Score {pull_score}"
        alert_queue.put((None, "pull_trend_score")) if state.last_trend is not None else None

        for idx, pull_trend in enumerate(result.get('pull_trend')):
            print("\n\t💤 Pull Trend: ") if idx == 0 else None
            print(f"\t\t{BWHTE}{pull_trend}{RES}") if pull_trend else None

        print(f"\n\t🧲 Delta{LMAG}Δ{RES} Pull Power ({LGRY}Current & Prev [10m]{RES}): {BLRED if result.get('new_delta_10m') < 0 else BLGRE}{result.get('new_delta_10m')}{RES} | {BLRED if result.get('old_delta_10m') < 0 else BLGRE}{result.get('old_delta_10m')}{RES}") 
        print(f"\t🧪 Delta{LMAG}Δ{RES} Shift ({LGRY}Diff Current - Prev [10m]{RES}): {BLRED if result.get('delta_shift') < 0 else BLGRE}{result.get('delta_shift')}{RES}")
        print(f"\t🧪 Delta{LMAG}Δ{RES} Shift ({LGRY}Analysis [10m]{RES}): {MAG}Strong{RES} Pull  ✅") if result.get('delta_shift_analysis') else \
            print(f"\t🧪 Delta{LMAG}Δ{RES} Shift ({LGRY}Analysis [10m]{RES}): {MAG}Weak{RES} Pull  ❌")
        print(f"\t🧪 Delta{LMAG}Δ{RES} Shift ({LGRY}Decision [10m]{RES}): {BMAG}{'Very Strong' if result.get('delta_shift') <= -50 else 'Stronger' if result.get('delta_shift') <= -20 else 'Strong'}{RES} Pull  ✅") if result.get('delta_shift_decision') else \
            print(f"\t🧪 Delta{LMAG}Δ{RES} Shift ({LGRY}Decision [10m]{RES}): {BMAG}{'Very Weak' if result.get('delta_shift') >= 50 else 'Weaker' if result.get('delta_shift') >= 20 else 'Weak'}{RES} Pull  ❌")
            
        print(f"\n\t📊 Delta{LMAG}Δ{RES} Trend Change Power ({LGRY}Current & Prev [10m_1h]{RES}): {BLRED if result.get('new_delta_10m_1h') < 0 else BLGRE}{result.get('new_delta_10m_1h')}{RES} | {BLRED if result.get('old_delta_10m_1h') < 0 else BLGRE}{result.get('old_delta_10m_1h')}{RES}")
        print(f"\t🧪 Delta{LMAG}Δ{RES} Shift ({LGRY}Diff Current - Prev [10m_1h]{RES}): {BLRED if result.get('delta_shift_10m_1h') < 0 else BLGRE}{result.get('delta_shift_10m_1h')}{RES}")
        print(f"\t🧪 Delta{LMAG}Δ{RES} Shift ({LGRY}Analysis [10m_1h]{RES}): {LRED}🐻 Bearish{RES} Power  ✅") if result.get('delta_shift_analysis_10m_1h') else \
            print(f"\t🧪 Delta{LMAG}Δ{RES} Shift ({LGRY}Analysis [10m_1h]{RES}): {LGRE}🐂 Bullish{RES} Power  ❌")
        print(f"\t🧪 Delta{LMAG}Δ{RES} Shift ({LGRY}Decision [10m_1h]{RES}): {BMAG}{'Very Strong' if result.get('delta_shift_10m_1h') <= 50 else 'Strong' if result.get('delta_shift_10m_1h') <= 20 else 'Weak'}{RES} Bearish Pull Surge  🐻") if result.get('delta_shift_decision_10m_1h') else \
            print(f"\t🧪 Delta{LMAG}Δ{RES} Shift ({LGRY}Decision [10m_1h]{RES}): {BMAG}{'Very Strong' if result.get('delta_shift_10m_1h') >= 50 else 'Strong' if result.get('delta_shift_10m_1h') >= 20 else 'Weak'}{RES} Bullish Pull Surge  🐂")
        
        print(f"\n\t⚡ Break Out: {BLRED}{lowest_low}{RES}{percent} {'✅' if is_breakout else '❌'}") if lowest_low < 0 else \
            print(f"\n\t⚡ Break Out: {lowest_low}{percent} {'✅' if is_breakout else '❌'}")
        print(f"\t⚡ Break Out Delta{LMAG}Δ{RES}: {BLRED}{lowest_low_delta}{RES}{percent} {'✅' if is_breakout_delta else '❌'}") if lowest_low_delta < 0 else \
            print(f"\t⚡ Break Out Delta{LMAG}Δ{RES}: {lowest_low_delta}{percent} {'✅' if is_breakout_delta else '❌'}")

    print(f"\n\t\t{'💰 ' if current['color'] == 'red' else '⚠️ '}  {LYEL}Bet [{RES} {(BLNK) + (LRED if current['color'] == 'red' else LBLU)}{bet_level.upper()}{RES} {LYEL}]{RES}\n\n") if bet_level is not None else \
        print("\n\t\t🚫  Don't Bet!  🚫\n\n")

    alert_queue.put((bet_level, None))
    state.bet_lvl = bet_level
    state.last_trend = None

    # if state.auto_mode and state.dual_slots:
    #     slots = ["left", "right"]
    #     bet_queue.put((bet_level, True, slots[0]))
    #     time.sleep(random.randint(*SPIN_DELAY_RANGE))
    #     bet_queue.put((bet_level, True, slots[1]))

    # elif state.left_slot:
    #     bet_queue.put((bet_level, True, slots[0]))
    # elif state.right_slot:
    #     bet_queue.put((bet_level, True, slots[1]))
    
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

def get_jackpot_bar(percentage: float, color: str, bar_length: int=20) -> str:
    filled_blocks = round((percentage / 100) * bar_length)
    empty_blocks = bar_length - filled_blocks
    filled_bar = '🟩' if color == 'green' else '🟥'
    empty_bar = '⬛'
    color_code = LGRE if color == 'green' else LRED

    return f"{color_code}{filled_bar * filled_blocks}{RES}{empty_bar * empty_blocks}"

def pct(p):
    if p is None:
        return 0.0
    if isinstance(p, str) and '%' in p:
        return float(p.strip('%'))
    try:
        return float(p)
    except (TypeError, ValueError):
        return 0.0

def load_breakout_memory(game: str):
    today = datetime_now().strftime("%Y-%m-%d")

    if os.path.exists(BREAKOUT_FILE):
        with open(BREAKOUT_FILE, 'r') as f:
            data = json.load(f)
            day_data = data.get(today, {})
            return day_data.get(game.lower(), {"lowest_low": 0, "lowest_low_delta": 0})
    return {"lowest_low": 0, "lowest_low_delta": 0}

def save_breakout_memory(game: str, lowest_low: float, lowest_low_delta: float):
    today = datetime_now().strftime("%Y-%m-%d")
    data = {}

    if os.path.exists(BREAKOUT_FILE):
        with open(BREAKOUT_FILE, 'r') as f:
            data = json.load(f)

    if today not in data:
        data[today] = {}

    data[today][game.lower()] = {
        "lowest_low": lowest_low,
        "lowest_low_delta": lowest_low_delta
    }

    with open(BREAKOUT_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def play_alert(bet_level: str=None, say: str=None):
    if platform.system() == "Darwin":
        while not stop_event.is_set():
            try:
                # bet_level, say = alert_queue.get(timeout=10)
                bet_level, say = alert_queue.get_nowait()

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
                    # f"{state.last_spin}" if say is not None and say == "spin_type" else \
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
                if casino == "JLJL9":
                    voice = DEFAULT_VOICE
                elif casino == "Bingo Plus":
                    voice = "Trinoids"
                elif casino == "Casino Plus":
                    voice = "Kathy"
                elif casino == "Rollem 88":
                    voice = "Karen"
                else:
                    voice = "Nora"
                subprocess.run(["say", "-v", voice, "--", sound_file])

            except Empty:
                continue
            except Exception as e:
                print(f"\n\t[Alert Thread Error] {e}")
    else:
        pass

def countdown_timer(countdown_queue: ThQueue, seconds: int = 60):
    time_left = (seconds - round(time.time() % 60)) if state.prev_pull_delta != 0.0 else seconds

    while not stop_event.is_set() and state.elapsed == 0:
        if reset_event.is_set():
            time_left = (seconds - round(time.time() % 60)) if state.prev_pull_delta != 0.0 else seconds
            reset_event.clear()
            sys.stdout.write("\r" + " " * 80 + "\r")
            sys.stdout.flush()

        text = f"Betting Ends In" if state.bet_lvl is not None else f"Waiting For Next Iteration"
        mins, secs = divmod(time_left, 60)
        timer = f"\t⏳ {text}: {BLYEL}{mins:02d}{BLNK}{BWHTE}:{RES}{BLYEL}{secs:02d}{RES}  ( {CYN}{game}{RES} )"

        if time_left <= 10:
            timer = f"\t⏳ {text}: {BWHTE}... {BLNK}{BLRED}{secs}{RES}"
            if time_left == 10:
                alert_queue.put((None, f"{time_left} seconds remaining"))
                state.non_stop = False
            elif time_left <= 5:
                alert_queue.put((None, time_left))
                if time_left < 5 and not state.non_stop and state.curr_color == 'red':
                    # print('\n\tLucky Bet: curr_color >> ', state.curr_color)
                    # print('\n\tLucky Bet: prev_pull_delta >> ', state.prev_pull_delta)
                    # print('\n\tLucky Bet: non_stop >> ', state.non_stop)
                    if state.dual_slots and state.auto_mode:
                        slots = ["left", "right"]
                        random.shuffle(slots)
                        spin_queue.put((None, None, slots[0], False))
                        spin_queue.put((None, None, slots[1], False))
                        time.sleep(random.uniform(*SPIN_DELAY_RANGE))
                    elif not state.dual_slots and state.auto_mode:
                        spin_queue.put((None, None, None, False))
                        time.sleep(random.uniform(*SPIN_DELAY_RANGE))
        else:
            if not forever_spin and state.auto_mode and state.prev_pull_delta != 0.0:
                # print(f"\nstate.elapsed: {state.elapsed}")
                # print(f"\nstate.curr_color: {state.curr_color}")
                # print("data.get('min10') | state.prev_10m : ", data.get('min10'), state.prev_10m)
                get_delta = round(state.new_10m - state.prev_10m, 2)
                state.non_stop = (state.new_jackpot_val < state.prev_jackpot_val and state.new_10m < state.prev_10m and get_delta < state.prev_pull_delta) or state.is_breakout or state.is_delta_breakout or state.is_reversal or state.bet_lvl in [ "max", "high" ]
                # print('\n\tget_delta >> ', get_delta)
                # print('\n\tstate.prev_pull_delta >> ', state.prev_pull_delta)
                # print('\n\tstate.new_jackpot_val >> ', state.new_jackpot_val)
                # print('\n\tstate.prev_jackpot_val >> ', state.prev_jackpot_val)
                # print('\n\tstate.new_10m >> ', state.new_10m)
                # print('\n\tstate.prev_10m >> ', state.prev_10m)

                # print('\n\n\tNON STOP >> ', state.non_stop)
                # print('\n\tREVERSAL >> ', state.is_reversal)
                # print('\n\tBREAKOUT >> ', state.is_breakout)
                # print('\n\tDELTA BREAKOUT >> ', state.is_delta_breakout)
                # print('\n\tBET LVL >> ', state.bet_lvl)
                if get_delta <= -30 and state.new_10m <= -30 and state.curr_color == 'red':
                    alert_queue.put((None, "non stop spin"))
                    if state.dual_slots:
                        slots = ["left", "right"]
                        if state.last_slot is None:
                            random.shuffle(slots)
                            chosen_slot = slots
                        else:
                            other_slot = "right" if state.last_slot == "left" else "left"
                            chosen_slot = [other_slot, state.last_slot]

                        spin_queue.put((None, None, chosen_slot[0], False))
                        spin_queue.put((None, None, chosen_slot[1], True))

                        state.last_slot = chosen_slot[1] if state.non_stop else None
                        time.sleep(random.uniform(*TIMEOUT_DELAY_RANGE)) if state.non_stop else None
                    else:
                        spin_queue.put((None, None, None, True))
                        time.sleep(random.uniform(*TIMEOUT_DELAY_RANGE))
            elif forever_spin: # Forever Spin
                if state.dual_slots and state.curr_color == 'red':
                    alert_queue.put((None, "forever spin"))
                    slots = ["left", "right"]
                    if state.last_slot is None:
                        random.shuffle(slots)
                        chosen_slot = slots
                    else:
                        other_slot = "right" if state.last_slot == "left" else "left"
                        chosen_slot = [other_slot, state.last_slot]

                    spin_queue.put(("low", None, chosen_slot[0], False))
                    spin_queue.put(("low", None, chosen_slot[1], False))

                    state.last_slot = chosen_slot[1]
                else:
                    time.sleep(random.uniform(*SPIN_DELAY_RANGE))
                    spin_queue.put((None, None, None, False))

                state.last_slot = chosen_slot[1] if state.non_stop else None
                time.sleep(random.uniform(*SPIN_DELAY_RANGE)) if state.non_stop else None
            
        countdown_queue.put(time_left)
        sys.stdout.write(f"\r{timer.ljust(80)}")
        sys.stdout.flush()

        time.sleep(1)
        time_left -= 1

        # if time_left >= 55:
        #     # countdown_queue.put("Timeout")
        #     print("\n\n\t[⏰ Timer] Countdown finished.")
        #     break

def bet_switch(bet_level: str=None, extra_bet: bool=None, slot_position: str=None):
    while not stop_event.is_set():
        try:
            bet_level, extra_bet, slot_position = bet_queue.get(timeout=10)

            if state.left_slot or slot_position == "left":
                center_x, center_y = LEFT_SLOT_POS.get("center_x"), LEFT_SLOT_POS.get("center_y")
            elif state.right_slot or slot_position == "right":
                center_x, center_y = RIGHT_SLOT_POS.get("center_x"), RIGHT_SLOT_POS.get("center_y")
            else:
                center_x, center_y = SCREEN_POS.get("center_x"), SCREEN_POS.get("center_y")
                # pyautogui.moveTo(x=center_x, y=center_y) if state.auto_mode else None

            cx, cy = center_x, center_y
            x1, x2, y1, y2 = 0, SCREEN_POS.get("right_x"), 0, SCREEN_POS.get("bottom_y")
            
            if slot_position is not None and state.split_screen:
                pyautogui.doubleClick(x=cx, y=y2)
                time.sleep(1)
                if extra_bet and game.startswith("Fortune Gems"):
                    pyautogui.click(x=cx-228, y=cy-126)
                    pyautogui.doubleClick(x=cx-100, y=cy-126)
                    pyautogui.doubleClick(x=cx-100, y=cy-126)
                else:
                    pyautogui.moveTo(x=cx-100, y=cy-126)
                    
            alert_queue.put((None, "extra_bet")) if extra_bet else None
        except Empty:
            continue

def spin(bet_level: str=None, chosen_spin: str=None, slot_position: str=None, stop_spin: bool=False):
    while not stop_event.is_set():
        try:
            bet_level, chosen_spin, slot_position, stop_spin = spin_queue.get(timeout=10)

            spin_types = [ "normal", "spin_hold", "spam_spin", "board_spin", "board_spin_delay", "board_spin_turbo", "board_spin_tap", "auto_spin", "turbo_spin" ]
            spin_type = random.choice(spin_types) if chosen_spin is None else chosen_spin
            bet = 0
            # bet_values = list()
            # extra_bet = False
            # bet_reset = False
            # lucky_bet_value = 1
            
            center_x, center_y = SCREEN_POS.get("center_x"), SCREEN_POS.get("center_y")

            if state.dual_slots and state.split_screen and slot_position is not None:
                if slot_position == "left":
                    center_x, center_y = LEFT_SLOT_POS.get("center_x"), LEFT_SLOT_POS.get("center_y")
                elif slot_position == "right":
                    center_x, center_y = RIGHT_SLOT_POS.get("center_x"), RIGHT_SLOT_POS.get("center_y")

                # time.sleep(1) if state.auto_mode else None
                # pyautogui.doubleClick(x=center_x, y=center_y) if state.auto_mode else None

            cx, cy = center_x, center_y if game != "Super Rich" else center_y + 150
            x1, x2, y1, y2 = 0, SCREEN_POS.get("right_x"), 0, SCREEN_POS.get("bottom_y")

            if state.dual_slots and slot_position is not None:
                if state.split_screen:
                    pyautogui.doubleClick(x=cx, y=y2)
                    time.sleep(0.5)
                else:
                    # if state.last_slot is None: # FIRST SPIN
                    print('\n\tFirst Spin')
                    if slot_position == 'right': # spin right away, during first spin if 'LEFT'
                        pyautogui.keyDown('ctrl')
                        pyautogui.press('right')
                        pyautogui.keyUp('ctrl')
                        time.sleep(0.5)
                    # elif state.last_slot is not None:
                    #     print('\n\tLast Spin')
                    #     if state.non_stop:
                    #         if state.last_slot != slot_position:

                    #         if slot_position == 'right':
                    #             pyautogui.keyDown('ctrl')
                    #             pyautogui.press('right')
                    #             pyautogui.keyUp('ctrl')
                    #             time.sleep(0.5)


                    #     elif slot_position == 'left':
                    #         pyautogui.keyDown('ctrl')
                    #         pyautogui.press(slot_position)
                    #         pyautogui.keyUp('ctrl')
                    #         time.sleep(0.5)

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
                
            if spin_type == "normal_spin":  # optimize later for space or click dynamics
                if state.spin:
                    pyautogui.doubleClick(x=cx, y=cy + 315)
                else:
                    pyautogui.press('space')
            elif spin_type == "spin_hold":
                if slot_position is None and state.widescreen and provider in [ "JILI", "JFF", "R88" ]:
                    pyautogui.doubleClick(x=cx + 450, y=cy + 325)
                else:
                    pyautogui.doubleClick(x=cx, y=cy + 315)
                pyautogui.mouseDown()
                time.sleep(random.uniform(*SPIN_DELAY_RANGE))
                pyautogui.mouseUp()
            elif spin_type == "spam_spin":
                if slot_position is None and state.widescreen and provider in [ "JILI", "JFF", "R88" ]:
                    pyautogui.click(x=cx + 450, y=cy + 325)
                    pyautogui.click(x=cx + 450, y=cy + 325)
                    pyautogui.click(x=cx + 450, y=cy + 325)
                    pyautogui.click(x=cx + 450, y=cy + 325)
                    pyautogui.click(x=cx + 450, y=cy + 325)
                else:
                    pyautogui.click(x=cx, y=cy + 315)
                    pyautogui.click(x=cx, y=cy + 315)
                    pyautogui.click(x=cx, y=cy + 315)
                    pyautogui.click(x=cx, y=cy + 315)
                    pyautogui.click(x=cx, y=cy + 315)
                    pyautogui.click(x=cx, y=cy + 315)
                time.sleep(random.uniform(*SPIN_DELAY_RANGE))
            elif spin_type == "board_spin":  # Click confirm during first board spin    
                if provider in [ "JILI", "FC", "JFF", "R88" ]:
                    pyautogui.click(x=cx, y=cy)
                elif provider in [ "PG", "PP" ]:
                    pyautogui.press('space')
                    time.sleep(random.uniform(*SPIN_DELAY_RANGE))
                    pyautogui.click(x=cx, y=cy)
            elif spin_type == "board_spin_delay":
                if provider in [ "JILI", "FC", "JFF", "R88" ]:
                    pyautogui.moveTo(x=cx, y=cy)
                    pyautogui.mouseDown()
                    time.sleep(random.uniform(*SPIN_DELAY_RANGE))
                    pyautogui.mouseUp()
                elif provider in [ "PG", "PP" ]:
                    pyautogui.keyDown('space')
                    time.sleep(random.uniform(*SPIN_DELAY_RANGE))
                    pyautogui.keyUp('space')
            elif spin_type == "board_spin_turbo":
                if provider in [ "JILI", "FC", "JFF", "R88" ]:
                    pyautogui.doubleClick(x=cx, y=cy)
                elif provider in [ "PG", "PP" ]:
                    pyautogui.press('space')
                    pyautogui.click(x=cx, y=cy)
            elif spin_type == "board_spin_tap":
                if provider in [ "FC" ]:
                    pyautogui.moveTo(x=cx, y=cy)
                    pyautogui.mouseDown()
                    time.sleep(random.uniform(*SPIN_DELAY_RANGE))
                    pyautogui.mouseUp()
                    pyautogui.click(x=cx, y=cy)
                elif provider in [ "JILI", "PG", "PP", "JFF", "R88" ]:
                    pyautogui.keyDown('space')
                    time.sleep(random.uniform(*SPIN_DELAY_RANGE))
                    pyautogui.keyUp('space')
                    action = random.choice([
                        lambda: pyautogui.press('space'),
                        lambda: pyautogui.doubleClick(x=cx, y=cy),
                        lambda: pyautogui.click(x=cx, y=cy)
                    ]) if not state.spin else lambda: pyautogui.doubleClick(x=cx, y=cy + 315)
                    action()
            elif spin_type == "auto_spin":
                if slot_position is None and state.widescreen and provider in [ "JILI", "JFF", "R88" ]:
                    pyautogui.doubleClick(x=cx + 380, y=cy + 325)
                else:
                    action = random.choice([
                        lambda: pyautogui.press('space'),
                        lambda: pyautogui.doubleClick(x=cx, y=cy),
                        lambda: pyautogui.click(x=cx, y=cy)
                    ]) if not state.spin else lambda: pyautogui.doubleClick(x=cx, y=cy + 315)
                    action()
            elif spin_type == "turbo_spin":
                if slot_position is None and state.widescreen and provider in [ "JILI", "JFF", "R88" ]:
                    pyautogui.doubleClick(x=cx + 450, y=cy + 325)
                else:
                    action = random.choice([
                        lambda: pyautogui.press('space'),
                        lambda: pyautogui.doubleClick(x=cx, y=cy),
                        lambda: pyautogui.click(x=cx, y=cy)
                    ]) if not state.spin else lambda: pyautogui.doubleClick(x=cx, y=cy + 315)
                    action()

            # time.sleep(2) if chosen_spin != "turbo_spin" else time.sleep(1)
            time.sleep(1)

            if state.dual_slots and slot_position is not None:
                if state.split_screen:
                    if slot_position == "right":
                        cx, cy = LEFT_SLOT_POS.get("center_x"), LEFT_SLOT_POS.get("center_y")
                    elif slot_position == "left":
                        cx, cy = RIGHT_SLOT_POS.get("center_x"), RIGHT_SLOT_POS.get("center_y")
                    pyautogui.doubleClick(x=cx, y=y2)
                    time.sleep(0.5)
                else: # reset back to left only if slot is 'RIGHT' during last spin
                    if slot_position == 'right':
                        print('\n\tResetting to LEFT: ', slot_position)
                        pyautogui.keyDown('ctrl')
                        pyautogui.press('left')
                        pyautogui.keyUp('ctrl')
                        time.sleep(0.5)

            # BET RESET
            # if bet_reset and not is_lucky_bet:
            #     print('\nDEBUG (BET RESET) ...\n')
            #     pyautogui.click(x=random_x - 190, y=random_y + 325)
            #     pyautogui.click(x=random_x - 50, y=random_y + 250)
            #     time.sleep(1)

            alert_queue.put((None, f"{spin_type}"))

            print(f"\n\t\t*** {state.last_trend} ***") if state.last_trend is not None else None
            print(f"\n\t\tBet: {WHTE}{bet}{RES} ({BLNK}🌀{RES} {RED}{spin_type.replace('_', ' ').upper()}{RES})\n")
            print(f"\t\tSlot: {BLBLU}{slot_position}{RES}\n") if state.dual_slots or state.split_screen or state.left_slot or state.right_slot else None

            if stop_spin and not state.non_stop:
                break
        except Empty:
            continue

def get_game_data_from_local_api(game: str):
    request_from = random.choice(["H5", "H6"])

    try:
        response = requests.get(
            f"{api_server}/game",
            params={
                "name": game,
                "requestFrom": request_from
            }
        )

        json_data = response.json()

        # print(f"📡 Calling with requestFrom={request_from}")
        # print("RESPONSE >>", json_data)

        # Always return a tuple
        return json_data, request_from

    except Exception as e:
        print(f"❌ Error calling API: {e}")
        return {"error": str(e)}, request_from

def monitor_game_info(game: str, provider: str, url: str, data_queue: ThQueue):
    last_min10 = None

    while not stop_event.is_set():
        try:
            data, request_from = get_game_data_from_local_api(game)

            if data and "error" not in data:
                min10 = data.get("min10")
                if min10 != last_min10:
                    last_min10 = min10
                    state.non_stop = False
                    state.new_jackpot_val = data.get("value")
                    state.new_10m = data.get("min10")
                    state.last_time = round(data.get('last_updated') % 60)
                    print("\n\tstate.last_time | time_now >> ", state.last_time, round(time.time() % 60))
                    # spin_queue.put((None, None, None, True)) # test spin on data not working
                    data_queue.put(data)
                else:
                    alert_queue.put((None, "redundant data"))
                    # print(f"\n\t🛰️. Redundant Data From [{BWHTE}{request_from}{RES}] → Current{BLNK}{BLYEL}={RES}{MAG}{min10}{RES} | Prev{BLNK}{BLYEL}={RES}{MAG}{last_min10}{RES}")
            else:
                print(f"\n\t⚠️  Game '{game}' not found") if state.elapsed != 0 else None
                # subprocess.run(["bash", "api_restart.sh"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) if state.elapsed != 0 else None
        except Exception as e:
            print(f"🤖❌  {e}")

        time.sleep(0.5)

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

def game_selector():
    state = {
        "typed": "",
        "selected_idx": None,
        "blinking": True
    }

    command_queue = ThQueue()

    def blink_loop():
        blink_on = True
        while state["blinking"]:
            try:
                # Try to get new input from queue without blocking
                key_event = command_queue.get_nowait()
                if key_event == "EXIT":
                    state["blinking"] = False
                    break
                elif isinstance(key_event, str):
                    state["typed"] = key_event
            except Empty:
                pass

            print(f"{CLEAR}", end="")
            blink_id = int(state["typed"]) if state["typed"].isdigit() and 1 <= int(state["typed"]) <= len(GAME_CONFIGS) else None
            print(render_games(blink_idx=blink_id, blink_on=blink_on))
            print(f"\n\t{DGRY}>>> Select Game: {WHTE}{state['typed']}{RES}", end='', flush=True)

            blink_on = not blink_on
            time.sleep(0.5)

    def on_input(key):
        typed = state["typed"]
        if key == Key.backspace:
            typed = typed[:-1]
        elif key == Key.esc:
            print("\nCancelled.")
            command_queue.put("EXIT")
            return False
        elif key == Key.enter:
            if typed.isdigit() and 1 <= int(typed) <= len(GAME_CONFIGS):
                state['selected_idx'] = int(typed)
                command_queue.put("EXIT")
                return False
            else:
                typed = ""
        elif hasattr(key, 'char') and key.char and key.char.isdigit():
            typed += key.char

        command_queue.put(typed)

    blink_thread = threading.Thread(target=blink_loop, daemon=True)
    blink_thread.start()

    with KeyboardListener(on_press=on_input) as kb_listener:
        kb_listener.join()

    print(f"{CLEAR}", end="")
    print(render_games())
    if state['selected_idx']:
        game_name = list(GAME_CONFIGS.keys())[state['selected_idx'] - 1]
        print(f"\n\tSelected: {WHTE}{game_name.upper()}{RES}")
        blink_thread.join()
        return game_name
    
def render_games(blink_idx: int=None, blink_on: bool=True):
    print(f"\n\n\t📘 {MAG}SCATTER JACKPOT MONITOR{RES}\n\n")

    games = list(GAME_CONFIGS.items())
    half = (len(games) + 1) // 2
    lines = list()

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
    games = list(GAME_CONFIGS.items())
    url = next((url for url in URLS if 'helpslot' in url), None)

    # if platform.system() == "Darwin":
    #     game = game_selector()
    # else:
    print(render_games())
    while True:
        try:
            choice = int(input("\n\t🔔 Enter the Game of your choice: "))
            if 1 <= choice <= len(games):
                game = games[choice - 1][0]
                print(f"\n\tSelected: {WHTE}{game}{RES}")
                break
            else:
                print("\t⚠️  Invalid choice. Try again.")
        except ValueError:
            print("\t⚠️  Please enter a valid number.")

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
    
    provider = GAME_CONFIGS.get(game).provider

    print(f"\n\n\t{BLNK}{DGRY}🔔 Select Server{RES}\n")
    print("  ".join(f"\n\t[{WHTE}{i}{RES}] - {'Local' if 'localhost' in host else 'VPS'}" for i, host in enumerate(API_URL, start=1)))

    while True:
        user_input = input(f"\n\n\t🔔 Choose your server ({DGRY}default: 1{RES}): ").strip()
        
        if not user_input:
            api_server = API_URL[0]
            print("\t⚠️  Invalid input. Defaulting to Local network.")
            break
        elif user_input.isdigit():
            choice = int(user_input)
            if 1 <= choice <= len(API_URL):
                api_server = API_URL[choice - 1]
                print(f"\n\tSelected: {WHTE}{'Local' if 'localhost' in api_server else 'VPS'}{RES}")
                break
        else:
            api_server = API_URL[0]
            print("\t⚠️  Invalid input. Defaulting to Local network.")
            break

    if 'localhost' in api_server:
        pass
        # print(f"{os.getpid()}")
        # subprocess.run(["bash", "killall.sh", f"{os.getpid()}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # subprocess.run(["bash", "api_restart.sh"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(["bash", "flush_dns.sh"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        hostname = api_server.replace("https://", "").split('/')[0]
        result = subprocess.run(["dig", "+short", hostname], capture_output=True, text=True)
        resolved_ip = result.stdout.strip().split("\n")[0]

        # print(f"\n\tResolved IP: {resolved_ip}")
        # print(f"\tExpected VPS IP: {VPS_IP}")

        if resolved_ip != VPS_IP:
            print("\n\t❌  IP Mismatch! Change your QOS.. Exiting...\n")
            sys.exit(1)
        else:
            print("\n\t✅  IP Match!")

    print(f"\n\n\t{BLNK}{DGRY}🔔 Select Casino{RES}\n")

    casinos = list(CASINOS)

    for i, casino in enumerate(casinos, start=1):
        print(f"\t[{WHTE}{i}{RES}]  - {casino}")

    while True:
        user_input = input(f"\n\t🔔 Enter the Casino of your choice ({DGRY}default: 1{RES}): ").strip()
        
        if not user_input:
            casino = casinos[0]
            print(f"\n\tSelected default: {WHTE}{casino}{RES}")
            break
        elif user_input.isdigit():
            choice = int(user_input)
            if 1 <= choice <= len(casinos):
                casino = casinos[choice - 1]
                print(f"\n\tSelected: {WHTE}{casino}{RES}")
                break
            else:
                print(f"\t⚠️  Invalid number. Please select from 1 to {len(casinos)}.")
        else:
            print("\t⚠️  Invalid input. Please enter a number.")

    user_input = input(f"\n\n\tDo you want to enable {CYN}Auto Mode{RES} ❓ ({DGRY}y/N{RES}): ").strip().lower()
    auto_mode = user_input in ("y", "yes")
    dual_slots = False
    split_screen = False
    left_slot = right_slot = False
    forever_spin = False

    if auto_mode:
        user_input = input(f"\n\n\tDo you want to enable {CYN}Dual Slots{RES} ❓ ({DGRY}y/N{RES}): ").strip().lower()
        dual_slots = user_input in ("y", "yes")
        
        if dual_slots:
            user_input = input(f"\n\n\tDo you want to enable {CYN}Split Screen{RES} ❓ ({DGRY}y/N{RES}): ").strip().lower()
            split_screen = user_input in ("y", "yes")

            if split_screen:
                enable_left = input(f"\n\n\tDo you want to enable {BLU}Left Slot{RES} ❓ ({DGRY}y/N{RES}): ").strip().lower()
                left_slot = enable_left in ("y", "yes")

                if not left_slot:
                    enable_right = input(f"\n\n\tDo you want to enable {MAG}Right Slot{RES} ❓ ({DGRY}y/N{RES}): ").strip().lower()
                    right_slot = enable_right in ("y", "yes")

        user_input = input(f"\n\n\tDo you want to enable {CYN}Forever Spin{RES} ❓ ({DGRY}y/N{RES}): ").strip().lower()
        forever_spin = user_input in ("y", "yes")

    print(f"\n\n\t... {WHTE}Starting real-time jackpot monitor.\n\t    Press ({BLMAG}Ctrl+C{RES}{WHTE}) to stop.{RES}\n")

    # Register a game
    requests.post(f"{api_server}/register", json={'url': url, 'name': game, 'provider': provider})

    breakout = load_breakout_memory(game)

    state = AutoState()
    settings = configure_game(game, api_server, breakout, auto_mode, dual_slots, split_screen, left_slot, right_slot, forever_spin)

    stop_event = threading.Event()
    reset_event = threading.Event()

    alert_queue = ThQueue()
    bet_queue = ThQueue()
    data_queue = ThQueue()
    countdown_queue = ThQueue()
    spin_queue = ThQueue()
    
    alert_thread = threading.Thread(target=play_alert, daemon=True)
    bet_thread = threading.Thread(target=bet_switch, daemon=True)
    countdown_thread = threading.Thread(target=countdown_timer, args=(countdown_queue, 60,), daemon=True)
    monitor_thread = threading.Thread(target=monitor_game_info, args=(game, provider, url, data_queue,), daemon=True)
    spin_thread = threading.Thread(target=spin, daemon=True)

    alert_thread.start()
    bet_thread.start()
    countdown_thread.start()
    monitor_thread.start()
    spin_thread.start()

    state.elapsed = 0

    try:
        while True:
            try:
                reset_event.set() # Reset the countdown because data came in
                state.elapsed = 0  # Reset elapsed on data
                data = data_queue.get(timeout=60) # Wait for new data from monitor thread (max 60s)

                alert_queue.put((None, game))
                parsed_data = extract_game_data(data)
                all_data = load_previous_data()
                previous_data = all_data.get(game.lower())
                compare_data(previous_data, parsed_data)
                all_data[game.lower()] = parsed_data
                save_current_data(all_data)
            except Empty:
                state.elapsed += 1
                print(f"\n\t⚠️  No data received in {state.elapsed} {'seconds' if state.elapsed > 1 else 'second'}.")
                # if state.elapsed == 2:
                #     print('Restarting API Service...')
                #     subprocess.run(["bash", "api_restart.sh"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                # if state.elapsed >= 50:
                #     print("⚠️  No data received in 1 minute.")
                #     state.elapsed = 0  # Optional: reset or exit
            # Handle timeout signal from countdown
            # try:
            #     # result = countdown_queue.get()
            #     result = countdown_queue.get_nowait()
            #     # result = countdown_queue.get_nowait()
            #     if result == "Timeout":
            #         print("⏰ Timer expired.")
            #         state.elapsed += 1
            #         # stop everything if timer expires
            #         stop_event.set()
            #         break
            # except Empty:
            #     pass  # No timer event
    except KeyboardInterrupt:
        print("\n\n\t🤖❌  Main program interrupted.")
        stop_event.set()  # Stop all threads

    # requests.post(f"http://{API_CONFIG.get('host')}:{API_CONFIG.get('port')}/deregister", json={'url': url, 'name': game, 'provider': provider})
    requests.post(f"{api_server}/deregister", json={
        'url': url,
        'name': game,
        'provider': provider
    })
    
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)

    print("\n\n\t🤖❌  All threads shut down.")
