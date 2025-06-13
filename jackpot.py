import atexit, csv, hashlib, json, os,  platform, pyautogui, random, re, subprocess, time#, threading
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dataclasses import dataclass
# from pynput.keyboard import Listener as KeyboardListener, Key, KeyCode
# from pynput.mouse import Listener as MouseListener, Button
from config import (GAME_CONFIGS, DEFAULT_GAME_CONFIG, DATA_FILE, SCREEN_POS, LEFT_SLOT_POS, RIGHT_SLOT_POS, DEFAULT_VOICE, DELAY_RANGE, PROVIDERS, URLS, CASINOS)


@dataclass
class AutoState:
    game: str = None
    url: str = None
    casino: str = None
    dual_slots: bool = False
    spin: bool = False
    auto_spin: bool = True
    turbo: bool = True
    feature: bool = None
    auto_play_menu: bool = False
    widescreen: bool = False
    provider: str = None
    
    auto_mode: bool = True
    # hotkeys: bool = True
    # running: bool = True
    # pressing: bool = False
    # clicking: bool = False
    # current_key: str = None
    # move: bool = False

    current_play: str = None
    prev_play: str = None
    first_count: int = 1
    second_count: int = 1
    third_count: int = 1
    bet: int = 0
    lucky_spins: int = 0
    global_mega_trend: bool = False
    mega_trend: bool = False

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

def configure_game(game, url, casino, dual_slots):
    state.game = game
    state.url = url
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

def fetch_html_via_selenium(driver, game):
    driver.get(state.url)
    time.sleep(2)

    search_box = driver.find_element(By.CLASS_NAME, "gameSearch")
    search_box.send_keys(game)

    if "helpslot" in state.url:
        providers = driver.find_elements(By.CLASS_NAME, "provider-item")

        for provider in providers:
            try:
                text = provider.find_element(By.CLASS_NAME, "text").text.strip()
                if not state.provider == "JILI" and text == state.provider:
                    provider.click()
                    break
            except:
                continue

    time.sleep(2)  # Let results update

    return driver.page_source

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    # for cached driver (brew install chromedriver)
    service = Service("/opt/homebrew/bin/chromedriver")
    return webdriver.Chrome(service=service, options=options)
    # for install driver
    # return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def extract_game_data(html):
    soup = BeautifulSoup(html, "html.parser")
    game_data = []
    game_blocks = soup.select(".game")

    for block in game_blocks:
        name_tag = block.select_one(".gameName")

        if not name_tag:
            continue

        if name_tag.text.strip().lower() == state.game.lower():
            meter_tag = block.select_one(".meterBody")
            meter_color = None

            if meter_tag:
                if "redMeter" in meter_tag.get("class", []):
                    meter_color = "red"
                elif "greenMeter" in meter_tag.get("class", []):
                    meter_color = "green"

            history_tags = block.select(".historyDetails.percentage div")
            if name_tag and meter_tag and len(history_tags) == 4:
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

def get_game_info():
    return next((elem for elem in data if elem["name"].lower() == state.game.lower()), None)

def load_previous_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_current_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    create_log()

