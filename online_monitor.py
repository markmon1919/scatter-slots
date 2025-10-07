#!/usr/bin/env .venv/bin/python

import aiofiles, asyncio, certifi, json, logging, math, os, platform, pyautogui, random, re, ssl, shutil, subprocess, sys, time, threading, websockets
import numpy as np
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from queue import Queue as ThQueue, Empty
from pynput.keyboard import Listener as KeyboardListener, Key, KeyCode
from trend import load_trend_memory
from config import (LOGS_PATH, LOG_LEVEL, GAME_CONFIGS, DEFAULT_GAME_CONFIG, API_URL, API_PORT, WS_URL, VPS_IP, VPS_DOMAIN, TREND_FILE, BREAKOUT_FILE, DATA_FILE, HELPSLOT_DATA_FILE, SCREEN_POS, LEFT_SLOT_POS, RIGHT_SLOT_POS, PING, VOICES, HOLD_DELAY_RANGE, SPIN_DELAY_RANGE, TIMEOUT_DELAY_RANGE, PROVIDERS, DEFAULT_PROVIDER_PROPS, URLS, 
                    LRED, LBLU, LCYN, LYEL, LMAG, LGRE, LGRY, RED, MAG, YEL, GRE, CYN, BLU, WHTE, BLRED, BLYEL, BLGRE, BLMAG, BLBLU, BLCYN, BYEL, BMAG, BCYN, BWHTE, DGRY, BLNK, CLEAR, RES)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


@dataclass
class AutoState:
    spin_btn: bool = False
    auto_spin: bool = True
    turbo: bool = True
    feature: bool = None
    auto_play_menu: bool = False
    widescreen: bool = False
    provider: str = None

    auto_mode: bool = False
    fast_mode: bool = False
    dual_slots: bool = False
    split_screen: bool = False
    left_slot: bool = False
    right_slot: bool = False
    # forever_spin: bool = False
    
    # hotkeys: bool = True
    # running: bool = True
    # pressing: bool = False
    # clicking: bool = False
    # current_key: str = None
    # move: bool = False
    # auto_play: bool = False

    breakout: dict = field(default_factory=dict)
    neutralize: bool = False
    is_low_breakout: bool = False
    is_low_delta_breakout: bool = False
    is_high_breakout: bool = False
    is_high_delta_breakout: bool = False
    is_reversal: bool = False
    is_reversal_potential: bool = False
    bet: int = 0
    bet_lvl: str = None
    extra_bet: bool = False
    last_spin: str = None
    last_trend: str = None
    interval: int = 0
    last_pull_delta: float = 0.0
    pull_delta: float = 0.0
    old_delta: float = 0.0
    # prev_pull_delta: float = 0.0
    prev_pull_score: int = 0
    prev_bear_score: int = 0
    pull_score: int = 0
    bear_score_inc: bool = False
    pull_score_inc: bool = False
    curr_color: str = None
    min10: float = 0.0
    last_min10: float = 0.0
    prev_jackpot_val: float = 0.0
    prev_10m: float = 0.0
    prev_1hr: float = 0.0
    last_slot: str = None
    non_stop: bool = False
    elapsed: int = 0
    last_time: Decimal = Decimal('0')
    current_color: str = None
    api_jackpot_delta: float = 0.0
    api_10m: float = 0.0
    api_1h: float = 0.0
    api_3h: float = 0.0
    new_jackpot_val: float = 0.0
    jackpot_signal: str = None
    # new_data: bool = False
    prev_helpslot_jackpot: float = 0.0
    api_major_pullback: bool = False
    helpslot_jackpot: float = 0.00
    helpslot_meter: str = None
    helpslot_jackpot_delta: float = 0.0
    helpslot_10m: float = 0.0
    helpslot_1h: float = 0.0
    helpslot_3h: float = 0.0
    # helpslot_6h: float = 0.0
    helpslot_major_pullback: bool = False
    extreme_pull: bool = False
    intense_pull: bool = False
    spike: bool = False
    pull_thresh: int = 0
    min10_thresh: int = 0

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

def configure_game(game: str, api_server: str, breakout: dict, auto_mode: bool=False, fast_mode: bool=False, dual_slots: bool=False, split_screen: bool=False, left_slot: bool=False, right_slot: bool=False):#, forever_spin: bool=False):
    state.breakout = breakout
    state.auto_mode = auto_mode
    state.fast_mode = fast_mode
    state.dual_slots = dual_slots
    state.split_screen = split_screen
    state.left_slot = left_slot
    state.right_slot = right_slot
    # state.forever_spin = forever_spin

    config = GAME_CONFIGS.get(game, DEFAULT_GAME_CONFIG)
    (
        state.spin_btn,
        state.auto_spin,
        state.turbo,
        state.feature,
        state.auto_play_menu,
        state.widescreen,
        state.provider
    ) = config

    return GameSettings(get_sleep_times(state.auto_play_menu))

def setup_driver():
    options = Options()
    if platform.system() != "Darwin" or os.getenv("IS_DOCKER") == "1":
        options.binary_location = "/opt/google/chrome/chrome"
        options.add_argument('--disable-dev-shm-usage')

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")

    service = Service(shutil.which("chromedriver"))
    return webdriver.Chrome(service=service, options=options)

# -------------------------
# Fetch HTML via Selenium
# -------------------------
def fetch_html(driver: webdriver.Chrome, url: str, game: str, provider: str):
    driver.get(url)
    time.sleep(1)
    
    try:
        search_box = driver.find_element(By.ID, "van-search-1-input")
        # driver.execute_script("arguments[0].value = '';", search_box) # use only if loop multiple games
        search_box.send_keys(game)
        time.sleep(1)
        
        if provider == "JILI":
            search_btn = driver.find_element(By.CLASS_NAME, "van-search__action")
            search_btn.click()
            time.sleep(1)
        else:
            provider_items = driver.find_elements(By.CSS_SELECTOR, ".provider-item")
            for item in provider_items:
                try:
                    img_elem = item.find_element(By.CSS_SELECTOR, ".provider-icon img")
                    img_url = img_elem.get_attribute("src")
                    
                    if PROVIDERS.get(provider).img_url in img_url.lower():
                        item.click()
                        break
                except Exception:
                    continue
    except Exception:
        pass
        
    time.sleep(1)
    return driver.page_source

def fetch_game_data(driver: webdriver.Chrome, game: str, fetch_queue: ThQueue) -> list:
    while not stop_event.is_set():
        now_time = Decimal(str(time.time()))
        
        card = driver.find_element(By.CSS_SELECTOR, ".game-block")
        
        try:
            name = card.find_element(By.CSS_SELECTOR, ".game-title").text.strip()
            if name != game:
                return None
                
            value_text = card.find_element(By.CSS_SELECTOR, ".progress-value").text.strip()
            value = float(value_text.replace("%", ""))
            
            # if state.helpslot_jackpot == value:
            #     logger.info(f"\t{RED}Skipped{RES}:  {name} {state.helpslot_jackpot} -- {value}")
            #     return None
            
            if state.helpslot_jackpot != value:
                create_hs_time_log(value, now_time)
                state.helpslot_jackpot = value
                
                progress_bar_elem = card.find_element(By.CSS_SELECTOR, ".progress-bar")
                bg = progress_bar_elem.value_of_css_property("background-color").lower()
                up = "red" if "255, 0, 0" in bg else "green"

                state.helpslot_meter = up

                history = {}
                history_tags = card.find_elements(By.CSS_SELECTOR, ".game-info-list .game-info-item")
                
                for item in history_tags:
                    label = item.find_element(By.CSS_SELECTOR, ".game-info-label").text.strip().rstrip(":").replace(" ", "").lower()
                    period_elem = item.find_element(By.CSS_SELECTOR, ".game-info-value")
                    period_text = period_elem.text.strip()
                    period = float(period_text.replace("%", ""))
                    history[label] = period
                    
                    if label == "10min":
                        state.helpslot_10m = period
                    if label == "1hr":
                        state.helpslot_1h = period
                    if label == "3hrs":
                        state.helpslot_3h = period
                    if label == "6hrs":
                        state.helpslot_6h = period
                    
                game_data = {
                    "name": game, 
                    "jackpot_value": value, 
                    "meter_color": up, 
                    **history
                }
                fetch_queue.put(game_data)
        except Exception as e:
            logger.info(f"🤖❌  {e}")
                # except Exception:
                #     continue
        # except Exception:
        #     pass
        time.sleep(0.5)

    # return game

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

def load_previous_data(data_source: str):
    filename = DATA_FILE if data_source == "api" else HELPSLOT_DATA_FILE if data_source == "helpslot" else None

    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_current_data(data_source: str, data: dict):
    filename = DATA_FILE if data_source == "api" else HELPSLOT_DATA_FILE if data_source == "helpslot" else None

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def create_hs_time_log(jackpot_value: float, timestamp: Decimal):
    if not os.path.exists(LOGS_PATH):
        os.makedirs(LOGS_PATH, exist_ok=True)
    
    spike = float(jackpot_value - state.prev_helpslot_jackpot)
    state.prev_helpslot_jackpot = jackpot_value
    
    if spike == state.prev_helpslot_jackpot == jackpot_value:
        return

    # if state.auto_mode and abs(spike) >= 1.0:
    #     # if spin_in_progress.is_set():
    #     #     spin_in_progress.clear()
    #     # threading.Thread(target=spin, args=(False, False, False,), daemon=True).start()
        
    #     # spin(False, False, True, False,)
    #     # state.spike = True
    #     # alert_queue.put(f"spike {int(timestamp % 60)} spike mode ON")
        
    #     if not state.fast_mode:
    #         spin(False, False, True, False,)
    #         state.fast_mode = True
    #         alert_queue.put(f"spike {int(timestamp % 60)} fast mode ON")
        
    # # if state.auto_mode and state.spike and abs(spike) <= 0.5:
    # #     spin(False, False, True, False,)
    # #     state.spike = False
    # #     alert_queue.put(f"spike mode OFF")
            
    # if state.auto_mode and state.fast_mode and abs(spike) <= 0.5:
    #     state.fast_mode = False
    #     alert_queue.put(f"fast mode OFF")
                
    csv_file = os.path.join(LOGS_PATH, f"{game.strip().replace(' ', '_').lower()}_log-hs.csv")
    write_header = not os.path.exists(csv_file)
    
    fieldnames = ["timestamp", "jackpot_meter","jackpot_delta"]
    row = {
        "timestamp": datetime.fromtimestamp(float(timestamp)).strftime("%Y-%m-%d %I:%M:%S %p"),
        "jackpot_meter": jackpot_value,
        "jackpot_delta": spike
    }
        
    with open(csv_file, "a", newline="") as f:
        if write_header:
            f.write(",".join(fieldnames) + "\n")
        f.write(",".join(str(row.get(fn, "")) for fn in fieldnames) + "\n")
        
async def create_time_log(data: dict):
    if not os.path.exists(LOGS_PATH):
        os.makedirs(LOGS_PATH, exist_ok=True)
        
    # # 🔑 check if same as last written
    # if last_logged.get("min10") == data.get("min10"):
    #     return  # skip writing identical row
    
    # # update last_logged cache
    # last_logged["min10"] = data.get("min10")
    
    # csv_file = os.path.join(LOGS_PATH, f"{data.get("name").strip().replace(' ', '_').lower()}_log.csv")
    csv_file = os.path.join(LOGS_PATH, f"{game.strip().replace(' ', '_').lower()}_log.csv")
    write_header = not os.path.exists(csv_file)
    
    fieldnames = [ "timestamp", "jackpot_meter", "color", "10m", "1h", "3h", "6h", "10m_delta", "prev_10m", "prev_10m_delta", "interval" ]
    row = {
        "timestamp": datetime.fromtimestamp(float(data.get("last_updated", time.time()))).strftime("%Y-%m-%d %I:%M:%S %p"),
        "jackpot_meter": data.get("value"),
        "color": "green" if data.get("up") is True else "red",
        "10m": data.get("min10"),
        "1h": data.get("hr1"),
        "3h": data.get("hr3"),
        "6h": data.get("hr6"),
        "10m_delta": data.get("10m_delta"),
        "prev_10m": data.get("prev_min10"),
        "prev_10m_delta": data.get('prev_10m_delta'),
        "interval": data.get('interval')
    }
        
    async with aiofiles.open(csv_file, mode="a", newline="") as f:
        if write_header:
            await f.write(",".join(fieldnames) + "\n")
        await f.write(",".join(str(row.get(fn, "")) for fn in fieldnames) + "\n")