def create_log():
    sanitized = re.sub(r'\W+', '_', state.game.strip().lower())
    output_csv = f"{'helpslot' if 'helpslot' in state.url else 'slimeserveahead'}_{sanitized}_log.csv"

    raw_data = get_game_info()

    # if not game_data:
    #     raise ValueError(f"No data found for game: {game_key}")

    # # Prepare one row from JSON
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    value = float(raw_data["jackpot_meter"].strip('%'))

    history = raw_data.get("history", {})

    # # Compose CSV row
    row = {
        "timestamp": timestamp,
        "value": value,
        "5s_change": "",  # No real-time tracking
        "1m_change": "",  # No real-time tracking
        
        "10m_change": history.get("10m", ""),
        "1h_change": history.get("1h", ""),
        "3h_change": history.get("3h", ""),
        "6h_change": history.get("6h", ""),
    }

    # # Write to CSV
    fieldnames = ["timestamp", "value", "5s_change", "1m_change", "10m_change", "1h_change", "3h_change", "6h_change"]

    write_header = not os.path.exists(output_csv)

    with open(output_csv, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(row)

    print(f"✅ Wrote data for {raw_data['name']} to {output_csv}")

def hash_data(data):
    return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

def spin(is_lucky_bet=None, bet_level=None, chosen_spin=None, slot_position=None):
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
    
    print(f"POSITION during switching slots below coordinates: {slot_position}")
    print(f"Y-axis (screen_height - 1): {y2}")

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
            
    print("\n\t*** Lucky Bet! ***") if is_lucky_bet else None
    print(f"\tBet: {bet} ({chosen_spin.replace('_', ' ').upper()})\n")
    print(f"\tSlot: {slot_position}\n") if state.dual_slots else None
        
def play_alert(is_lucky_bet=None, bet_level=None, luck_count=None, say=None):
        sound_map = {
            "high": "bet high",
            "mid": "bet mid",
            "low": "bet low",
            None: "do not bet"
        }

        sound_file = (
            # "play number one" if say is not None and say == "set_play" and state.current_play == "first" else \
            # "play number two" if say is not None and say == "set_play" and state.current_play == "second" else \
            # "play number three" if say is not None and say == "set_play" and state.current_play == "third" else \
            "global mega trend" if state.global_mega_trend else \
            "mega trend" if state.mega_trend and state.current_play == "first" else \
            "auto mode disabled" if say is not None and say == "auto mode DISABLED" else \
            "auto mode enabled" if say is not None and say == "auto mode ENABLED" else \
            "hotkeys disabled" if say is not None and say == "hotkeys DISABLED" else \
            "hotkeys enabled" if say is not None and say == "hotkeys ENABLED" else \
            "turbo mode on" if say is not None and say == "turbo mode ON" else \
            "normal speed on" if say is not None and say == "normal speed ON" else \
        	"trend detected" if bet_level is None and not is_lucky_bet and luck_count is not None and luck_count > 0 else \
            "lucky bet!" if bet_level is None and is_lucky_bet else \
            "double spin" if bet_level is not None and is_lucky_bet else \
            # f"{board_spin}" if board_spin is not None else \
            sound_map.get(bet_level)
        )

        voices = [ "Trinoids", "Kanya", "Karen", "Kathy", "Nora" ]
        voice = random.choice(voices) if state.current_play is None else DEFAULT_VOICE
        subprocess.run(["say", "-v", voice, sound_file])

def parse_percentage(value):
    try:
        return float(value.replace('%', '').replace(',', ''))
    except:
        return None

def compare_data(prev, current):
    slots = [ "left", "right" ]
    # random.shuffle(slots)

    # luck_count = state.lucky_spins
    # is_lucky_bet = True if luck_count > 1 else False
    # luck_count = 0 if bet_level is None else luck_count
    bet_level = None

    # set_plays = [ "first", "second", "third" ] if "slimeserveahead" in state.url else [ "second", "third" ]
    # play_now = random.choice(set_plays) if state.current_play is None else state.current_play

    # print("Play Now => ", play_now, state.first_count if play_now == "first" else state.second_count if play_now == "second" else state.third_count)
    
    if prev and 'jackpot_meter' in prev:
        current_jackpot = parse_percentage(current['jackpot_meter'])
        prev_jackpot = parse_percentage(prev['jackpot_meter'])
        delta = round(current_jackpot - prev_jackpot, 2)
        sign = '+' if delta > 0 else ''
        diff = f"{prev_jackpot} Δ: {sign}{delta}%"



        print(f'\n\n{"-":>12}----------------------------------')
        print(f"{"":>12}[ {current['name'].upper()} ] @ {PROVIDERS.get(state.provider)}")
        print(f"{"":>5}{'helpslot' if 'helpslot' in state.url else 'slimeserveahead'} ({state.url})")
        print(f"{"":>12}@ ({state.casino})")
        print(f'{"-":>12}----------------------------------')
        print(f"\n\tJackpot Meter | \033[1m{current_jackpot}\033[0m (Prev: \033[1m{diff}\033[0m)\n")
        



        
        # # print(f"\n\txxx Don't Bet! xxx\n") if not is_lucky_bet else None
        

        # MEGATREND GLOBAL
    #     if play_now != "first" and prev['color'] == "green" and current['color'] == "red":
    #         print('\nCOLOR (prev) >> ', prev['color'])
    #         print('COLOR (current) >> ', current['color'])
    #         print('\nCOLOR (check) >> ', prev['color'] == "green" and current['color'] == "red")

    #         is_lucky_bet = True
    #         state.global_mega_trend = True

    #         bet_level = "max"

    #         if state.dual_slots and state.auto_mode:
    #             pyautogui.press('space')
    #             spin(is_lucky_bet=True, bet_level=bet_level, chosen_spin=None, slot_position=slots[0])
    #             spin(is_lucky_bet=True, bet_level=bet_level, chosen_spin=None, slot_position=slots[1])
    #         else:
    #             spin(is_lucky_bet=True, bet_level=bet_level, chosen_spin=None) if state.auto_mode else print(f"Auto Mode is {state.auto_mode}")
    #     else:
    #         if state.global_mega_trend and delta <= -20:
    #             is_lucky_bet = False
    #             state.global_mega_trend = False

    #             if "slimeserveahead" in state.url:
    #                 if state.dual_slots and state.auto_mode:
    #                     spin(is_lucky_bet=True, bet_level=bet_level, chosen_spin=None, slot_position=slots[0])
    #                     spin(is_lucky_bet=True, bet_level=bet_level, chosen_spin=None, slot_position=slots[1])
    #                 else:
    #                     spin(is_lucky_bet=True, bet_level=bet_level, chosen_spin=None) if state.auto_mode else print(f"Auto Mode is {state.auto_mode}")

    #             if "helpslot" in state.url and current['color'] == "red":
    #                 if state.dual_slots and state.auto_mode:
    #                     pyautogui.press('space') #if not state.spin
    #                     spin(is_lucky_bet=True, bet_level=bet_level, chosen_spin=None, slot_position=slots[0])
    #                     spin(is_lucky_bet=True, bet_level=bet_level, chosen_spin=None, slot_position=slots[1])
    #                 else:
    #                     spin(is_lucky_bet=True, bet_level=bet_level, chosen_spin=None) if state.auto_mode else print(f"Auto Mode is {state.auto_mode}")

    #     # SET 1
    #     if play_now == "first":
    #         if "slimeserveahead" in state.url:
    #             is_trending = True if current_jackpot < prev_jackpot else False
    #             print('is_trending --> ', is_trending)
    #             print('\nCOLOR (prev) >> ', prev['color'])
    #             print('COLOR (current) >> ', current['color'])
    #             print('COLOR (check) >> ', prev['color'] == "green" and current['color'] == "red")
    #             # if is_trending and prev['color'] == "green" and current['color'] == "red" and delta <= -30:
    #             # if state.mega_trend and current['color'] == "red":
    #             if state.mega_trend and is_trending and current['color'] == "red" and delta <= -20:
    #                 is_lucky_bet = True
    #                 state.mega_trend = False

    #                 if state.dual_slots and state.auto_mode:
    #                     pyautogui.press('space')
    #                     spin(is_lucky_bet=True, bet_level=bet_level, chosen_spin=None, slot_position=slots[0])
    #                     spin(is_lucky_bet=True, bet_level=bet_level, chosen_spin=None, slot_position=slots[1])
    #                 else:
    #                     spin(is_lucky_bet=True, bet_level=bet_level, chosen_spin=None) if state.auto_mode else print(f"Auto Mode is {state.auto_mode}")
    #             elif not state.mega_trend and is_trending and prev['color'] == "green" and current['color'] == "red":
    #                 # is_trending = True if current_jackpot > prev_jackpot else False
    #             # delta_reverse = round(prev_jackpot - current_jackpot, 2)
    #             # if is_trending and current['color'] == "red" and delta_reverse > 0:
    #                 is_lucky_bet = True
    #                 state.mega_trend = True

    #                 if state.dual_slots and state.auto_mode:
    #                     pyautogui.press('space')
    #                     spin(is_lucky_bet=True, bet_level=bet_level, chosen_spin=None, slot_position=slots[0])
    #                     spin(is_lucky_bet=True, bet_level=bet_level, chosen_spin=None, slot_position=slots[1])
    #                 else:
    #                     spin(is_lucky_bet=True, bet_level=bet_level, chosen_spin=None) if state.auto_mode else print(f"Auto Mode is {state.auto_mode}")
    #             else:
    #                 is_lucky_bet = False
    #                 state.mega_trend = False

    #             state.first_count += 1

    #     if play_now == "second":
    #         # SET 2
    #         luckybet_threshold = 9.5 if "slimeserveahead" in state.url else 0
    #         is_trending = True if current_jackpot < prev_jackpot else False
    #         is_check_trend = True if not is_lucky_bet and is_trending and current_jackpot + luckybet_threshold < prev_jackpot else False
    #         # is_check_trend = True if not is_lucky_bet and is_trending and delta <= -30 else False
    #         is_lucky_bet = True if is_trending and is_check_trend else is_lucky_bet

    #         print(f'\nluckybet_threshold [{luckybet_threshold}] vs delta [{delta}] ')
    #         print('is_trending --> ', is_trending)
    #         print('is_check_trend --> ', is_check_trend)
    #         print('is_lucky_bet --> ', is_lucky_bet)
    #         print('\nCOLOR (prev) >> ', prev['color'])
    #         print('COLOR (current) >> ', current['color'])
    #         print('COLOR (check) >> ', prev['color'] == "green" and current['color'] == "red")

    #         luck_count = luck_count + 1 if is_check_trend else 0 if not is_trending else luck_count

    #         if "slimeserveahead" in state.url:
    #             if state.dual_slots and state.auto_mode and is_lucky_bet:
    #                 spin(is_lucky_bet=is_lucky_bet, bet_level=bet_level, chosen_spin=None, slot_position=slots[0])
    #                 spin(is_lucky_bet=is_lucky_bet, bet_level=bet_level, chosen_spin=None, slot_position=slots[1])
    #             else:
    #                 spin(is_lucky_bet=is_lucky_bet, bet_level=bet_level, chosen_spin=None) if is_trending and is_lucky_bet and state.auto_mode else print(f"Auto Mode is {state.auto_mode}")

    #         if "helpslot" in state.url and current['color'] == "red":
    #             if state.dual_slots and state.auto_mode and is_lucky_bet:
    #                 pyautogui.press('space')
    #                 spin(is_lucky_bet=is_lucky_bet, bet_level=bet_level, chosen_spin=None, slot_position=slots[0])
    #                 spin(is_lucky_bet=is_lucky_bet, bet_level=bet_level, chosen_spin=None, slot_position=slots[1])
    #             else:
    #                 spin(is_lucky_bet=is_lucky_bet, bet_level=bet_level, chosen_spin=None) if is_trending and is_lucky_bet and state.auto_mode else print(f"Auto Mode is {state.auto_mode}")

    #         state.second_count += 1

    #     if play_now == "third":
    #         # SET 3
    #         if parse_percentage(current['jackpot_meter']) < parse_percentage(prev['jackpot_meter']): # regardless just press
    #             if luck_count > 1:

    #                 if "slimeserveahead" in state.url:
    #                     if state.dual_slots and state.auto_mode:
    #                         spin(is_lucky_bet=is_lucky_bet, chosen_spin=None, slot_position=slots[0])
    #                         spin(is_lucky_bet=is_lucky_bet, chosen_spin=None, slot_position=slots[1])
    #                     else:
    #                         spin(is_lucky_bet=is_lucky_bet, chosen_spin=None) if state.auto_mode else print(f"Auto Mode is {state.auto_mode}")

    #                 if "helpslot" in state.url and current['color'] == "red":
    #                     if state.dual_slots and state.auto_mode:
    #                         pyautogui.press('space')
    #                         spin(is_lucky_bet=is_lucky_bet, chosen_spin=None, slot_position=slots[0])
    #                         spin(is_lucky_bet=is_lucky_bet, chosen_spin=None, slot_position=slots[1])
    #                     else:
    #                         spin(is_lucky_bet=is_lucky_bet, chosen_spin=None) if state.auto_mode else print(f"Auto Mode is {state.auto_mode}")

    #             elif luck_count == 0 and parse_percentage(current['jackpot_meter']) + 9.5 < parse_percentage(prev['jackpot_meter']):
    #                 luck_count = 2

    #                 if "slimeserveahead" in state.url:
    #                     if state.dual_slots and state.auto_mode:
    #                         spin(is_lucky_bet=is_lucky_bet, chosen_spin=None, slot_position=slots[0])
    #                         spin(is_lucky_bet=is_lucky_bet, chosen_spin=None, slot_position=slots[1])
    #                     else:
    #                         spin(is_lucky_bet=is_lucky_bet, chosen_spin=None) if state.auto_mode else print(f"Auto Mode is {state.auto_mode}")

    #                 if "helpslot" in state.url and current['color'] == "red":
    #                     if state.dual_slots and state.auto_mode:
    #                         pyautogui.press('space')
    #                         spin(is_lucky_bet=is_lucky_bet, chosen_spin=None, slot_position=slots[0])
    #                         spin(is_lucky_bet=is_lucky_bet, chosen_spin=None, slot_position=slots[1])
    #                     else:
    #                         spin(is_lucky_bet=is_lucky_bet, chosen_spin=None) if state.auto_mode else print(f"Auto Mode is {state.auto_mode}")
    #             else:
    #                 luck_count += 1

    #             if parse_percentage(current['jackpot_meter']) < parse_percentage(prev['jackpot_meter']) and not is_lucky_bet:
    #                 print(f'\nDEBUG (Lucky Bet SPIN 1) ...{is_lucky_bet}\n')
    #                 is_lucky_bet = True

    #                 if "slimeserveahead" in state.url:
    #                     if state.dual_slots and state.auto_mode:
    #                         spin(bet_level=bet_level, chosen_spin=None, slot_position=slots[0])
    #                         spin(bet_level=bet_level, chosen_spin=None, slot_position=slots[1])
    #                     else:
    #                         spin(bet_level=bet_level, chosen_spin=None) if state.auto_mode else print(f"Auto Mode is {state.auto_mode}")

    #                 if "helpslot" in state.url and current['color'] == "red":
    #                     if state.dual_slots and state.auto_mode:
    #                         pyautogui.press('space')
    #                         spin(bet_level=bet_level, chosen_spin=None, slot_position=slots[0])
    #                         spin(bet_level=bet_level, chosen_spin=None, slot_position=slots[1])
    #                     else:
    #                         spin(bet_level=bet_level, chosen_spin=None) if state.auto_mode else print(f"Auto Mode is {state.auto_mode}")

    #             elif is_lucky_bet:
    #                 print(f'\nDEBUG (Lucky Bet SPIN 2) ...{is_lucky_bet}\n')
    #                 time.sleep(3)

    #                 if "slimeserveahead" in state.url:
    #                     if state.dual_slots and state.auto_mode:
    #                         spin(bet_level=bet_level, chosen_spin=None, slot_position=slots[0])
    #                         spin(bet_level=bet_level, chosen_spin=None, slot_position=slots[1])
    #                     else:
    #                         spin(bet_level=bet_level, chosen_spin=None) if state.auto_mode else print(f"Auto Mode is {state.auto_mode}")                    

    #                 if "helpslot" in state.url and current['color'] == "red":
    #                     if state.dual_slots and state.auto_mode:
    #                         pyautogui.press('space')
    #                         spin(bet_level=bet_level, chosen_spin=None, slot_position=slots[0])
    #                         spin(bet_level=bet_level, chosen_spin=None, slot_position=slots[1])
    #                     else:
    #                         spin(bet_level=bet_level, chosen_spin=None) if state.auto_mode else print(f"Auto Mode is {state.auto_mode}")

    #             elif parse_percentage(current['jackpot_meter']) < parse_percentage(prev['jackpot_meter']) and is_lucky_bet:
    #                 print(f'\nDEBUG (Lucky Bet SPIN 2) ...{is_lucky_bet}\n')

    #                 if "slimeserveahead" in state.url:
    #                     if state.dual_slots and state.auto_mode:
    #                         spin(bet_level=bet_level, chosen_spin=None, slot_position=slots[0])
    #                         spin(bet_level=bet_level, chosen_spin=None, slot_position=slots[1])
    #                     else:
    #                         spin(bet_level=bet_level, chosen_spin=None) if state.auto_mode else print(f"Auto Mode is {state.auto_mode}")

    #                 if "helpslot" in state.url and current['color'] == "red":
    #                     if state.dual_slots and state.auto_mode:
    #                         pyautogui.press('space')
    #                         spin(bet_level=bet_level, chosen_spin=None, slot_position=slots[0])
    #                         spin(bet_level=bet_level, chosen_spin=None, slot_position=slots[1])
    #                     else:
    #                         spin(bet_level=bet_level, chosen_spin=None) if state.auto_mode else print(f"Auto Mode is {state.auto_mode}")
    #         else:
    #             is_lucky_bet = False
    #             luck_count = 0

    #         state.third_count += 1
    else:
        print(f'\n\n{"-":>12}----------------------------------')
        print(f"{"":>12}[ {current['name'].upper()} ] @ {PROVIDERS.get(state.provider)}")
        print(f"{"":>5}{'helpslot' if 'helpslot' in state.url else 'slimeserveahead'} ({state.url})")
        print(f"{"":>12}@ ({state.casino})")
        print(f'{"-":>12}----------------------------------')
        print(f"\n\tJackpot Meter | \033[1m{current['jackpot_meter']}\033[0m\n")

    # for index, (period, value) in enumerate(current['history'].items()):
    for index, (period, value) in enumerate(current['history'].items()):
        print("PERIOD: ", period)
        print("INDEX: ", index)
        old_value = prev['history'].get(period) if prev else None
        diff = ""
        if old_value is not None:
            new_num = parse_percentage(value)
            old_num = parse_percentage(old_value)
            if new_num is not None and old_num is not None:
                delta = round(new_num - old_num, 2)
                sign = '+' if delta > 0 else ''
                diff = f" (Prev: {old_value}, Δ: {sign}{delta}%)"
                # COMMENT FOR NOW THIS IS GOOD IN GAME BUT I DON'T KNOW WHY?
                # if index == 0 or index == 1 and new_num < old_num:# and delta <= 20:
                #     if index == 0:#: and delta <= 20:
                #         new_num_10m = new_num
                #         old_num_10m = old_num
                #         delta_10m = delta
                #     elif index == 1 and new_num_10m is not None and old_num_10m is not None and delta_10m is not None: #and delta <= 5:
                #         new_delta_10m_1h = round(new_num_10m - new_num, 2) #
                #         old_delta_10m_1h = round(old_num_10m - old_num, 2)
                #         if new_delta_10m_1h < old_delta_10m_1h:
                #             bet_level = "max" if delta_10m <= 80 else "high" if delta_10m <= 60 else "mid" if delta_10m <= 40 else "low" if delta_10m <=20 else None
                #             if bet_level is not None:
                #                 if state.dual_slots and state.auto_mode:
                #                     pyautogui.press('space')
                #                     spin(bet_level=bet_level, chosen_spin=None, slot_position=slots[0])
                #                     spin(bet_level=bet_level, chosen_spin=None, slot_position=slots[1])
                #                 else:
                #                     spin(bet_level=bet_level, chosen_spin=None) if state.auto_mode else print(f"Auto Mode is {state.auto_mode}")
                #     else:
                #         new_num_10m = None
                #         delta_10m = None

                if index == 0 or index == 1 and new_num < old_num:# and delta <= 20:
                    if index == 0:#: and delta <= 20:
                        new_num_10m = new_num
                        old_num_10m = old_num
                        delta_10m = delta
                    elif index == 1 and new_num_10m is not None and old_num_10m is not None and delta_10m is not None: #and delta <= 5:
                        # old code always win going to optimize
                        # new_delta_10m_1h = round(new_num_10m - new_num, 2) #if new_num_10m < new_num else None
                        # old_delta_10m_1h = round(old_num_10m - old_num, 2) #if new_num_10m < new_num else None
                        # if new_delta_10m_1h < old_delta_10m_1h: # old code always win going to optimize
                        # if new_delta_10m_1h < old_delta_10m_1h: # old code always win going to optimize
                        # print('index | new_delta_10m_1h: ', index, new_delta_10m_1h)
                        # print('index | old_delta_10m_1h: ', index, old_delta_10m_1h)
                        # LOGIC TO INDETIFY PULL POWER
                        # 1.	Direction Shift:
                        #     If 10m trend is falling but 1h is rising, or vice versa → indicates a reversal zone or pullback potential.
                        # 2.	Delta Amplification:
                        #     A growing delta between short and long timeframes means pull momentum is building.
                        # 3.	Historical Comparison:
                        #     If the delta shift (new vs old) is increasing significantly → potential breakout or deep pullback.

                        h10, h1 = pct(new_num_10m), pct(new_num)
                        ph10, ph1 = pct(old_num_10m), pct(old_num)

                        new_delta_10m_1h = h10 - h1
                        old_delta_10m_1h = ph10 - ph1

                        print('index | new_delta_10m_1h: ', index, new_delta_10m_1h)
                        print('index | old_delta_10m_1h: ', index, old_delta_10m_1h)

                        delta_shift = new_delta_10m_1h - old_delta_10m_1h

                        score = 0
                        trend = None

                        if h10 < 0 < h1 or h10 > 0 > h1:
                            trend = "Reversal Potential"
                            score += 2

                        if abs(delta_shift) > 20:
                            trend = "Strong Pull"
                            score += 3

                        if abs(new_delta_10m_1h) < abs(old_delta_10m_1h):
                            trend = "Weakening Pull"
                            score -= 1

                        if abs(current_jackpot - prev_jackpot) < 0.05 and abs(delta_shift) > 15:
                            trend = "Hidden Pull (No visible jackpot Δ)"
                            score += 1

                        result = {
                            'delta_10m_1h': new_delta_10m_1h,
                            'delta_shift': delta_shift,
                            'pull_score': score,
                            'pull_trend': trend or 'Neutral'
                        }

                        print('Results: ', result)

                        pull_score = result.get('pull_score')

                        if pull_score >= 4: # ≥ 4 Strong Pull / Reversal Potential
                            bet_level = "high"
                        elif pull_score >= 2 and pull_score <= 3: # 2–3 Moderate Pull
                            bet_level = "mid" 
                        elif pull_score >= 1 and pull_score <= 0: # 0-1 Neutral
                            bet_level = "low" 
                        else: # < 0 Weakening / No Pull
                            bet_level = None
                            
                        if bet_level is not None:
                            if state.dual_slots and state.auto_mode:
                                pyautogui.press('space')
                                spin(bet_level=bet_level, chosen_spin=None, slot_position=slots[0])
                                spin(bet_level=bet_level, chosen_spin=None, slot_position=slots[1])
                            else:
                                spin(bet_level=bet_level, chosen_spin=None) if state.auto_mode else print(f"Auto Mode is {state.auto_mode}")
                    else:
                        new_num_10m = None
                        delta_10m = None
                    # print("new_num_10m @ 10m >> ", new_num_10m, index)
                    # print("new_delta_10m @ 10m >> ", new_delta_10m, index)
                    # print("new_num @ 10m >> ", new_num, index)
                    # print("old_num @ 10m >> ", old_num, index)

                # if index == 1 and new_num_10m is not None and new_delta_10m is not None and delta < 0:
                #     if new_num < old_num and new_num_10m < new_num:
                #         bet_level = "max" if new_delta_10m <= 80 else "high" if new_delta_10m <= 60 else "mid" if new_delta_10m <= 40 else "low" if new_delta_10m <=20 else None
                #         luck_count += 1 if bet_level is not None else 0
                #         if luck_count > 1 and luck_count <= 3:
                #             if state.dual_slots and state.auto_mode:
                #                 pyautogui.press('space')
                #                 spin(bet_level=bet_level, chosen_spin=None, slot_position=slots[0])
                #                 spin(bet_level=bet_level, chosen_spin=None, slot_position=slots[1])
                #             else:
                #                 spin(bet_level=bet_level, chosen_spin=None) if state.auto_mode else print(f"Auto Mode is {state.auto_mode}")

                #         print("new_num_10m @ 1h >> ", new_num_10m, period)
                #         print("new_delta_10m @ 1h >> ", new_delta_10m, period)
                #         print("new_num @ 1h >> ", new_num, period)
                #         print("old_num @ 1h >> ", old_num, period)

                # print("new_num_10m | END >> ", new_num_10m)
                # print("new_delta_10m | END >> ", new_delta_10m)
                # print("new_num | END >> ", new_num, period)
                # print("old_num | END >> ", old_num, period)
        else:
            diff = f"\t(Prev: {old_value})"
                    
        print(f"\t{period}: {value}{diff}")

    print(f"\n\txxx Don't Bet! xxx\n") if bet_level is None else None
    print(f"\n\t>>> Bet [ {bet_level.upper()} ]\n") if bet_level is not None else None
    play_alert(bet_level=bet_level)




            #         if "helpslot" in state.url:
            #             if index == 0 and new_num < old_num and new_num < 0 and delta < 0 and abs(delta) >= 30:
            #                 if abs(delta) >= 90:
            #                     bet_level = "max"
            #                 elif abs(delta) >= 70:
            #                     bet_level = "high"
            #                 elif abs(delta) >= 50:
            #                     bet_level = "mid"
            #                 else:
            #                     bet_level = "low"
                                
            #                 if not is_lucky_bet:
            #                     luck_count = 0

            #                     if state.dual_slots and state.auto_mode:
            #                         pyautogui.press('space')
            #                         spin(is_lucky_bet=is_lucky_bet, bet_level=bet_level, chosen_spin=None, slot_position=slots[0])
            #                         spin(is_lucky_bet=is_lucky_bet, bet_level=bet_level, chosen_spin=None, slot_position=slots[1])
            #                     else:
            #                         spin(is_lucky_bet=is_lucky_bet, bet_level=bet_level, chosen_spin=None) if state.auto_mode else print(f"Auto Mode is {state.auto_mode}")
            #                 elif bet_level is not None and is_lucky_bet:
            #                     luck_count += 1
            #                     time.sleep(3)

            #                     if state.dual_slots and state.auto_mode:
            #                         pyautogui.press('space')
            #                         spin(is_lucky_bet=is_lucky_bet, bet_level=bet_level, chosen_spin=None, slot_position=slots[0])
            #                         spin(is_lucky_bet=is_lucky_bet, bet_level=bet_level, chosen_spin=None, slot_position=slots[1])
            #                     else:
            #                         spin(is_lucky_bet=is_lucky_bet, bet_level=bet_level, chosen_spin=None) if state.auto_mode else print(f"Auto Mode is {state.auto_mode}") # double spin if lucky bet and bet level
            #                     print('\t+++ Double Spin +++\n')
            #     else:
            #         diff = f"\t(Prev: {old_value})"
                    
            # print(f"\t{period}: {value}{diff}")


                
    # if state.first_count == 3 or state.second_count == 3 or state.third_count == 3:
    #     print("++ Reset All")
    #     state.first_count = 1
    #     state.second_count = 1
    #     state.third_count = 1
    #     state.prev_play = state.current_play
    #     state.current_play = None
    # else:
    #     state.current_play = play_now

    # state.lucky_spins = luck_count
    # play_alert(is_lucky_bet=is_lucky_bet, bet_level=bet_level, luck_count=luck_count)
    # play_alert(bet_level=bet_level, luck_count=luck_count)
    # if luck_count > 0 and luck_count <= 3:


    # print(f"\n\t>>> Bet [ {bet_level.upper()} ]\n") if bet_level is not None else None
    # print(f"\n\txxx Don't Bet! xxx\n") if not is_lucky_bet else None
    # print(f"\n\txxx Don't Bet! xxx\n") if bet_level is None else None
        # if not is_lucky_bet:
        #     print(f"\n\txxx Don't Bet! xxx\n")
        #     # play_alert()
        #     state.lucky_bet = False
        #     state.lucky_spins = 0
        # else:
        #     # play_alert()
        #     state.lucky_bet = True

# Convert to float
def pct(p): return float(p.strip('%')) if isinstance(p, str) and '%' in p else float(p)

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
#                 else:
#                     set_location(state.current_key)

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

if __name__ == "__main__":
    os.system('cls' if platform.system() == "Windows" else 'clear')
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    print("\n\n\t>>> Jackpot Alert by: MMM <<<\n")
    print("\n\t>>> Select Game <<<\n")
    
    games = list(GAME_CONFIGS.keys())

    half = (len(games) + 1) // 2  # ensures right column covers odd-length lists
    for i, left_game in enumerate(games[:half], start=1):
        left = f"\t[{i}] - {left_game}"
        right_index = (i - 1) + half
        right = f"[{right_index + 1}] - {games[right_index]}" if right_index < len(games) else ""
        print(f"{left:<35} {right}")

    while True:
        try:
            choice = int(input("\n\tEnter the game of your choice: "))
            if 1 <= choice <= len(games):
                game = games[choice - 1]
                print(f"\n\tSelected: {game.upper()}")
                break
            else:
                print("\tInvalid choice. Try again.")
        except ValueError:
            print("\tPlease enter a valid number.")

    print("\n\t>>> Select Source URL <<<\n")

    source_urls = list(URLS)

    for i, url in enumerate(source_urls, start=1):
        print(f"\t[{i}]\t- {"":>1} {'helpslot' if 'helpslot' in url else 'slimeserveahead'} ({url})")

    while True:
        try:
            choice = int(input("\n\tEnter the source URL of your choice: "))
            if 1 <= choice <= len(source_urls):
                url = source_urls[choice - 1]
                print(f"\n\tSelected: {url}")
                break
            else:
                print("\tInvalid choice. Try again.")
        except ValueError:
            print("\tPlease enter a valid number.")

    print("\n\t>>> Select Casino <<<\n")

    casinos = list(CASINOS)

    for i, casino in enumerate(casinos, start=1):
        print(f"\t[{i}]\t- {"":>1} {casino}")

    while True:
        try:
            choice = int(input("\n\tEnter the Casino of your choice: "))
            if 1 <= choice <= len(casinos):
                casino = casinos[choice - 1]
                print(f"\n\tSelected: {casino}")
                break
            else:
                print("\tInvalid choice. Try again.")
        except ValueError:
            print("\tPlease enter a valid number.")

    dual_slots = int(input("\n\tEnter number of slots: "))

    print("\n\tStarting real-time jackpot monitor. Press Ctrl+C to stop.\n")

    state = AutoState()
    settings = configure_game(game=game, url=url, casino=casino, dual_slots=dual_slots)

    # threading.Thread(target=keyboard, args=(settings,), daemon=True).start()
    # threading.Thread(target=mouse, daemon=True).start()

    driver = setup_driver()
    previous_hash = None

    try:
        while True:
            html = fetch_html_via_selenium(driver, game)
            data = extract_game_data(html)
            current_info = get_game_info()

            if current_info:
                current_hash = hash_data(current_info)
                if current_hash != previous_hash:
                    previous_data = load_previous_data().get(game.lower())
                    compare_data(previous_data, current_info)
                    all_data = load_previous_data()
                    all_data[game.lower()] = current_info
                    save_current_data(all_data)
                    previous_hash = current_hash
            else:
                print("Game not found. Please check the name.")

            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
    finally:
        driver.quit()
        atexit.register(driver.quit)