def compare_data(prev: dict, current: dict, prev_helpslot: dict, helpslot_data: dict):
    # today = datetime.fromtimestamp(time.time())
    today = datetime.fromtimestamp(float(state.last_time))
    state.curr_color = current['color']
    slots = ["left", "right"]
    bet_level = None
    result = None
    bear_score = 0
    percent = f"{LGRY}%{RES}"

    border = "-" * 44
    content_width = len(border) + 8
    title_text = f"{LGRY}{re.sub(r'\\s*\\(.*?\\)', '', game).upper()}{RES} ({PROVIDERS.get(provider).color}{PROVIDERS.get(provider).provider}{RES})"
    slot_mode = "dual" if state.dual_slots else "split screen" if state.split_screen else "left" if state.left_slot else "right" if state.right_slot else "single"

    slot_mode_colored = (
        f"{RED}dual{RES}" if slot_mode == "dual"
        else f"{LBLU}split screen{RES}" if slot_mode == "split screen"
        else f"{BLU}left{RES}" if slot_mode == "left"
        else f"{MAG}right{RES}" if slot_mode == "right"
        else f"{DGRY}single{RES}"
    )

    slot_text = f"{BLGRE}Slot{RES}: {slot_mode_colored}"
    auto_mode_text = f"{BLGRE}Mode{RES}: {BLCYN if auto_mode else CYN}{'auto' if auto_mode else 'manual'}{RES}"
    fast_mode_text = f"{BLGRE}Fast Mode{RES}: {BLCYN if fast_mode else CYN}{'ON' if auto_mode else 'OFF'}{RES}"

    def visible_length(s):
        return len(re.sub(r"\x1b\[[0-9;]*m", "", s))

    def center_text(text, width):
        pad_total = max(width - visible_length(text), 0)
        pad_left = pad_total // 2
        pad_right = pad_total - pad_left
        return " " * pad_left + text + " " * pad_right

    icons_len = (visible_length("🃏") + visible_length("🎰")) * 2
    space_for_text = (content_width - 1) - icons_len

    slot_text_centered = center_text(slot_text, space_for_text)
    slot_line = f"🃏{slot_text_centered}🎰"

    time_line = f"\n\n\n\t\t{LMAG}[{DGRY}{f"{today.second}.{today.microsecond // 10000:02d}"} ms{WHTE}]{RES}  ⏰  {BYEL}{today.strftime('%I')}{BWHTE}:{BYEL}{today.strftime('%M')}{BWHTE}:{BLYEL}{today.strftime('%S')} {LBLU}{today.strftime('%p')} {MAG}{today.strftime('%a')}{RES}"
    time_line_centered = center_text(time_line, content_width)

    banner_lines = [
        f"♦️  {border}  ♠️",
        center_text(title_text, content_width),
        slot_line,
        center_text(auto_mode_text, content_width - 1),
        center_text(fast_mode_text, content_width - 1),
        f"♣️  {border}  ♥️",
    ]

    banner_lines.insert(0, time_line_centered)
    banner = "\n\t".join(banner_lines)
    banner = "\t" + banner

    # time_data = load_previous_time_data()

    # if time_data and time_data.get('10m'):
    #     jackpot_10m = time_data['10m'].get('jackpot_meter', 'None')
    #     color_10m = LRED if time_data['10m'].get('color') == 'red' else LGRE
    #     colored_time_data_jackpot_10m = f"{YEL}10m {color_10m}{jackpot_10m}{RES}"
    # else:
    #     colored_time_data_jackpot_10m = f"{YEL}10m {DGRY}No History{RES}"

    # if time_data and time_data.get('1h'):
    #     jackpot_1h = time_data['1h'].get('jackpot_meter', 'None')
    #     color_1h = LRED if time_data['1h'].get('color') == 'red' else LGRE
    #     colored_time_data_jackpot_1h = f"{YEL}1h {color_1h}{jackpot_1h}{RES}"
    # else:
    #     colored_time_data_jackpot_1h = f"{YEL}1h {DGRY}No History{RES}"

    # if time_data and time_data.get('3h'):
    #     jackpot_3h = time_data['3h'].get('jackpot_meter', 'None')
    #     color_3h = LRED if time_data['3h'].get('color') == 'red' else LGRE
    #     colored_time_data_jackpot_3h = f"{YEL}3h {color_3h}{jackpot_3h}{RES}"
    # else:
    #     colored_time_data_jackpot_3h = f"{YEL}3h {DGRY}No History{RES}"

    # if time_data and time_data.get('6h'):
    #     jackpot_6h = time_data['6h'].get('jackpot_meter', 'None')
    #     color_6h = LRED if time_data['6h'].get('color') == 'red' else LGRE
    #     colored_time_data_jackpot_6h = f"{YEL}6h {color_6h}{jackpot_6h}{RES}"
    # else:
    #     colored_time_data_jackpot_6h = f"{YEL}6h {DGRY}No History{RES}"



    # if helpslot_data and helpslot_data.get('jackpot_value') and helpslot_data.get('meter_color'):
    #     helpslot_jackpot = pct(helpslot_data.get('jackpot_value'))
    #     helpslot_jackpot_bar = get_jackpot_bar(helpslot_jackpot, helpslot_data.get('meter_color'))
    #     helpslot_signal = f"{LRED}⬇{RES}" if helpslot_data.get('meter_color') == "red" else f"{LGRE}⬆{RES}" if helpslot_data.get('meter_color') == "green" else f"{LCYN}◉{RES}"
    #     bet_value = f"{LRED}HIGH{RES}" if helpslot_jackpot >= 80 else f"{LGRE}LOW{RES}" if helpslot_jackpot <= 20 else f"{LYEL}MID{RES}"

    # if helpslot_data and helpslot_data.get('jackpot_value') and helpslot_data.get('meter_color') and helpslot_data.get('10min'):
    #     history_10m = pct(helpslot_data.get('10min', 'None'))
    #     color_10m = LRED if history_10m < 0 else LGRE if history_10m > 0 else LCYN
    #     colored_helpslot_data_history_10m = f"{YEL}10m {color_10m}{history_10m}{RES}"
    # else:
    #     colored_helpslot_data_history_10m = f"{YEL}10m {DGRY}No History{RES}"

    # if helpslot_data and helpslot_data.get('jackpot_value') and helpslot_data.get('meter_color') and helpslot_data.get('1hr'):
    #     history_1h = pct(helpslot_data.get('1hr', 'None'))
    #     color_1h = LRED if history_1h < 0 else LGRE if history_1h > 0 else LCYN
    #     colored_helpslot_data_history_1h = f"{YEL}1h {color_1h}{history_1h}{RES}"
    # else:
    #     colored_helpslot_data_history_1h = f"{YEL}1h {DGRY}No History{RES}"

    # if helpslot_data and helpslot_data.get('jackpot_value') and helpslot_data.get('meter_color') and helpslot_data.get('3hrs'):
    #     history_3h = pct(helpslot_data.get('3hrs', 'None'))
    #     color_3h = LRED if history_3h < 0 else LGRE if history_3h > 0 else LCYN
    #     colored_helpslot_data_history_3h = f"{YEL}3h {color_3h}{history_3h}{RES}"
    # else:
    #     colored_helpslot_data_history_3h = f"{YEL}3h {DGRY}No History{RES}"

    # if helpslot_data and helpslot_data.get('jackpot_value') and helpslot_data.get('meter_color') and helpslot_data.get('6hrs'):
    #     history_6h = pct(helpslot_data.get('6hrs', 'None'))
    #     color_6h = LRED if history_6h < 0 else LGRE if history_6h > 0 else LCYN
    #     colored_helpslot_data_history_6h = f"{YEL}6h {color_6h}{history_6h}{RES}"
    # else:
    #     colored_helpslot_data_history_6h = f"{YEL}6h {DGRY}No History{RES}"
    
    current_jackpot = pct(current['jackpot_meter'])
    jackpot_bar = get_jackpot_bar(current_jackpot, current['color'])
    
    # state.pull_score = 0
    state.extreme_pull = False
    state.intense_pull = False
    state.is_reversal = False
    state.is_reversal_potential = False
    state.neutralize = False
    is_low_breakout = False
    is_low_breakout_delta = False
    is_high_breakout = False
    is_high_breakout_delta = False
    state.is_low_breakout = False
    state.is_low_delta_breakout = False
    state.is_high_breakout = False
    state.is_high_delta_breakout = False
    state.api_major_pullback = False
    
    if current_jackpot >= 99:
        # alert_queue.put(f"API Jackpot {current_jackpot}")
        if state.api_jackpot_delta < 0:
        # if current['color'] == "red" or current_jackpot == 100:
            state.api_major_pullback = True
            alert_queue.put(f"API Major Pullback")
            
    state.current_color = current['color']
    state.new_jackpot_val = current_jackpot
    state.api_10m = pct(current['history'].get('10m'))
    state.api_1h = pct(current['history'].get('1h'))
    state.api_3h = pct(current['history'].get('3h'))
    state.new_6h = pct(current['history'].get('6h'))
    lowest_low = state.breakout["lowest_low"]
    lowest_low_delta = state.breakout["lowest_low_delta"]
    highest_high = state.breakout["highest_high"]
    highest_high_delta = state.breakout["highest_high_delta"]

    logger.info(f"{banner}")

    if helpslot_data and "jackpot_value" in helpslot_data:
        helpslot_jackpot = pct(helpslot_data.get('jackpot_value'))
        state.helpslot_major_pullback = False
        if helpslot_jackpot >= 88:
            # alert_queue.put(f"Helpslot Jackpot {helpslot_jackpot}")
            if pct(helpslot_data.get('10min')) >= 0:
                state.helpslot_major_pullback = True
                # alert_queue.put(f"Helpslot Major Pullback")
        
        helpslot_jackpot_bar = get_jackpot_bar(helpslot_jackpot, helpslot_data.get('meter_color'))
        # helpslot_signal = f"{LRED}⬇{RES}" if helpslot_data.get('meter_color') == "red" else f"{LGRE}⬆{RES}" if helpslot_data.get('meter_color') == "green" else f"{LCYN}◉{RES}"

        bet_value = f"{LRED}HIGH{RES}" if helpslot_jackpot >= 80 else f"{LGRE}LOW{RES}" if helpslot_jackpot <= 20 else f"{LYEL}MID{RES}"
        
        history_10m = pct(helpslot_data.get('10min', 'None'))
        color_10m = RED if history_10m < 0 else GRE if history_10m > 0 else LCYN
        colored_helpslot_data_history_10m = f"{color_10m}{history_10m}{RES}"
    # else:
    #     colored_helpslot_data_history_10m = f"{YEL}10m {DGRY}No History{RES}"

    # if helpslot_data and helpslot_data.get('jackpot_value') and helpslot_data.get('meter_color') and helpslot_data.get('1hr'):
        history_1h = pct(helpslot_data.get('1hr', 'None'))
        color_1h = RED if history_1h < 0 else GRE if history_1h > 0 else LCYN
        colored_helpslot_data_history_1h = f"{color_1h}{history_1h}{RES}"
    # else:
    #     colored_helpslot_data_history_1h = f"{YEL}1h {DGRY}No History{RES}"

    # if helpslot_data and helpslot_data.get('jackpot_value') and helpslot_data.get('meter_color') and helpslot_data.get('3hrs'):
        history_3h = pct(helpslot_data.get('3hrs', 'None'))
        color_3h = RED if history_3h < 0 else GRE if history_3h > 0 else LCYN
        colored_helpslot_data_history_3h = f"{color_3h}{history_3h}{RES}"
    # else:
    #     colored_helpslot_data_history_3h = f"{YEL}3h {DGRY}No History{RES}"

    # if helpslot_data and helpslot_data.get('jackpot_value') and helpslot_data.get('meter_color') and helpslot_data.get('6hrs'):
        history_6h = pct(helpslot_data.get('6hrs', 'None'))
        color_6h = RED if history_6h < 0 else GRE if history_6h > 0 else LCYN
        colored_helpslot_data_history_6h = f"{color_6h}{history_6h}{RES}"
    # else:
    #     colored_helpslot_data_history_6h = f"{YEL}6h {DGRY}No History{RES}"
        
    if prev_helpslot and "jackpot_value" in prev_helpslot:
        prev_helpslot_jackpot = pct(prev_helpslot.get('jackpot_value'))
        # state.prev_jackpot_val = prev_jackpot
        helpslot_jackpot_delta = round(helpslot_jackpot - prev_helpslot_jackpot, 2)
        state.helpslot_jackpot_delta = helpslot_jackpot_delta
        helpslot_colored_delta = f"{RED if helpslot_jackpot_delta < 0 else GRE}{pct(helpslot_jackpot_delta)}{RES}"
        helpslot_sign = f"{GRE}+{RES}" if helpslot_jackpot_delta > 0 else ""
        # signal = f"{LRED}⬇{RES}" if helpslot_jackpot < prev_helpslot_jackpot else f"{LGRE}⬆{RES}" if helpslot_jackpot > prev_helpslot_jackpot else f"{LCYN}◉{RES}"
        # helpslot_signal = f"{LRED}⬇{RES}" if helpslot_data.get('meter_color') == "red" else f"{LGRE}⬆{RES}" if helpslot_data.get('meter_color') == "green" else f"{LCYN}◉{RES}"
        helpslot_signal = f"{LRED}⬇{RES}" if helpslot_jackpot < prev_helpslot_jackpot else f"{LGRE}⬆{RES}" if helpslot_jackpot > prev_helpslot_jackpot else f"{LCYN}◉{RES}"
        helpslot_diff = f"({YEL}Prev{DGRY}:{RES} {GRE}{prev_helpslot_jackpot}{RES}{percent}{DGRY}, {LMAG}Δ{DGRY}: {helpslot_sign}{helpslot_colored_delta}{percent})"

        # colored_value = f"{RED if pct(value) < 0 else GRE if pct(value) > 0 else CYN}{pct(value)}{RES}"
        prev_history_10m = pct(prev_helpslot.get('10min', 'None'))
        prev_history_1h = pct(prev_helpslot.get('1hr', 'None'))
        prev_history_3h = pct(prev_helpslot.get('3hrs', 'None'))
        prev_history_6h = pct(prev_helpslot.get('6hrs', 'None'))

        prev_color_10m = RED if prev_history_10m < 0 else GRE if prev_history_10m > 0 else LCYN
        prev_colored_helpslot_data_history_10m = f"{prev_color_10m}{prev_history_10m}{RES}"
        helpslot_delta_10m = round(history_10m - prev_history_10m, 2)
        helpslot_colored_delta_10m = f"{RED if helpslot_delta_10m < 0 else GRE if helpslot_delta_10m > 0 else CYN}{pct(helpslot_delta_10m)}{RES}"
        helpslot_sign_10m = f"{GRE}+{RES}" if helpslot_delta_10m > 0 else ""
        helpslot_signal_10m = f"{LRED}▼{RES}" if history_10m < prev_history_10m else f"{LGRE}▲{RES}" if history_10m > prev_history_10m else f"{LCYN}◆{RES}"
        helpslot_diff_10m = f"({YEL}Prev{DGRY}: {prev_colored_helpslot_data_history_10m}{percent}{DGRY}, {LMAG}Δ{DGRY}: {helpslot_sign_10m}{helpslot_colored_delta_10m}{percent})"

        prev_color_1h = RED if prev_history_1h < 0 else GRE if prev_history_1h > 0 else LCYN
        prev_colored_helpslot_data_history_1h = f"{prev_color_1h}{prev_history_1h}{RES}"
        helpslot_delta_1h = round(history_1h - prev_history_1h, 2)
        helpslot_colored_delta_1h = f"{RED if helpslot_delta_1h < 0 else GRE if helpslot_delta_1h > 0 else CYN}{pct(helpslot_delta_1h)}{RES}"
        helpslot_sign_1h = f"{GRE}+{RES}" if helpslot_delta_1h > 0 else ""
        helpslot_signal_1h = f"{LRED}▼{RES}" if history_1h < prev_history_1h else f"{LGRE}▲{RES}" if history_1h > prev_history_1h else f"{LCYN}◆{RES}"
        helpslot_diff_1h = f"({YEL}Prev{DGRY}: {prev_colored_helpslot_data_history_1h}{percent}{DGRY}, {LMAG}Δ{DGRY}: {helpslot_sign_1h}{helpslot_colored_delta_1h}{percent})"

        prev_color_3h = RED if prev_history_3h < 0 else GRE if prev_history_3h > 0 else LCYN
        prev_colored_helpslot_data_history_3h = f"{prev_color_3h}{prev_history_3h}{RES}"
        helpslot_delta_3h = round(history_3h - prev_history_3h, 2)
        helpslot_colored_delta_3h = f"{RED if helpslot_delta_3h < 0 else GRE if helpslot_delta_3h > 0 else CYN}{pct(helpslot_delta_3h)}{RES}"
        helpslot_sign_3h = f"{GRE}+{RES}" if helpslot_delta_3h > 0 else ""
        helpslot_signal_3h = f"{LRED}▼{RES}" if history_3h < prev_history_3h else f"{LGRE}▲{RES}" if history_3h > prev_history_3h else f"{LCYN}◆{RES}"
        helpslot_diff_3h = f"({YEL}Prev{DGRY}: {prev_colored_helpslot_data_history_3h}{percent}{DGRY}, {LMAG}Δ{DGRY}: {helpslot_sign_3h}{helpslot_colored_delta_3h}{percent})"
        
        prev_color_6h = RED if prev_history_6h < 0 else GRE if prev_history_6h > 0 else LCYN
        prev_colored_helpslot_data_history_6h = f"{prev_color_6h}{prev_history_6h}{RES}"
        helpslot_delta_6h = round(history_6h - prev_history_6h, 2)
        helpslot_colored_delta_6h = f"{RED if helpslot_delta_6h < 0 else GRE if helpslot_delta_6h > 0 else CYN}{pct(helpslot_delta_6h)}{RES}"
        helpslot_sign_6h = f"{GRE}+{RES}" if helpslot_delta_6h > 0 else ""
        helpslot_signal_6h = f"{LRED}▼{RES}" if history_6h < prev_history_6h else f"{LGRE}▲{RES}" if history_6h > prev_history_6h else f"{LCYN}◆{RES}"
        helpslot_diff_6h = f"({YEL}Prev{DGRY}: {prev_colored_helpslot_data_history_6h}{percent}{DGRY}, {LMAG}Δ{DGRY}: {helpslot_sign_6h}{helpslot_colored_delta_6h}{percent})"

        logger.info(f"\n\t🎰 {BLCYN}Helpslot Meter{RES}: {RED if helpslot_jackpot < prev_helpslot_jackpot else GRE}{helpslot_jackpot}{percent} {helpslot_diff} ({bet_value}{RES})")
        logger.info(f"\n\t{helpslot_jackpot_bar} {helpslot_signal}\n")

        logger.info(f"\t{CYN}⏱{RES} {LYEL}10m{RES}: {colored_helpslot_data_history_10m}{percent} {helpslot_diff_10m} {helpslot_signal_10m}") if pct(history_10m) < 0 else \
            logger.info(f"\t{CYN}⏱{RES} {LYEL}10m{RES}:  {colored_helpslot_data_history_10m}{percent} {helpslot_diff_10m} {helpslot_signal_10m}")
        
        logger.info(f"\t{CYN}⏱{RES} {LYEL}1h{RES}:  {colored_helpslot_data_history_1h}{percent} {helpslot_diff_1h} {helpslot_signal_1h}") if pct(history_1h) < 0 else \
            logger.info(f"\t{CYN}⏱{RES} {LYEL}1h{RES}:   {colored_helpslot_data_history_1h}{percent} {helpslot_diff_1h} {helpslot_signal_1h}")
        
        logger.info(f"\t{CYN}⏱{RES} {LYEL}3h{RES}:  {colored_helpslot_data_history_3h}{percent} {helpslot_diff_3h} {helpslot_signal_3h}") if pct(history_3h) < 0 else \
            logger.info(f"\t{CYN}⏱{RES} {LYEL}3h{RES}:   {colored_helpslot_data_history_3h}{percent} {helpslot_diff_3h} {helpslot_signal_3h}")

        logger.info(f"\t{CYN}⏱{RES} {LYEL}6h{RES}:  {colored_helpslot_data_history_6h}{percent} {helpslot_diff_6h} {helpslot_signal_6h}") if pct(history_6h) < 0 else \
            logger.info(f"\t{CYN}⏱{RES} {LYEL}6h{RES}:   {colored_helpslot_data_history_6h}{percent} {helpslot_diff_6h} {helpslot_signal_6h}")
    else:
        
        logger.info(f"\n\t🎰 {BLCYN}Helpslot Meter{RES}: {RED if helpslot_data.get('meter_color') == "red" else GRE}{helpslot_jackpot}{RES}{percent} ({bet_value}{RES})")
        logger.info(f"\n\t{helpslot_jackpot_bar}\n")

        logger.info(f"\t{CYN}⏱{RES} {LYEL}10m{RES}: {colored_helpslot_data_history_10m}{percent}") if pct(history_10m) < 0 else \
            logger.info(f"\t{CYN}⏱{RES} {LYEL}10m{RES}:  {colored_helpslot_data_history_10m}{percent}")
        
        logger.info(f"\t{CYN}⏱{RES} {LYEL}1h{RES}:  {colored_helpslot_data_history_1h}{percent}") if pct(history_1h) < 0 else \
            logger.info(f"\t{CYN}⏱{RES} {LYEL}1h{RES}:   {colored_helpslot_data_history_1h}{percent}")
        
        logger.info(f"\t{CYN}⏱{RES} {LYEL}3h{RES}:  {colored_helpslot_data_history_3h}{percent}") if pct(history_3h) < 0 else \
            logger.info(f"\t{CYN}⏱{RES} {LYEL}3h{RES}:   {colored_helpslot_data_history_3h}{percent}")

        logger.info(f"\t{CYN}⏱{RES} {LYEL}6h{RES}:  {colored_helpslot_data_history_6h}{percent}") if pct(history_6h) < 0 else \
            logger.info(f"\t{CYN}⏱{RES} {LYEL}6h{RES}:   {colored_helpslot_data_history_6h}{percent}")

    if prev and 'jackpot_meter' in prev:
        prev_jackpot = pct(prev['jackpot_meter'])
        state.prev_jackpot_val = prev_jackpot
        delta = round(current_jackpot - prev_jackpot, 2)
        state.api_jackpot_delta = delta
        colored_delta = f"{RED if delta < 0 else GRE}{pct(delta)}{RES}"
        sign = f"{GRE}+{RES}" if delta > 0 else ""
        signal = f"{LRED}⬇{RES}" if current_jackpot < prev_jackpot else f"{LGRE}⬆{RES}" if current_jackpot > prev_jackpot else f"{LCYN}◉{RES}"
        diff = f"({YEL}Prev{DGRY}:{RES} {GRE}{prev_jackpot}{RES}{percent}{DGRY}, {LMAG}Δ{DGRY}: {sign}{colored_delta}{percent})"

        # logger.info(f"{banner}")
        # logger.info(f"\n\t🎰 {BLCYN}Helpslot Meter{RES}: {RED if helpslot_data.get('meter_color') == "red" else GRE}{helpslot_jackpot}{percent} ({bet_value})")
        # logger.info(f"\n\t{helpslot_jackpot_bar} {helpslot_signal} {colored_helpslot_data_history_10m} {colored_helpslot_data_history_1h} {colored_helpslot_data_history_3h} {colored_helpslot_data_history_6h}")
        logger.info(f"\n\t🎰 {BLMAG}Jackpot Meter{RES}: {RED if current_jackpot < prev_jackpot else GRE}{current_jackpot}{percent} {diff}")
        # logger.info(f"\n\t{jackpot_bar} {signal} {colored_time_data_jackpot_10m} {colored_time_data_jackpot_1h} {colored_time_data_jackpot_3h} {colored_time_data_jackpot_6h} {DGRY}History{RES}\n")
        logger.info(f"\n\t{jackpot_bar} {signal}{RES}\n")
    else:
        # logger.info(f"{banner}")
        # logger.info(f"\n\t🎰 {BLCYN}Helpslot Meter{RES}: {RED if helpslot_data.get('meter_color') == "red" else GRE}{helpslot_jackpot}{percent} ({bet_value}{RES})")
        # logger.info(f"\n\t{helpslot_jackpot_bar} {helpslot_signal} {colored_helpslot_data_history_10m} {colored_helpslot_data_history_1h} {colored_helpslot_data_history_3h} {colored_helpslot_data_history_6h}")
        logger.info(f"\n\t🎰 {BLMAG}Jackpot Meter{RES}: {RED if current['color'] == 'red' else GRE}{current_jackpot}{RES}{percent}")
        # logger.info(f"\n\t{jackpot_bar} {LCYN}◉{RES} {colored_time_data_jackpot_10m} {colored_time_data_jackpot_1h} {colored_time_data_jackpot_3h} {colored_time_data_jackpot_6h} {DGRY}History{RES}\n")
        logger.info(f"\n\t{jackpot_bar} {LCYN}◉{RES}\n")


    for index, (period, value) in enumerate(current['history'].items()):
        old_value = prev['history'].get(period) if prev else None
        state.prev_10m = pct(prev['history'].get('10m')) if prev else None
        state.prev_1hr = pct(prev['history'].get('1h')) if prev else None
        colored_value = f"{RED if pct(value) < 0 else GRE if pct(value) > 0 else CYN}{pct(value)}{RES}"
        diff = ""
        signal = ""

        if old_value is not None:
            colored_old_value = f"{RED if pct(old_value) < 0 else GRE if pct(old_value) > 0 else CYN}{pct(old_value)}{RES}"
            new_num = pct(value)
            old_num = pct(old_value)

            if new_num is not None and old_num is not None:
                delta = round(new_num - old_num, 2)
                colored_delta = f"{RED if delta < 0 else GRE if delta > 0 else CYN}{pct(delta)}{RES}"
                sign = f"{GRE}+{RES}" if delta > 0 else ""
                signal = f"{LRED}▼{RES}" if new_num < old_num else f"{LGRE}▲{RES}" if new_num > old_num else f"{LCYN}◆{RES}"
                diff = f"({YEL}Prev{DGRY}: {colored_old_value}{percent}{DGRY}, {LMAG}Δ{DGRY}: {sign}{colored_delta}{percent})"

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
                        is_low_breakout = True
                        state.is_low_breakout = True
                        # alert_queue.put("low_break_out")
                        updated = True

                    if lowest_low_delta <= 0 and delta < lowest_low_delta:
                        lowest_low_delta = round(delta, 2)
                        state.breakout["lowest_low_delta"] = lowest_low_delta
                        is_low_breakout_delta = True
                        state.is_low_delta_breakout = True
                        # alert_queue.put("low_delta_break_out")
                        updated = True

                    if highest_high >= 0 and new_num > highest_high:
                        highest_high = round(new_num, 2)
                        state.breakout["highest_high"] = highest_high
                        is_high_breakout = True
                        state.is_high_breakout = True
                        state.is_reversal_potential = True
                        # alert_queue.put("high_break_out")
                        updated = True

                    if highest_high_delta >= 0 and delta > highest_high_delta:
                        highest_high_delta = round(delta, 2)
                        state.breakout["highest_high_delta"] = highest_high_delta
                        is_high_breakout_delta = True
                        state.is_high_delta_breakout = True
                        state.is_reversal_potential = True
                        # alert_queue.put("high_delta_break_out")
                        updated = True

                    if updated:
                        save_breakout_memory(game, lowest_low, lowest_low_delta, highest_high, highest_high_delta)
                elif index == 1 and new_num_10m is not None and old_num_10m is not None and new_delta_10m is not None:
                    h10, h1 = pct(new_num_10m), pct(new_num)
                    ph10, ph1 = pct(old_num_10m), pct(old_num)
                    
                    old_delta_10m = state.old_delta
                    state.old_delta = new_delta_10m
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

                    # ✅ 1. Check for directional reversal: Strong signal
                    # optimize to add prev value h1 > 0 and h1 < ph1
                    if ph10 > 0 and h10 < 0 and h1 > 0 and current['color'] == 'green':
                        trend.append("Reversal Potential")
                        state.is_reversal_potential = True 
                        score += 2
                    elif ph10 < 0 and h10 > 0 and h1 < 0 and current['color'] == 'red':
                        trend.append("Reversal Potential")
                        score -= 2
                    # if h10 < 0 < h1 or h10 > 0 > h1:
                    #     trend.append("Reversal Potential")
                    #     state.is_reversal_potential = True 
                    #     if current['color'] == 'green':
                    #         # alert_queue.put("reversal potential")
                    #         score += 2
                    #     else:
                    #         score -= 3

                    # ✅ 2. Sharp shift in pull momentum: Medium-strong signal
                    # if abs(delta_shift_10m_1h) > 20:
                    if delta_shift_10m_1h < -20:
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
                        trend.append(f"{BLNK}{BLRED}R {WHTE}E {BLBLU}V {BLYEL}E {BLMAG}R {BLGRE}S {DGRY}A {BLCYN}L  🚀🚀{RES}")
                        reversal = True
                        state.is_reversal = True
                        score += 2
                        bear_score += 1 if h10 < ph10 and new_delta_10m < 0 else bear_score

                    # ✅ 8. Check for bet high
                    if current['color'] == 'red' and current_jackpot <= prev_jackpot and h10 < ph10:
                        trend.append("Intense Bearish Pull")
                        score += 2
                        bear_score += 1 if h10 < ph10 and new_delta_10m < 0 else bear_score

                    # ✅ 0. Check for bet max
                    if current['color'] == 'red' and current_jackpot < prev_jackpot and (current_jackpot - prev_jackpot < -0.03) and h10 < ph10:
                        trend.append("Extreme Bearish Pull")
                        score += 3
                        bear_score += 2 if h10 < ph10 and new_delta_10m < 0 else bear_score

                    # ✅ 10. Check for neutralization
                    if not trend:
                        trend.append("Neutral")

                    # alert_queue.put("reversal!") if reversal else None

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
                    
                    # add spin high pull score
                    # state.pull_score = result.get('pull_score', 0)
                    # if result.get('pull_score', 0) >= 10:
                    #     if spin_in_progress.is_set():
                    #         spin_in_progress.clear()
                    #         spin(*random.choice([(True, False), (False, True)]))
                    #         alert_queue.put(f"pull score {state.pull_score}")
                    #     else:
                    #         threading.Thread(target=spin, args=(False, False,), daemon=True).start()
                            
                    #     # logger.info(f"\t\t{BLCYN}Pull Score:: {result.get('pull_score', 0)}{RES}")
                    #         alert_queue.put(f"pull score {state.pull_score}")
                        
                    # state.prev_pull_delta = result.get('old_delta_10m')

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

        # if time_data and time_data.get(period):
        #     change = time_data[period].get('change')
        #     timestamp = time_data[period].get('timestamp')
        #     time_str = f"{YEL}{timestamp.strftime('%I')}{WHTE}:{YEL}{timestamp.strftime('%M')}{WHTE}:{LYEL}{timestamp.strftime('%S')} {LBLU}{timestamp.strftime('%p')}{RES}"
        #     color = LRED if change < 0 else LGRE if change > 0 else LCYN
        #     colored_time_data_change = f"{DGRY}History {color}{change}{percent} ({YEL}{time_str}{RES})"
        # else:
        #     colored_time_data_change = f"{DGRY}No History{RES}"
        
        # logger.info(f"\t{CYN}⏱{RES} {LYEL}{period}{RES}:  {colored_value}{percent} {diff} {signal} {colored_time_data_change}") if period == "10m" and pct(value) >= 0 else \
        #     logger.info(f"\t{CYN}⏱{RES} {LYEL}{period}{RES}: {colored_value}{percent} {diff} {signal} {colored_time_data_change}") if period == "10m" and pct(value) < 0 else \
        #     logger.info(f"\t{CYN}⏱{RES} {LYEL}{period}{RES}:   {colored_value}{percent} {diff} {signal} {colored_time_data_change}") if pct(value) >= 0 else \
        #     logger.info(f"\t{CYN}⏱{RES} {LYEL}{period}{RES}:  {colored_value}{percent} {diff} {signal} {colored_time_data_change}")
        
        logger.info(f"\t{CYN}⏱{RES} {LYEL}{period}{RES}:  {colored_value}{percent} {diff} {signal}") if period == "10m" and pct(value) >= 0 else \
            logger.info(f"\t{CYN}⏱{RES} {LYEL}{period}{RES}: {colored_value}{percent} {diff} {signal}") if period == "10m" and pct(value) < 0 else \
            logger.info(f"\t{CYN}⏱{RES} {LYEL}{period}{RES}:   {colored_value}{percent} {diff} {signal}") if pct(value) >= 0 else \
            logger.info(f"\t{CYN}⏱{RES} {LYEL}{period}{RES}:  {colored_value}{percent} {diff} {signal}")

    if result is not None:
        signal = f"{LRED}＋{RES}" if bear_score > state.prev_bear_score else f"{LGRE}－{RES}" if bear_score < state.prev_bear_score else f"{LCYN}＝{RES}"
        state.bear_score_inc = True if bear_score > state.prev_bear_score else False
        state.prev_bear_score = bear_score

        logger.info(f"\n\t🐻 Bear Score: {DGRY}[ {BWHTE}{bear_score} {DGRY}]{signal}")

        if bear_score >= 2:
            logger.info("\n\t✅ Bearish Momentum Detected")
        else:
            logger.info("\n\t❌ Not Enough Bearish Momentum")

        # state.prev_pull_delta = result.get('old_delta_10m')
        pull_score = result.get('pull_score', 0)
        signal = f"{LRED}＋{RES}" if pull_score > state.prev_pull_score else f"{LGRE}－{RES}" if pull_score < state.prev_pull_score else f"{LCYN}＝{RES}"
        state.pull_score_inc = True if pull_score > state.prev_pull_score else False
        state.prev_pull_score = pull_score

        if pull_score >= 8 and bet_level == "max":
            trend_strength = "💥💥💥  Extreme Pull"
            state.extreme_pull = True
        elif pull_score >= 7 and bet_level in [ "max", "high" ]:
            trend_strength = "🔥🔥  Intense Pull"
            state.intense_pull = True
        elif pull_score >= 6 and bet_level in [ "max", "high" ]:
            trend_strength = "☄️  Very Strong Pull"
        elif pull_score >= 5:
            trend_strength = "🔴  Stronger Pull"
        elif pull_score >= 4:
            trend_strength = "🟠  Strong Pull"
        elif pull_score >= 2:
            trend_strength = "🟡  Moderate Pull"
        elif pull_score >= 1:
            trend_strength = "🟤  Weak Pull"
        elif pull_score >= 0:
            trend_strength = "⚪  Neutral"
        else:
            trend_strength = "❓  Invalid"

        logger.info(f"\n\t💤 Pull Score: {BLCYN}{trend_strength} {DGRY}[ {BMAG}{pull_score} {DGRY}]{signal}")
        state.last_trend = f"{re.sub(r'[^\x00-\x7F]+', '', trend_strength)} score {pull_score}"

        if pull_score == 0 and bear_score == 0:
            alert_queue.put("Neutralize")
            state.neutralize = True
            logger.info(f"\t\t{LBLU}NEUTRALIZE{RES}")

        for idx, pull_trend in enumerate(result.get('pull_trend')):
            logger.info("\n\t💤 Pull Trend: ") if idx == 0 else None
            logger.info(f"\t\t{BWHTE}{pull_trend}{RES}") if pull_trend else None
        
        signal = f"{LRED}▼{RES}" if result.get('new_delta_10m') < result.get('old_delta_10m') and result.get('old_delta_10m') != 0 else f"{LGRE}▲{RES}" if result.get('new_delta_10m') > result.get('old_delta_10m') and result.get('old_delta_10m') != 0 else f"{LCYN}◆{RES}"
        logger.info(f"\n\t🧲 Delta{LMAG}Δ{RES} Pull Power ({DGRY}Current & Prev [10m]{RES}): {RED if result.get('new_delta_10m') < 0 else GRE + '+' if result.get('new_delta_10m') > 0 else CYN}{result.get('new_delta_10m')}{LMAG}Δ{RES} {DGRY}| {RED if result.get('old_delta_10m') < 0 else GRE + '+' if result.get('old_delta_10m') > 0 else CYN + '+'}{result.get('old_delta_10m')}{LMAG}Δ{RES}") 
        logger.info(f"\t🧪 Delta{LMAG}Δ{RES} Shift ({DGRY}Diff Current - Prev [10m]{RES}): {RED if result.get('delta_shift') < 0 else GRE + '+'}{result.get('delta_shift')}{LMAG}Δ{RES} {signal}")
        logger.info(f"\t🧪 Delta{LMAG}Δ{RES} Shift ({DGRY}Analysis [10m]{RES}): {MAG}Strong{RES} Pull  ✅") if result.get('delta_shift_analysis') else \
            logger.info(f"\t🧪 Delta{LMAG}Δ{RES} Shift ({DGRY}Analysis [10m]{RES}): {MAG}Weak{RES} Pull  ❌")
        logger.info(f"\t🧪 Delta{LMAG}Δ{RES} Shift ({DGRY}Decision [10m]{RES}): {BMAG}{'Very Strong' if result.get('delta_shift') <= -50 else 'Stronger' if result.get('delta_shift') <= -20 else 'Strong'}{RES} Pull  ✅") if result.get('delta_shift_decision') else \
            logger.info(f"\t🧪 Delta{LMAG}Δ{RES} Shift ({DGRY}Decision [10m]{RES}): {BMAG}{'Very Weak' if result.get('delta_shift') >= 50 else 'Weaker' if result.get('delta_shift') >= 20 else 'Weak'}{RES} Pull  ❌")
            
        signal = f"{LRED}▼{RES}" if result.get('new_delta_10m_1h') < result.get('old_delta_10m_1h') else f"{LGRE}▲{RES}" if result.get('new_delta_10m_1h') > result.get('old_delta_10m_1h') else f"{LCYN}◆{RES}"
        logger.info(f"\n\t📊 Delta{LMAG}Δ{RES} Trend Change Power ({DGRY}Current & Prev [10m_1h]{RES}): {RED if result.get('new_delta_10m_1h') < 0 else GRE + '+' if result.get('new_delta_10m_1h') > 0 else CYN}{result.get('new_delta_10m_1h')}{LMAG}Δ{RES} {DGRY}| {RED if result.get('old_delta_10m_1h') < 0 else GRE + '+' if result.get('old_delta_10m_1h') > 0 else CYN}{result.get('old_delta_10m_1h')}{LMAG}Δ{RES}")
        logger.info(f"\t🧪 Delta{LMAG}Δ{RES} Shift ({DGRY}Diff Current - Prev [10m_1h]{RES}): {RED if result.get('delta_shift_10m_1h') < 0 else GRE + '+'}{result.get('delta_shift_10m_1h')}{LMAG}Δ{RES} {signal}")
        logger.info(f"\t🧪 Delta{LMAG}Δ{RES} Shift ({DGRY}Analysis [10m_1h]{RES}): {LRED}🐻 Bearish{RES} Power  ✅") if result.get('delta_shift_analysis_10m_1h') else \
            logger.info(f"\t🧪 Delta{LMAG}Δ{RES} Shift ({DGRY}Analysis [10m_1h]{RES}): {GRE}🐂 Bullish{RES} Power  ❌")
        logger.info(f"\t🧪 Delta{LMAG}Δ{RES} Shift ({DGRY}Decision [10m_1h]{RES}): {BMAG}{'Very Strong' if result.get('delta_shift_10m_1h') <= 50 else 'Strong' if result.get('delta_shift_10m_1h') <= 20 else 'Weak'}{RES} Bearish Pull Surge  🐻") if result.get('delta_shift_decision_10m_1h') else \
            logger.info(f"\t🧪 Delta{LMAG}Δ{RES} Shift ({DGRY}Decision [10m_1h]{RES}): {BMAG}{'Very Strong' if result.get('delta_shift_10m_1h') >= 50 else 'Strong' if result.get('delta_shift_10m_1h') >= 20 else 'Weak'}{RES} Bullish Pull Surge  🐂")
        
        logger.info(f"\n\t⚡ Lowest Low Break Out: {RED if lowest_low < 0 else GRE}{lowest_low}{RES}{percent} {'✅' if is_low_breakout else '❌'}")
        logger.info(f"\t⚡ Lowest Low Break Out Delta{LMAG}Δ{RES}: {RED if lowest_low_delta < 0 else GRE}{lowest_low_delta}{RES}{percent} {'✅' if is_low_breakout_delta else '❌'}")
        logger.info(f"\n\t⚡ Highest High Break Out: {RED if highest_high < 0 else GRE}{highest_high}{RES}{percent} {'✅' if is_high_breakout else '❌'}")
        logger.info(f"\t⚡ Highest High Break Out Delta{LMAG}Δ{RES}: {RED if highest_high_delta < 0 else GRE}{highest_high_delta}{RES}{percent} {'✅' if is_high_breakout_delta else '❌'}")
 
    logger.info(f"\n\t\t{'💰 ' if current['color'] == 'red' else '⚠️ '}  {LYEL}Bet [{RES} {(BLNK) + (LRED if current['color'] == 'red' else LBLU)}{bet_level.upper()}{RES} {LYEL}]{RES}\n\n") if bet_level is not None else \
        logger.info("\n\t\t🚫  Don't Bet!  🚫\n\n")

    # if bet_level is not None:
    #     alert_queue.put(f"caution, bet {bet_level}, {state.last_trend}") if current['color'] == 'green' else \
    #     alert_queue.put(f"bet {bet_level}, {state.last_trend}")
    # else:
    #     alert_queue.put("do not bet")

    state.bet_lvl = bet_level
    # state.last_trend = None

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
    #     logger.info(f"\n\t>>> Bet [ {BLYEL}{bet_level.upper()}{RES} ]\n\n")
    #     countdown_thread = threading.Thread(target=countdown_timer, args=(59,), daemon=True)
    #     countdown_thread.start()
    # else:
    #     logger.info(f"\n\t❌ Don't Bet! ❌\n")
    # logger.info('\t[2] - BET_LEVEL << ', bet_level)
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
    today = datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d")
    
    if os.path.exists(BREAKOUT_FILE):
        with open(BREAKOUT_FILE, 'r') as f:
            data = json.load(f)
            day_data = data.get(today, {})
            return day_data.get(game.lower(), {"lowest_low": 0, "lowest_low_delta": 0, "highest_high": 0, "highest_high_delta": 0})
    return {"lowest_low": 0, "lowest_low_delta": 0, "highest_high": 0, "highest_high_delta": 0}

def save_breakout_memory(game: str, lowest_low: float, lowest_low_delta: float, highest_high: float, highest_high_delta: float):
    today = datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d")
    data = {}

    if os.path.exists(BREAKOUT_FILE):
        with open(BREAKOUT_FILE, 'r') as f:
            data = json.load(f)

    if today not in data:
        data[today] = {}

    data[today][game.lower()] = {
        "lowest_low": lowest_low,
        "lowest_low_delta": lowest_low_delta,
        "highest_high": highest_high,
        "highest_high_delta": highest_high_delta
    }

    with open(BREAKOUT_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def play_alert(say: str=None):
    if platform.system() == "Darwin":
        while not stop_event.is_set():
            try:
                say = alert_queue.get_nowait()
                sound_file = (say)

                if sound_file == "ping":
                    subprocess.run(["afplay", PING])
                else:
                    voice = VOICES["Trinoids"] if "prediction" in sound_file or "pull score spin" in sound_file or "bet max" in sound_file else VOICES["Samantha"]
                    subprocess.run(["say", "-v", voice, "--", sound_file])
                    
            except Empty:
                continue
            except Exception as e:
                logger.info(f"\n\t[Alert Thread Error] {e}")
    else:
        pass

def countdown_timer(seconds: int = 10):
    triggered_sec = None
    
    while not stop_event.is_set():
        now_time = time.time()
        # now_time = Decimal(str(time.time()))
        current_sec = int(now_time) % seconds
        time_left = 0 if current_sec % 10 == 0 else seconds - current_sec

        blink = BLNK if current_sec % 2 == 0 else ""
        
        text = (
            f"{BLU}Betting Ends In{RES}"
            if state.bet_lvl is not None else
            f"{BCYN}Loading Game Data{RES}" if state.new_jackpot_val == 0.0 else
            f"{BLU}Waiting For Next Iteration{RES}"
        )

        timer = (
            f"\t⏳ {text}: "
            f"{BYEL}{time_left // seconds:02d}{BWHTE}{blink}:{RES}"
            f"{BLYEL}{time_left:02d}{RES}  "
            f"( {LGRY}{re.sub(r'\\s*\\(.*?\\)', '', game)}{RES} "
            f"{DGRY}| {PROVIDERS.get(provider).color}{provider}{RES} )"
        )
        
        sys.stdout.write(f"\r{timer}")
        sys.stdout.flush()
        
        if state.auto_mode:
            # dynamic jackpot conditions - absolute value test pull
            jackpot_conditions = all([
                abs(state.last_pull_delta) < abs(state.pull_delta),
                state.last_min10 < state.min10,
                state.min10 >= state.min10_thresh,
                abs(state.pull_delta) >= state.pull_thresh
            ])
            # # dynamic jackpot conditions
            # jackpot_conditions = all([
            #     state.last_pull_delta < state.pull_delta,
            #     state.last_min10 < state.min10,
            #     state.min10 >= state.min10_thresh,
            #     state.pull_delta >= state.pull_thresh
            # ])
            # jackpot_conditions = all([
            #     state.last_pull_delta < state.pull_delta,
            #     state.last_min10 < state.min10,
            #     state.min10 >= 40, # note on this change too
            #     state.pull_delta >= 50 # this is trend changer in charet.. 
            # ])
            
            if jackpot_conditions and triggered_sec is None:
                spin(False, False, True, False,)
                # state.fast_mode = True
                triggered_sec = current_sec
                logger.info(f"\n\t💥  Jackpot trend detected! pull_delta={state.pull_delta:.2f}, min10={state.min10:.2f}")
                alert_queue.put(f"{current_sec} jackpot mode ON")
                
            if triggered_sec is not None:
                spin(False, False, False, False,)
                if not jackpot_conditions:
                    triggered_sec = None
                    alert_queue.put(f"{current_sec} jackpot mode OFF")
                
                # if not jackpot_conditions and triggered_sec is not None:
                #     # state.fast_mode = False
                #     triggered_sec = None
                #     alert_queue.put(f"{current_sec} jackpot mode OFF")
            
            # logger.info(f"\n\tprediction >> {prediction_conditions} | current sec >> {current_sec}")
            # logger.info(f"\tcondition # 1 >>> {state.last_pull_delta < state.pull_delta}")
            # logger.info(f"\tcondition # 2 >>> {state.last_min10 < state.min10}")
            # logger.info(f"\tcondition # 3 >>> {state.min10 > 0}")
            # logger.info(f"\tcondition # 4 >>> {state.pull_delta >= 25}")
            
            # logger.info(f"state.last_pull_delta: {state.last_pull_delta}")
            # logger.info(f"state.pull_delta: {state.pull_delta}")
            # logger.info(f"state.last_min10: {state.last_min10}")
            # logger.info(f"state.min10: {state.min10}")
            
            if not jackpot_conditions:
                if not state.fast_mode:
                    if current_sec == 6 and state.last_time != Decimal('0'): # DEAD SPIN
                        # wait_before_spin = float(interval_ms - 2)
                        # wait_before_spin = float(interval_ms)
                        threading.Thread(target=spin, args=(False, False, False, True,), daemon=True).start()
                        
                        # logger.info(f"\nCurrent Sec ({YEL}{current_sec}){RES}, Trigger Sec: ({MAG}{trigger_sec}{RES})")
                        # logger.info(f"\nINTERVAL MS (prediction): {interval_ms}")
                        # spin(False, False, False, wait_before_spin)
                        # logger.info(f"\nTRIGGER SEC (prediction): {trigger_sec}")
                        # logger.info(f"\nWAIT INIT (prediction): {wait_before_spin}")
                    else:
                        if current_sec >= 8 or current_sec == 0:
                            alert_queue.put(f"{time_left}")
                else:   # FAST MODE
                    spin(False, False, False, False,)
                    
        # Calculate precise sleep until the next full second
        next_sec = math.ceil(now_time)
        sleep_time = max(0, next_sec - time.time())
        time.sleep(sleep_time)
        
def bet_switch(bet_level: str=None, extra_bet: bool=None, slot_position: str=None):
    while not stop_event.is_set():
        try:
            bet_level, extra_bet, slot_position = bet_queue.get_nowait()

            # if state.left_slot or slot_position == "left":
            #     center_x, CENTER_Y = LEFT_SLOT_POS.get("center_x"), LEFT_SLOT_POS.get("center_y")
            # elif state.right_slot or slot_position == "right":
            #     center_x, CENTER_Y = RIGHT_SLOT_POS.get("center_x"), RIGHT_SLOT_POS.get("center_y")
            # else:
            #     center_x, CENTER_Y = SCREEN_POS.get("center_x"), SCREEN_POS.get("center_y")
                # pyautogui.moveTo(x=center_x, y=CENTER_Y) if state.auto_mode else None

            cx, cy = CENTER_X, CENTER_Y
            # LEFT_X, RIGHT_X, TOP_Y, BTM_Y = 0, SCREEN_POS.get("right_x"), 0, SCREEN_POS.get("bottom_y")
            
            if slot_position is not None and state.split_screen:
                pyautogui.doubleClick(x=cx, y=BTM_Y)
                time.sleep(1)
                # if extra_bet and game.startswith("Fortune Gems"):
                if extra_bet and game in [ "Fortune Gems", "Neko Fortune" ]:
                    pyautogui.click(x=cx-228, y=cy-126)
                    pyautogui.doubleClick(x=cx-100, y=cy-126)
                    pyautogui.doubleClick(x=cx-100, y=cy-126)
                else:
                    pyautogui.moveTo(x=cx-100, y=cy-126)
            else:
                # if extra_bet and game.startswith("Fortune Gems"):
                if extra_bet:
                    if game in "Fortune Gems":
                        x1, y1 = cx - 550, cy + 215
                        x2, y2 = cx - 248, cy + 215
                    elif game in "Neko Fortune":
                        x1, y1 = cx - 585, cy + 237
                        x2, y2 = cx - 350, cy + 237
                    # logger.info(f"\t\n{BLRED}cx, cy{RES} >> ", cx, cy) Arguments: (735, 478)
                    pyautogui.click(x=x1, y=y1)
                    pyautogui.click(x=x2, y=y2)

            if extra_bet:
                state.extra_bet = not state.extra_bet
                status = "on" if state.extra_bet else "disabled"
                alert_queue.put(f"extra_bet {status}")
                logger.debug(f"\tExtra Bet: {status}")
        except Empty:
            continue

def spin(combo_spin: bool = False, spam_spin: bool = False, turbo_spin: bool = False, wait_before_spin: bool = False):
    # while not stop_event.is_set():
    if spin_in_progress.is_set():
        sys.stdout.write("\t⚠️  Spin still in action, skipping")
        return
    
    spin_in_progress.set()

    try:
        # cmd, combo_spin = spin_queue.get_nowait()
        # spin_in_progress, combo_spin = spin_queue.get(timeout=1)
        spin_types = [ "normal_spin", "spin_hold", "spin_delay", "spin_hold_delay", "turbo_spin", "super_turbo", "board_spin", "board_spin_hold", "board_spin_delay", "board_spin_hold_delay", "board_spin_turbo", "spin_slide", "auto_spin" ]
        
        if not combo_spin and "PG" in provider:
            spin_types = [s for s in spin_types if not s.startswith("board")]

        if combo_spin:
            spin_types = [s for s in spin_types if s.startswith("board")]
            spin_types.extend(["combo_spin", "spam_spin", "turbo_spin"])
            
        if turbo_spin:
            spin_types = [ "turbo_spin", "super_turbo", "spin_hold", "spam_spin", "combo_spin" ]
                
        if "JILI" in provider:
            spin_types.extend([ "max_turbo" ])
            
        if not state.fast_mode and wait_before_spin and random.random() < 0.4: # 40% use normal spin
            spin_type = "normal_spin"
        else:
            spin_type = random.choice(spin_types) #if not spam_spin else "spam_spin"
            
        cx, cy = CENTER_X, CENTER_Y

        shrink_percentage = 60 if state.widescreen else 32
        width = int(max(RIGHT_X, BTM_Y) * (shrink_percentage / 100))
        height = int(min(RIGHT_X, BTM_Y) * (shrink_percentage / 100))
        border_space_top = cy // 3 if state.widescreen else 0
        radius_x, radius_y = width // 2, height // 2 #if widescreen else width // 2
        # rand_x = cx + random.randint(-radius_x, radius_x)
        # rand_y = cy + random.randint(-radius_y, radius_y) + (border_space_top if radius_y <= 0 else -border_space_top)
        # rand_x2 = cx - random.randint(-radius_x, radius_x)
        # rand_y2 = cy - random.randint(-radius_y, radius_y) + (border_space_top if radius_y <= 0 else -border_space_top)
        rand_x = cx - random.randint(-radius_x, radius_x)
        rand_y = random.randint(200, cy)
        # mystic = 100
        # cruise_royal = 100
        # queen of bounty = cy

        rand_x2 = cx - random.randint(-radius_x, radius_x)
        rand_y2 = random.randint(200, cy)

        # print(f'\theight >>> {height}')
        # print(f'\tBTM_Y >>> {BTM_Y}')
        # print(f'\tcx >>> {cx}')
        # print(f'\tcy >>> {cy}')
        # print(f'\tradius_x >>> {radius_x}')
        # print(f'\tradius_y >>> {radius_y}')
        # print(f'\trand_x >>> {rand_x}')
        # print(f'\trand_y >>> {rand_y}')
        # print(f'\trand_x2 >>> {rand_x2}')
        # print(f'\trand_y2 >>> {rand_y2}')
        
        action = []
        
        hold_delay = random.uniform(*HOLD_DELAY_RANGE)
        # spin_delay = random.uniform(*SPIN_DELAY_RANGE)
        timeout_delay = random.uniform(*TIMEOUT_DELAY_RANGE)
        # print(f'widescreen: {widescreen}')
        # print(f'state.spin_btn: {state.spin_btn}')
        
        if spin_type == "normal_spin":
            if state.widescreen:
                action.extend([
                    lambda: pyautogui.click(x=cx + 520, y=cy + 335, button='left'),
                    lambda: pyautogui.click(x=cx + 520, y=cy + 335, button='right'),
                    lambda: pyautogui.press('space'),
                    lambda: (pyautogui.keyDown('space'), pyautogui.keyUp('space')),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='left'), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='right'), pyautogui.mouseUp())
                ])
            else:
                # NO RIGHT CLICK FOR BUTTON IN PG (BUT MOUSEDOWN IS GOOD)
                action.extend([
                    lambda: pyautogui.click(x=cx, y=BTM_Y - 105, button='left'),
                    # lambda: pyautogui.click(x=cx, y=BTM_Y - 105, button='right'),
                    lambda: pyautogui.press('space'),
                    lambda: (pyautogui.keyDown('space'), pyautogui.keyUp('space')),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), pyautogui.mouseUp())
                ]) if not state.spin_btn else \
                action.extend([
                    lambda: pyautogui.click(x=cx, y=BTM_Y - 105, button='left'),
                    lambda: pyautogui.click(x=cx, y=BTM_Y - 105, button='right'),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), pyautogui.mouseUp())
                ])
        elif spin_type == "spin_hold":
            if state.widescreen:
                action.extend([
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), pyautogui.mouseDown(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), pyautogui.mouseDown(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), pyautogui.mouseDown(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), pyautogui.mouseDown(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'))
                ])
            else:
                action.extend([
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.mouseDown(button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.mouseDown(button='right')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.mouseDown(button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.mouseDown(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.press('space'), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.press('space'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.keyDown('space'), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.keyDown('space'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'))
                ]) if not state.spin_btn else \
                action.extend([
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.mouseDown(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.mouseDown(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.mouseDown(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.mouseDown(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'))
                ])
        elif spin_type == "spin_delay":
            if state.widescreen:
                action.extend([
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(button='left')),
                    # lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(button='right')),
                    # lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='left')),
                    # lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='right')),
                    # lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.keyUp('space')),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='right'), time.sleep(hold_delay), pyautogui.mouseUp())
                ])
            else:
                action.extend([
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.press('space')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(button='right')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(button='right')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.keyUp('space')),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.mouseUp())
                ]) if not state.spin_btn else \
                action.extend([
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(button='right')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.mouseUp())
                ])
        elif spin_type == "spin_hold_delay":
            if state.widescreen:
                action.extend([
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.press('space')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='left')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 335, button='right')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='right')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='right'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='right'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 335, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),                       
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),                        
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right'))
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='right'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='right'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='right'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='right'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'))
                ])
            else:
                action.extend([
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.press('space')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.press('space')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),                       
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),                        
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right'))
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'))
                ]) if not state.spin_btn else \
                action.extend([
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),                       
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),                        
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right'))
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'))
                ])
        elif spin_type == "board_spin":
            if state.widescreen:
                action.extend([
                    lambda: pyautogui.click(x=rand_x, y=rand_y, button='left'),
                    lambda: pyautogui.click(x=rand_x, y=rand_y, button='right'),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), pyautogui.mouseUp())
                ])
            else:
                action.extend([
                    lambda: pyautogui.click(x=rand_x, y=rand_y, button='left'),
                    # lambda: pyautogui.click(x=rand_x, y=rand_y, button='right'),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), pyautogui.mouseUp())
                ]) if not state.spin_btn else \
                action.extend([
                    lambda: pyautogui.click(x=rand_x, y=rand_y, button='left'),
                    lambda: pyautogui.click(x=rand_x, y=rand_y, button='right'),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), pyautogui.mouseUp())
                ])
        elif spin_type == "board_spin_hold":
            if state.widescreen:
                action.extend([
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.mouseDown(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.mouseDown(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.mouseDown(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.mouseDown(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y), pyautogui.mouseDown(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y), pyautogui.mouseDown(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y), pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y), pyautogui.mouseDown(x=cx + 520, y=cy + 335, button='right'))
                ])
            else:
                action.extend([
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.mouseDown(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.mouseDown(button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.mouseDown(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.mouseDown(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y), pyautogui.mouseDown(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y), pyautogui.mouseDown(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'))
                ]) if not state.spin_btn else \
                action.extend([
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.mouseDown(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.mouseDown(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.mouseDown(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.mouseDown(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y), pyautogui.mouseDown(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y), pyautogui.mouseDown(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'))
                ])
        elif spin_type == "board_spin_delay":
            if state.widescreen:
                action.extend([
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.mouseUp())
                ])
            else:
                action.extend([
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.press('space')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.mouseUp())
                ]) if not state.spin_btn else \
                action.extend([
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.mouseUp())
                ])
        elif spin_type == "board_spin_hold_delay":
            if state.widescreen:
                action.extend([
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='left')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='left')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(button='right'))
                ])
            else:
                action.extend([
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.press('space')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(button='right'))
                ]) if not state.spin_btn else \
                action.extend([
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(button='right'))
                ])
        elif spin_type == "spin_slide":
            if state.widescreen:
                action.extend([
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.moveTo(x=rand_x2, y=rand_y2), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.moveTo(x=rand_x2, y=rand_y2), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), pyautogui.moveTo(x=rand_x2, y=rand_y2), time.sleep(hold_delay), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), pyautogui.moveTo(x=rand_x2, y=rand_y2), time.sleep(hold_delay), pyautogui.mouseUp())
                ])
            else:
                action.extend([
                    lambda: (pyautogui.press('space'), time.sleep(timeout_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), pyautogui.moveTo(x=rand_x2, y=rand_y2), pyautogui.mouseUp()),
                    lambda: (pyautogui.press('space'), time.sleep(timeout_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), pyautogui.moveTo(x=rand_x2, y=rand_y2), pyautogui.mouseUp()),
                    lambda: (pyautogui.press('space'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), pyautogui.moveTo(x=rand_x2, y=rand_y2), time.sleep(hold_delay), pyautogui.mouseUp()),
                    lambda: (pyautogui.press('space'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), pyautogui.moveTo(x=rand_x2, y=rand_y2), time.sleep(hold_delay), pyautogui.mouseUp()),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(timeout_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), pyautogui.moveTo(x=rand_x2, y=rand_y2), pyautogui.mouseUp()),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(timeout_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), pyautogui.moveTo(x=rand_x2, y=rand_y2), pyautogui.mouseUp()),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(timeout_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), pyautogui.moveTo(x=rand_x2, y=rand_y2), pyautogui.mouseUp()),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(timeout_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), pyautogui.moveTo(x=rand_x2, y=rand_y2), pyautogui.mouseUp()),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), pyautogui.moveTo(x=rand_x2, y=rand_y2), time.sleep(hold_delay), pyautogui.mouseUp()),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), pyautogui.moveTo(x=rand_x2, y=rand_y2), time.sleep(hold_delay), pyautogui.mouseUp()),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), pyautogui.moveTo(x=rand_x2, y=rand_y2), time.sleep(hold_delay), pyautogui.mouseUp()),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), pyautogui.moveTo(x=rand_x2, y=rand_y2), time.sleep(hold_delay), pyautogui.mouseUp())
                ]) if not state.spin_btn else \
                action.extend([
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.moveTo(x=rand_x2, y=rand_y2), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.moveTo(x=rand_x2, y=rand_y2), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), pyautogui.moveTo(x=rand_x2, y=rand_y2), time.sleep(hold_delay), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), pyautogui.moveTo(x=rand_x2, y=rand_y2), time.sleep(hold_delay), pyautogui.mouseUp())
                ])
        elif spin_type == "board_spin_turbo":
            if state.widescreen:
                action.extend([
                    lambda: pyautogui.doubleClick(x=rand_x, y=rand_y, button='left'),
                    lambda: pyautogui.doubleClick(x=rand_x, y=rand_y, button='right'),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(x=cx + 520, y=cy + 335, button='right'))
                ])
            else:
                action.extend([
                    lambda: pyautogui.doubleClick(x=rand_x, y=rand_y, button='left'),
                    # lambda: pyautogui.doubleClick(x=rand_x, y=rand_y, button='right'),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.press('space')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.keyDown('space')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'))
                ]) if not state.spin_btn else \
                action.extend([
                    lambda: pyautogui.doubleClick(x=rand_x, y=rand_y, button='left'),
                    lambda: pyautogui.doubleClick(x=rand_x, y=rand_y, button='right'),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'))
                ])
        elif spin_type == "turbo_spin": # add turbo-on + space then board stop and turbo-off soon; also auto_spin + board_stop..etc
            if state.widescreen:
                if provider == "JILI": # Playtime
                    cx += 40
                    cy += 40
                action.extend([
                    lambda: pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='left'),
                    lambda: pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='right'),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.press('space')),
                    lambda: (pyautogui.press('space'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.click(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.click(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.press('space')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.click(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.click(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.click(x=rand_x, y=rand_y, button='right'))
                ])
            else:
                if "PG" in provider:
                    action.extend([
                        lambda: pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left'),
                        # lambda: pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right'),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(button='left')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(button='right')),
                        # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(button='left')),
                        # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(button='right')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(button='left')),
                        # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(button='right')),
                        # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(button='left')),
                        # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(button='right')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                        # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                        # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                        # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                        # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                        # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                        # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                        
                        # # TURBO ENABLED
                        # lambda: (pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left')),
                        # # lambda: (pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left')),
                        # # lambda: (pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left')),
                        # # lambda: (pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left')),
                        # # lambda: (pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='right'), pyautogui.press('space'), pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left')),
                        # # TURBO ENABLED
                        
                        lambda: (pyautogui.press('space'), pyautogui.press('space')),
                        lambda: (pyautogui.press('space'), pyautogui.keyDown('space')),
                        
                        lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                        # lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),

                        lambda: (pyautogui.press('space'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(button='left')),
                        # lambda: (pyautogui.press('space'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(button='right')),
                        # lambda: (pyautogui.press('space'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(button='left')),
                        # lambda: (pyautogui.press('space'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(button='right'))
                    ])
                else:
                    action.extend([
                        lambda: pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left'),
                        lambda: pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right'),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.press('space')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.press('space')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.keyDown('space')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.keyDown('space')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(button='left')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(button='right')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(button='left')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(button='right')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(button='left')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(button='right')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(button='left')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(button='right')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                        lambda: (pyautogui.press('space'), pyautogui.press('space')),
                        lambda: (pyautogui.press('space'), pyautogui.keyDown('space')),
                        lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                        lambda: (pyautogui.press('space'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.press('space'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                        lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                        lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                        lambda: (pyautogui.press('space'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                        lambda: (pyautogui.press('space'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                        lambda: (pyautogui.keyDown('space'), pyautogui.press('space')),
                        lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                        lambda: (pyautogui.keyDown('space'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.keyDown('space'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                        lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                        lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                        lambda: (pyautogui.keyDown('space'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                        lambda: (pyautogui.keyDown('space'), pyautogui.click(x=rand_x, y=rand_y, button='right'))
                    ]) if not state.spin_btn else \
                    action.extend([
                        #
                    ])
        elif spin_type == "super_turbo": # 1 star if JILI
            if state.widescreen:
                if provider == "JILI": # Playtime
                    cx += 40
                    cy += 40
                action.extend([
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.press('space'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.press('space'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right')),
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.press('space'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.press('space'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right')),
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.click(x=cx + 520, y=cy + 335, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.click(x=cx + 520, y=cy + 335, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right')),
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.click(x=cx + 520, y=cy + 335, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.click(x=cx + 520, y=cy + 335, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right')),
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.click(x=cx + 520, y=cy + 335, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right')),
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.click(x=cx + 520, y=cy + 335, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.click(x=cx + 520, y=cy + 335, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right')),
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.click(x=cx + 520, y=cy + 335, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.click(x=rand_x2, y=rand_y2, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.click(x=rand_x2, y=rand_y2, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right')),
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.click(x=rand_x2, y=rand_y2, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.click(x=rand_x2, y=rand_y2, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right')),
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.click(x=rand_x2, y=rand_y2, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right')),
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.click(x=rand_x2, y=rand_y2, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.click(x=rand_x2, y=rand_y2, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right')),
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.click(x=rand_x2, y=rand_y2, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
                    # auto spin style
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right')),
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right')),
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right')),
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
                    lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right'))
                ])
            else:
                if "PG" in provider:
                    action.extend([
                        # TURBO ENABLED
                        lambda: (pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(0.5), pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left')),
                        # lambda: (pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left')),
                        # lambda: (pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left')),
                        # lambda: (pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left')),
                        # lambda: (pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='right'), pyautogui.press('space'), pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left')),
                        # TURBO ENABLED
                        lambda: (pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left'), pyautogui.press('space'), time.sleep(0.5), pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left'))
                    ])
                else:
                    action.extend([
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.press('space'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.press('space'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right')),
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.press('space'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.press('space'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right')),
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right')),
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right')),
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right')),
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right')),
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x2, y=rand_y2, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x2, y=rand_y2, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right')),
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x2, y=rand_y2, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x2, y=rand_y2, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right')),
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x2, y=rand_y2, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right')),
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x2, y=rand_y2, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x2, y=rand_y2, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right')),
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x2, y=rand_y2, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
                        # auto spin style
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right')),
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right')),
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right')),
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right'))
                    ]) if not state.spin_btn else \
                    action.extend([
                        #
                    ])
        elif spin_type == "max_turbo": # 2 stars only JILI
            if state.widescreen:
                if provider == "JILI": # Playtime
                    cx += 40
                    cy += 40
                action.extend([
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left'), pyautogui.press('space'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='left')),
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left'), pyautogui.press('space'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='right')),
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right'), pyautogui.press('space'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='left')),
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right'), pyautogui.press('space'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='right')),
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left'), pyautogui.click(x=cx + 520, y=cy + 335, button='left'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='left')),
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left'), pyautogui.click(x=cx + 520, y=cy + 335, button='left'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='right')),
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left'), pyautogui.click(x=cx + 520, y=cy + 335, button='right'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='left')),
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left'), pyautogui.click(x=cx + 520, y=cy + 335, button='right'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='right')),
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right'), pyautogui.click(x=cx + 520, y=cy + 335, button='right'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='right')),
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right'), pyautogui.click(x=cx + 520, y=cy + 335, button='right'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='left')),
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right'), pyautogui.click(x=cx + 520, y=cy + 335, button='left'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='right')),
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right'), pyautogui.click(x=cx + 520, y=cy + 335, button='left'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='left')),
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left'), pyautogui.click(x=rand_x2, y=rand_y2, button='left'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='left')),
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left'), pyautogui.click(x=rand_x2, y=rand_y2, button='left'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='right')),
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left'), pyautogui.click(x=rand_x2, y=rand_y2, button='right'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='left')),
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left'), pyautogui.click(x=rand_x2, y=rand_y2, button='right'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='right')),
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right'), pyautogui.click(x=rand_x2, y=rand_y2, button='right'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='right')),
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right'), pyautogui.click(x=rand_x2, y=rand_y2, button='right'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='left')),
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right'), pyautogui.click(x=rand_x2, y=rand_y2, button='left'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='right')),
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right'), pyautogui.click(x=rand_x2, y=rand_y2, button='left'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='left')),
                    # auto spin style
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left'), pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='left'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='left')),
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left'), pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='left'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='right')),
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left'), pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='right'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='left')),
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left'), pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='right'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='right')),
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right'), pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='left'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='left')),
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right'), pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='left'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='right')),
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right'), pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='right'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='left')),
                    lambda: (pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right'), pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='right'), time.sleep(0.5), pyautogui.click(x=cx + 240, y=cy + 325, button='right'))
                ])
            else:
                action.extend([
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.press('space'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.press('space'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.press('space'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.press('space'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x2, y=rand_y2, button='left'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x2, y=rand_y2, button='left'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x2, y=rand_y2, button='right'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x2, y=rand_y2, button='right'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x2, y=rand_y2, button='right'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x2, y=rand_y2, button='right'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x2, y=rand_y2, button='left'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x2, y=rand_y2, button='left'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left')),
                    # auto spin style
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='left'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='left'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='right'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='right'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='left'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='left'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='right'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='right'), time.sleep(0.5), pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'))
                ])
        elif spin_type == "auto_spin":
            if state.widescreen:
                if provider == "JILI": # Playtime
                    cx += 40
                    cy += 40
                action.extend([
                    lambda: pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='left'),
                    lambda: pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='right'),
                    lambda: (pyautogui.click(x=cx + 380, y=cy + 325, button='left'), pyautogui.click(x=cx + 380, y=cy + 325,button='left')),
                    lambda: (pyautogui.click(x=cx + 380, y=cy + 325, button='right'), pyautogui.click(x=cx + 380, y=cy + 325,button='right'))
                ])
            else:
                if "PG" in provider:
                    action.extend([
                        lambda: (pyautogui.click(x=cx + 195, y=BTM_Y - 105, button='left'), time.sleep(0.3), pyautogui.click(x=cx - 195, y=BTM_Y - 205, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(1.5), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.click(x=cx + 195, y=BTM_Y - 105, button='left'), time.sleep(0.3), pyautogui.click(x=cx - 100, y=BTM_Y - 205, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(1.5), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.click(x=cx + 195, y=BTM_Y - 105, button='left'), time.sleep(0.3), pyautogui.click(x=cx, y=BTM_Y - 205, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(1.5), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.click(x=cx + 195, y=BTM_Y - 105, button='left'), time.sleep(0.3), pyautogui.click(x=cx + 100, y=BTM_Y - 205, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(1.5), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.click(x=cx + 195, y=BTM_Y - 105, button='left'), time.sleep(0.3), pyautogui.click(x=cx + 195, y=BTM_Y - 205, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(1.5), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                        # lambda: (pyautogui.click(x=cx + 195, y=BTM_Y - 105, button='right'), time.sleep(0.3), pyautogui.click(x=cx - 195, y=BTM_Y - 205, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(0.9), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                        # lambda: (pyautogui.click(x=cx + 195, y=BTM_Y - 105, button='right'), time.sleep(0.3), pyautogui.click(x=cx - 100, y=BTM_Y - 205, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(0.9), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                        # lambda: (pyautogui.click(x=cx + 195, y=BTM_Y - 105, button='right'), time.sleep(0.3), pyautogui.click(x=cx, y=BTM_Y - 205, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(0.9), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                        # lambda: (pyautogui.click(x=cx + 195, y=BTM_Y - 105, button='right'), time.sleep(0.3), pyautogui.click(x=cx + 100, y=BTM_Y - 205, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(0.9), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                        # lambda: (pyautogui.click(x=cx + 195, y=BTM_Y - 105, button='right'), time.sleep(0.3), pyautogui.click(x=cx + 195, y=BTM_Y - 205, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(0.9), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'))
                    ])
                else:
                    action.extend([
                        lambda: pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='left'),
                        lambda: pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='right'),
                        lambda: (pyautogui.click(x=cx + 95, y=BTM_Y - 105, button='left'), pyautogui.click(x=cx + 95, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.click(x=cx + 95, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx + 95, y=BTM_Y - 105, button='right'))
                    ]) if not state.spin_btn else \
                action.extend([
                    #
                ])
        elif spin_type == "combo_spin":
            action.extend([
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.moveTo(x=rand_x2, y=rand_y2), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.moveTo(x=rand_x2, y=rand_y2), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), pyautogui.moveTo(x=rand_x2, y=rand_y2), time.sleep(hold_delay), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), pyautogui.moveTo(x=rand_x2, y=rand_y2), time.sleep(hold_delay), pyautogui.mouseUp()),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.keyUp('space')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    # spam
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_y2, y=rand_y2, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_y2, y=rand_y2, button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_y2, y=rand_y2, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_y2, y=rand_y2, button='right')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.click(x=rand_y2, y=rand_y2, button='left')),
                    # lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.click(x=rand_y2, y=rand_y2, button='right')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.click(x=rand_y2, y=rand_y2, button='right')),
            ])
        elif spin_type == "spam_spin":
            action.extend([
                lambda: [ pyautogui.typewrite(['space'] * 6, interval=0.01) for _ in range(3) ],
                lambda: [ pyautogui.click(x=rand_x, y=rand_y, clicks=6, interval=0.01, button="left") for _ in range(3) ],
                # lambda: pyautogui.doubleClick(x=rand_x, y=rand_y, clicks=3, interval=0.01, button="left"),
                lambda: [ pyautogui.click(x=cx, y=BTM_Y - 105, clicks=6, interval=0.01, button="left") for _ in range(3) ],
                # lambda: pyautogui.doubleClick(x=cx, y=BTM_Y - 105, clicks=3, interval=0.01, button="left"),
                
                lambda: [ (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.moveTo(x=rand_x2, y=rand_y2), pyautogui.mouseUp()) for _ in range(3) ],
                lambda: [ (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button="left"), pyautogui.typewrite(['space'] * 6, interval=0.01)) for _ in range(3) ],
                lambda: [ (pyautogui.mouseDown(x=rand_x, y=rand_y, button="left"), pyautogui.typewrite(['space'] * 6, interval=0.01)) for _ in range(3) ],
                lambda: [ (pyautogui.keyDown('space'), pyautogui.click(x=rand_x, y=rand_y, clicks=6, interval=0.01, button="left")) for _ in range(3) ],
                lambda: [ (pyautogui.keyDown('space'), pyautogui.click(x=cx, y=BTM_Y - 105, clicks=6, interval=0.01, button="left")) for _ in range(3) ],
                
                lambda: [ (pyautogui.press("space"), pyautogui.click(x=rand_x, y=rand_y, button="left"), time.sleep(0.01)) for _ in range(3) ],
                # lambda: [ (pyautogui.press("space"), pyautogui.doubleClick(x=rand_x, y=rand_y, button="left")) for _ in range(3) ],
                lambda: [ (pyautogui.press("space"), pyautogui.click(x=cx, y=BTM_Y - 105, button="left"), time.sleep(0.01)) for _ in range(3) ],
                # lambda: [ (pyautogui.press("space"), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button="left")) for _ in range(3) ],
                lambda: [ (pyautogui.click(x=cx, y=BTM_Y - 105, button="left"), pyautogui.click(x=rand_x, y=rand_y, button="left"), time.sleep(0.01)) for _ in range(3) ],
            ])
        elif spin_type == "quick_spin":
            if state.widescreen:
                action.extend([
                    lambda: pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='left'),
                    lambda: pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='right'),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='left'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 335, button='right'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.press('space')),
                    lambda: (pyautogui.press('space'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.click(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.click(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.press('space')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.click(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.click(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: pyautogui.doubleClick(x=rand_x, y=rand_y, button='left'),
                    lambda: pyautogui.doubleClick(x=rand_x, y=rand_y, button='right'),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(x=cx + 520, y=cy + 335, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(x=cx + 520, y=cy + 335, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(x=cx + 520, y=cy + 335, button='right'))
                ])
            else:
                action.extend([
                    lambda: pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left'),
                    lambda: pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right'),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.press('space')),
                    lambda: (pyautogui.press('space'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.press('space')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: pyautogui.doubleClick(x=rand_x, y=rand_y, button='left'),
                    lambda: pyautogui.doubleClick(x=rand_x, y=rand_y, button='right'),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'))
                ]) if not state.spin_btn else \
                action.extend([
                    lambda: pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left'),
                    lambda: pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right'),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: pyautogui.doubleClick(x=rand_x, y=rand_y, button='left'),
                    lambda: pyautogui.doubleClick(x=rand_x, y=rand_y, button='right'),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'))
                ])

        if not action:
            logger.info(f"\t⚠️ No available spin actions for {spin_type}")
            return
        
        if not state.fast_mode:
            alert_queue.put(f"{spin_type}")
        
        if not state.fast_mode and wait_before_spin:
            interval_ms = Decimal(str(time.time())) - state.last_time
            waiting_time = float(interval_ms) - 3
            
            if spin_type.endswith("delay"):# or spin_type.startswith("combo"):
                waiting_time = waiting_time - hold_delay
            elif spin_type.endswith("slide"):
                waiting_time = waiting_time - timeout_delay
            # elif spin_type.startswith("super"):
            #     if "PG" in provider:
            #         waiting_time = waiting_time - 0.3
            #     elif "JILI" in provider:
            #         waiting_time = waiting_time - 0.5
            elif spin_type.startswith("auto") and "PG" in provider:
                waiting_time = 0
                
            sys.stdout.write(f"\t\t<{BLNK}🌀{RES} {RED}{spin_type.replace('_', ' ').upper()}{RES} Waiting Time: {WHTE}{waiting_time}{RES} Interval MS: {WHTE}{interval_ms}{RES} State-Interval: {WHTE}{state.interval}{RES}>\n")
            
            time.sleep(waiting_time)
        else:
            sys.stdout.write(f"\t\t<{BLNK}🌀{RES} {RED}SPIKE SPIN{RES}>\n")
            
        random.choice(action)()
        
        # COMBO SPIN INITIAL spin(normal or auto_spin)
        # if spin_type.startswith("combo"):
        #     init_action = []
        #     init_action.extend([
        #         lambda: pyautogui.click(x=cx, y=BTM_Y - 105, button='left'),
        #         # lambda: pyautogui.click(x=cx, y=BTM_Y - 105, button='right'),
        #         lambda: pyautogui.press('space'),
        #         lambda: (pyautogui.click(x=cx + 195, y=BTM_Y - 105, button='left'), time.sleep(0.3), pyautogui.click(x=cx - 195, y=BTM_Y - 205, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'))
        #     ])
        #     random.choice(init_action)()
        #     time.sleep(0.5)
        #     random.choice(action)()
        
        # if not state.fast_mode and wait_before_spin and spin_type == "normal_spin":
        #     extra_spin = []
        #     if state.widescreen:
        #         if provider == "JILI": # Playtime
        #             cx += 40
        #             cy += 40
        #         extra_spin.extend([
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.press('space'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.press('space'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right')),
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.press('space'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.press('space'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right')),
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.click(x=cx + 520, y=cy + 335, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.click(x=cx + 520, y=cy + 335, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right')),
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.click(x=cx + 520, y=cy + 335, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.click(x=cx + 520, y=cy + 335, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right')),
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.click(x=cx + 520, y=cy + 335, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right')),
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.click(x=cx + 520, y=cy + 335, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.click(x=cx + 520, y=cy + 335, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right')),
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.click(x=cx + 520, y=cy + 335, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.click(x=rand_x2, y=rand_y2, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.click(x=rand_x2, y=rand_y2, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right')),
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.click(x=rand_x2, y=rand_y2, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.click(x=rand_x2, y=rand_y2, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right')),
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.click(x=rand_x2, y=rand_y2, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right')),
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.click(x=rand_x2, y=rand_y2, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.click(x=rand_x2, y=rand_y2, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right')),
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.click(x=rand_x2, y=rand_y2, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
        #             # auto spin style
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right')),
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='left'), pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right')),
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right')),
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='left')),
        #             lambda: (pyautogui.click(x=cx + 240, y=cy + 325, button='right'), pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 240, y=cy + 325, button='right'))
        #         ])
        #     else:
        #         if "PG" in provider:
        #             extra_spin.extend([
        #                 # TURBO ENABLED
        #                 lambda: (pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(0.5), pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left')),
        #                 # lambda: (pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left')),
        #                 # lambda: (pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left')),
        #                 # lambda: (pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left')),
        #                 # lambda: (pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='right'), pyautogui.press('space'), pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left')),
        #                 # TURBO ENABLED
        #                 lambda: (pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left'), pyautogui.press('space'), time.sleep(0.5), pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left'))
        #             ])
        #         else:
        #             extra_spin.extend([
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.press('space'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.press('space'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right')),
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.press('space'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.press('space'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right')),
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right')),
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right')),
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right')),
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right')),
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x2, y=rand_y2, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x2, y=rand_y2, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right')),
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x2, y=rand_y2, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x2, y=rand_y2, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right')),
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x2, y=rand_y2, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right')),
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x2, y=rand_y2, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x2, y=rand_y2, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right')),
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x2, y=rand_y2, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
        #                 # auto spin style
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right')),
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right')),
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='left'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right')),
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='left')),
        #                 lambda: (pyautogui.click(x=cx + 152, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='right'), time.sleep(0.5), pyautogui.doubleClick(x=cx + 152, y=BTM_Y - 105, button='right'))
        #             ]) if not state.spin_btn else \
        #             extra_spin.extend([
        #                 #
        #             ])
                    
        #     random.choice(extra_spin)()
        #     alert_queue.put(f"{spin_type}")
                    
        # now_time = time.time()
        # current_sec = int(now_time) % 10
        # return spin_type
        
        # now_time = time.time()
        # current_sec = int(now_time) % 60
        # sys.stdout.write(f"\t\t<{BLNK}🌀{RES} {RED}{spin_type.replace('_', ' ').upper()}{RES} {MAG}{current_sec}{RES}>\n")

        # print(f"\tHold Delay: {hold_delay:.2f}")
        # print(f"\tSpin Delay: {spin_delay:.2f}")
        # print(f"\tTimeout Delay: {timeout_delay:.2f}")
        # print(f"\tCombo Spin: {combo_spin}")
        # print(f"\n\t\t<{BLNK}🌀{RES} {RED}{spin_type.replace('_', ' ').upper()} {RES}>\n")
        # alert_queue.put(f"{spin_type}")
        # spin_in_progress.clear()
    finally:
        spin_in_progress.clear()

def start_listeners(stop_event):
    with KeyboardListener(on_press=on_key_press) as kb_listener:
        while not stop_event.is_set():
            kb_listener.join(0.1)

def on_key_press(key):
    if key == Key.esc:
        # state.running = False
        os._exit(0)
        
    if key == Key.shift:
        state.auto_mode = not state.auto_mode
        status = "ENABLED" if state.auto_mode else "DISABLED"
        # play_alert(say=f"auto mode {status}")
        alert_queue.put(f"auto mode {status}")
        color = BLMAG if status == "ENABLED" else BLRED
        logger.info(f"\t\t{WHTE}Auto Mode{RES}: {color}{status}{RES}")
        
    if key == Key.caps_lock:
        state.fast_mode = not state.fast_mode
        status = "ENABLED" if state.fast_mode else "DISABLED"
        # play_alert(say=f"auto mode {status}")
        alert_queue.put(f"fast mode {status}")
        color = BLMAG if status == "ENABLED" else BLRED
        logger.info(f"\t\t{WHTE}Fast Mode{RES}: {color}{status}{RES}")
        
    if key == Key.tab:
        alert_queue.put(f"scatter")
        spammer = [
            lambda: (pyautogui.mouseDown(button='left'), pyautogui.mouseUp()),
            lambda: (pyautogui.mouseDown(button='right'), pyautogui.mouseUp()),
            lambda: (pyautogui.keyDown('space'), pyautogui.keyUp('space')),
            lambda: pyautogui.click(clicks=2, interval=0.01, button="left"),
            lambda: pyautogui.click(clicks=2, interval=0.01, button="right"),
            lambda: pyautogui.typewrite(['space'], interval=0.01)
        ]
        for _ in range(3):
            random.choice(spammer)()
            # pyautogui.PAUSE = 0.1
            # pyautogui.FAILSAFE = True
            time.sleep(0.005)  # Super fast (200 actions per second)
            
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

            logger.info(f"{CLEAR}", end="")
            blink_id = int(state["typed"]) if state["typed"].isdigit() and 1 <= int(state["typed"]) <= len(GAME_CONFIGS) else None
            logger.info(render_games(blink_idx=blink_id, blink_on=blink_on))
            logger.info(f"\n\t{DGRY}>>> Select Game: {WHTE}{state['typed']}{RES}", end='', flush=True)

            blink_on = not blink_on
            time.sleep(0.5)

    def on_input(key):
        typed = state["typed"]
        if key == Key.backspace:
            typed = typed[:-1]
        elif key == Key.esc:
            logger.info("\nCancelled.")
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

    logger.info(f"{CLEAR}", end="")
    logger.info(render_games())
    if state['selected_idx']:
        game_name = list(GAME_CONFIGS.keys())[state['selected_idx'] - 1]
        logger.info(f"\n\tSelected: {WHTE}{game_name.upper()}{RES}")
        blink_thread.join()
        return game_name
    
def render_games(provider: str, blink_idx: int=None, blink_on: bool=True):
    # logger.info(f"\n\n\t📘 {MAG}SCATTER JACKPOT MONITOR{RES}\n\n")
    
    games = [(g, cfg) for g, cfg in GAME_CONFIGS.items() if cfg.provider == provider]
    half = (len(games) + 1) // 2
    lines = list()
    
    trending_games = []
    if os.path.exists(TREND_FILE):
        trending_games = [g for g in load_trend_memory().keys()]

    for idx, (left_game, left_conf) in enumerate(games[:half], start=1):
        is_blinking = False
        left_color = PROVIDERS.get(left_conf.provider).color
        left_str = f"[{WHTE}{idx}{RES}] - {left_color}{left_game}{RES}"
        
        if left_game.lower() in trending_games:
            left_str = f" {LMAG}{idx}{RES}  - {LYEL}{BLNK}{left_game} 🔥{RES}"
            is_blinking = True
                
        right_index = idx - 1 + half
        if right_index < len(games):
            right_game, right_conf = games[right_index]
            right_color = PROVIDERS.get(right_conf.provider).color
            right_str = f"[{WHTE}{right_index + 1:>2}{RES}] - {right_color}{right_game}{RES}"
        # else:
        #     right_str = "\t"
        if right_game.lower() in trending_games:
            right_str = f" {LMAG}{right_index + 1:>2}{RES}  - {LYEL}{BLNK}{right_game} 🔥{RES}"

        if is_blinking:
            lines.append(f"\t{left_str:<50}\t\t\t{right_str}")
        else:
            lines.append(f"\t{left_str:<50}\t\t{right_str}")

    return "\n".join(lines)

def games_list(provider: str):
    # games = list(GAME_CONFIGS.items())
    games = [(g, cfg) for g, cfg in GAME_CONFIGS.items() if cfg.provider == provider]
    
    while True:
        try:
            choice = int(input("\n\t🔔 Enter the Game of your choice: "))
            if 1 <= choice <= len(games):
                game = games[choice - 1][0]
                logger.info(f"\n\tSelected: {WHTE}{game}{RES}")
                return game
            else:
                logger.warning("\t⚠️  Invalid choice. Try again.")
        except ValueError:
            logger.warning("\t⚠️  Please enter a valid number.")

def render_providers():
    logger.info(f"\n\n\t📘 {MAG}SCATTER JACKPOT MONITOR{RES}\n\n")

    providers = list(PROVIDERS.items())
    half = (len(providers) + 1) // 2
    lines = list()

    for idx, (left_provider, left_conf) in enumerate(providers[:half], start=1):
        left_color = left_conf.color
        left_str = f"[{WHTE}{idx}{RES}] - {left_color}{left_conf.provider}{RES}\t"
        
        right_index = idx - 1 + half
        if right_index < len(providers):
            right_provider, right_conf = providers[right_index]
            right_color = right_conf.color
            right_str = f"[{WHTE}{right_index + 1:>2}{RES}] - {right_color}{right_conf.provider}{RES}"
        else:
            right_str = ""

        lines.append(f"\t{left_str:<50}\t{right_str}")
    return "\n".join(lines)

def providers_list():
    providers = list(PROVIDERS.items())

    while True:
        try:
            choice = int(input("\n\t🔔 Choose Provider: "))
            if 1 <= choice <= len(providers):
                provider = providers[choice - 1][0]
                provider_name = providers[choice - 1][1].provider
                provider_color = providers[choice - 1][1].color
                logger.info(f"\n\tSelected: {provider_color}{provider_name} {RES}({provider_color}{provider}{RES})\n\n")
                return provider, provider_name
            else:
                logger.warning("\t⚠️  Invalid choice. Try again.")
        except ValueError:
            logger.warning("\t⚠️  Please enter a valid number.")
            
# def update_recent_data(pull_delta, min10):
#     """Add new data to the rolling window"""
#     recent_pull_deltas.append(pull_delta)
#     recent_min10.append(min10)

def get_dynamic_thresholds():
    """Compute dynamic thresholds for pull_delta and min10"""
    if len(recent_pull_deltas) < 5:
        # Not enough data yet, use default conservative values
        return 50, 40
    
    # pull_delta threshold: mean + 1.5*std or 95th percentile
    # pull_array = np.array(recent_pull_deltas)
    pull_array = np.abs(np.array(recent_pull_deltas)) # absolute value test
    pull_thresh = max(pull_array.mean() + 1.5 * pull_array.std(),
                    np.percentile(pull_array, 95))
    
    # min10 threshold: top 25% of recent min10 values
    min10_array = np.array(recent_min10)
    min10_thresh = np.percentile(min10_array, 75)

    return pull_thresh, min10_thresh
            
# ────────────── ASYNC WEBSOCKET CLIENT ──────────────
def start_ws_client(api_server, game, data_queue: ThQueue,):
    async def fetch_api_data():
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        while not stop_event.is_set():
            try:
                async with websockets.connect(api_server, ssl=ssl_context) as ws:
                    await ws.send(json.dumps({"game": game, "provider": provider}))
                    
                    while not stop_event.is_set():
                        message = await ws.recv()
                        data = json.loads(message)

                        state.last_time = Decimal(data.get('last_updated'))
                        state.min10 = data.get('min10')
                        state.last_min10 = data.get("prev_min10")
                        state.pull_delta = data.get('10m_delta')
                        state.last_pull_delta = data.get('prev_10m_delta')
                        state.interval = data.get("interval")
                        
                        try:
                            await create_time_log(data)
                        except Exception as e:
                            logger.info(f"⚠️ {BLRED}Failed to log CSV for {game}: {e}")
                            
                        # Example usage in your main loop
                        # pull_delta = state.pull_delta
                        # min10 = state.min10

                        # update rolling window
                        # update_recent_data(pull_delta, min10)
                        recent_pull_deltas.append(data.get('10m_delta'))
                        recent_min10.append(data.get('min10'))

                        # compute dynamic thresholds
                        state.pull_thresh, state.min10_thresh = get_dynamic_thresholds()
                        
                        data_queue.put(data)
                        
                        logger.debug(f"\n\tstate.last_time: {datetime.fromtimestamp(float(state.last_time))}")
                        logger.debug(f"⚡ Update for {game}: last_time={state.last_time} interval={state.interval} "
                                f"min10={state.min10} prev_min10={state.last_min10} "
                                f"pull_delta={state.pull_delta} last_pull_delta={state.last_pull_delta}")

            except (websockets.ConnectionClosed, ConnectionRefusedError) as e:
                logger.warning(f"⚠️ Connection lost, retrying in 3s... ({e})")
                await asyncio.sleep(3)
            except Exception as e:
                logger.error(f"💥 Unexpected error: {e}")
                await asyncio.sleep(3)

    asyncio.run(fetch_api_data())
    

if __name__ == "__main__":
    # MAIN
    logger = logging.getLogger("monitor")
    logger.setLevel(logging.DEBUG if LOG_LEVEL == "DEBUG" else logging.INFO)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG if LOG_LEVEL == "DEBUG" else logging.INFO)

    formatter = logging.Formatter("%(message)s")
    stream_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)

    # Uncomment if you want logs saved:
    # file_handler = logging.FileHandler("monitor.log", encoding="utf-8")
    # file_handler.setLevel(logging.DEBUG)
    # file_handler.setFormatter(formatter)
    # logger.addHandler(file_handler)
    
    for f in [DATA_FILE, HELPSLOT_DATA_FILE]:
        if os.path.exists(f):
            os.remove(f)
    
    stop_event = threading.Event()
    # reset_event = threading.Event()
    spin_in_progress = threading.Event()

    alert_queue = ThQueue()
    alert_thread = threading.Thread(target=play_alert, daemon=True)
    alert_thread.start()
        
    logger.info(CLEAR)
    logger.info(render_providers())
    
    url = next((url for url in URLS if 'helpslot' in url), None)
    provider, provider_name = providers_list()
    alert_queue.put(provider_name)
    
    logger.info(render_games(provider))
    game = games_list(provider)
    alert_queue.put(game)
    # store current game in file
    with open("current_game.txt", "w", encoding="utf-8") as f:
        f.write(game)
    
    # api_server = WS_URL[0] # local
    api_server = f"wss://{VPS_DOMAIN}/ws" # vps
    
    user_input = input(f"\n\n\tDo you want to enable {CYN}Auto Mode{RES} ❓ ({DGRY}Y/n{RES}): ").strip().lower()
    auto_mode = user_input in ("", "y", "yes") # default to yes
    fast_mode = False
    dual_slots = False
    split_screen = False
    left_slot = right_slot = False
    
    # MODIFY LATER
    driver = setup_driver()
    fetch_html(driver, url, game, provider)
    
    logger.info(f"\n\n\t... {WHTE}Starting real-time jackpot monitor.\n\t    Press ({BLMAG}Ctrl+C{RES}{WHTE}) to stop.{RES}\n\n")
    
    breakout = load_breakout_memory(game)

    state = AutoState()
    settings = configure_game(game, api_server, breakout, auto_mode, fast_mode, dual_slots, split_screen, left_slot, right_slot)#, forever_spin)
    
    if dual_slots and split_screen:# and slot_position is not None:
        # if slot_position == "left":
        if left_slot:
            CENTER_X, CENTER_Y = LEFT_SLOT_POS.get("center_x"), LEFT_SLOT_POS.get("center_y")
        # elif slot_position == "right":
        elif right_slot:
            CENTER_X, CENTER_Y = RIGHT_SLOT_POS.get("center_x"), RIGHT_SLOT_POS.get("center_y")
    else:
        CENTER_X, CENTER_Y = SCREEN_POS.get("center_x"), SCREEN_POS.get("center_y")
    LEFT_X, RIGHT_X, TOP_Y, BTM_Y = 0, SCREEN_POS.get("right_x"), 0, SCREEN_POS.get("bottom_y")
    # LEFT_X, RIGHT_X, TOP_Y, BTM_Y = 0, SCREEN_POS.get("right_x"), 0, SCREEN_POS.get("bottom_y") - 55 # DREAM CASINO
    
    bet_queue = ThQueue()
    data_queue = ThQueue()
    # countdown_queue = ThQueue()
    fetch_queue = ThQueue()
    
    # Start PyAutoGUI & other threads
    threads = []
    
    threads.append(threading.Thread(target=bet_switch, daemon=True))
    threads.append(threading.Thread(target=countdown_timer, daemon=True))
    threads.append(threading.Thread(target=fetch_game_data, args=(driver, game, fetch_queue,), daemon=True))
    threads.append(threading.Thread(target=start_listeners, args=(stop_event,), daemon=True))
    threads.append(threading.Thread(target=start_ws_client, args=(api_server, game, data_queue,), daemon=True))
    
    for t in threads:
        t.start()
    
    # bet_thread = threading.Thread(target=bet_switch, daemon=True)
    # countdown_thread = threading.Thread(target=countdown_timer, daemon=True)
    # fetch_thread = threading.Thread(target=fetch_game_data, args=(driver, game, fetch_queue,), daemon=True)
    # kb_thread = threading.Thread(target=start_listeners, args=(stop_event,), daemon=True)
    # monitor_thread = threading.Thread(target=monitor_game_info, args=(game, data_queue,), daemon=True)
    
    # bet_thread.start()
    # countdown_thread.start()
    # fetch_thread.start()
    # kb_thread.start()
    # monitor_thread.start()
    
    window = 20 # number of iterations
    recent_pull_deltas = deque(maxlen=window)
    recent_min10 = deque(maxlen=window)
    
    try:
        while not stop_event.is_set():
            try:
                # Always check countdown queue in non-blocking way
                # try:
                #     msg = countdown_queue.get_nowait()
                #     logger.info(f"\n✅ {msg}")
                # except Empty:
                #     pass
                
                # Wait for data (block until something arrives)
                # data = data_queue.get(timeout=1)
                helpslot_data = fetch_queue.get_nowait()
                data = data_queue.get_nowait()
                parsed_data = extract_game_data(data)
                
                all_data = load_previous_data("api")
                all_helpslot_data = load_previous_data("helpslot")

                previous_data = all_data.get(game.lower())
                previous_helpslot_data = all_helpslot_data.get(game.lower())

                compare_data(previous_data, parsed_data, previous_helpslot_data, helpslot_data)

                all_data[game.lower()] = parsed_data
                all_helpslot_data[game.lower()] = helpslot_data
                
                save_current_data("api", all_data)
                save_current_data("helpslot", all_helpslot_data)
                
                # create_time_log(all_data) # transfer to async in future for advance data writing
                
                # alert_queue.put(re.sub(r"\s*\(.*?\)", "", game))
                # alert_queue.put("low_break_out") if state.is_low_breakout else None
                # alert_queue.put("low_delta_break_out") if state.is_low_delta_breakout else None
                # alert_queue.put("high_break_out") if state.is_high_breakout else None
                # alert_queue.put("high_delta_break_out") if state.is_high_delta_breakout else None
                # alert_queue.put("reversal potential") if state.is_reversal_potential and state.curr_color == 'green' else None
                # alert_queue.put("reversal!") if state.is_reversal else None
                # if state.bet_lvl is not None:
                #     alert_queue.put(f"caution, bet {state.bet_lvl}, {state.last_trend}") if state.curr_color == 'green' else \
                #     alert_queue.put(f"bet {state.bet_lvl}, {state.last_trend}")
                # else:
                #     alert_queue.put("do not bet")
                # state.last_trend = 

            except Empty:
                # No data in the last 1 second — not an error
                pass
            stop_event.wait(1)
    except KeyboardInterrupt:
        logger.error(f"\n\n\t🤖❌  {BLRED}Main program interrupted.{RES}")
        stop_event.set()
    finally:        
        for f in [DATA_FILE, HELPSLOT_DATA_FILE]:
            if os.path.exists(f):
                os.remove(f)
                
        logger.warning(f"\n\n\t🤖❌  {LYEL}All threads shut down...{RES}")
        