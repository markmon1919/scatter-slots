#!/usr/bin/env .venv/bin/python

import atexit, json, os, platform, random, re, requests, shutil, subprocess, threading, time
from queue import Queue as ThQueue, Empty
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from meter import fetch_jackpot
from config import (PROVIDERS, DEFAULT_PROVIDER_PROPS, URLS, USER_AGENTS, VOICES, PING,
                    LRED, LBLU, LCYN, LYEL, LMAG, LGRE, LGRY, RED, MAG, YEL, GRE, CYN, BLU, WHTE, BLRED, BLYEL, BLGRE, BLMAG, BLBLU, BLCYN, BYEL, BGRE, BMAG, BCYN, BWHTE, DGRY, BLNK, CLEAR, RES)


def setup_driver():
    options = Options()
    if platform.system() != "Darwin" or os.getenv("IS_DOCKER") == "1":
        options.binary_location = "/opt/google/chrome/chrome"
        options.add_argument('--disable-dev-shm-usage')

    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--blink-settings=imagesEnabled=false')  # Disable images
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    # options.add_argument(f"--user-data-dir={os.getcwd()}/chrome_profile_{session_id}")
    # options.add_argument(f"--profile-directory=Profile_{game.lower()}")

    service = Service(shutil.which("chromedriver"))
    return webdriver.Chrome(service=service, options=options)

def render_providers():
    print(f"\n\n\t📘 {MAG}SCATTER TREND CHECK{RES}\n\n")

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
                print(f"\n\tSelected: {provider_color}{provider_name}{RES}\n\n")
                return provider, provider_name
            else:
                print("\t⚠️  Invalid choice. Try again.")
        except ValueError:
            print("\t⚠️  Please enter a valid number.")

def get_game_data_from_local_api(provider: str, games: list):
    user_agent = random.choice(USER_AGENTS)
    REQUEST_FROM = random.choice(["H5", "H6"])
    URL = next((url for url in URLS if 'helpslot' in url), None)
    HEADERS = {
        "Accept": "application/json",
        "User-Agent": user_agent
    }

    try:
        response = requests.get(
            f"{URL}/api/games?manuf={provider}&requestFrom={REQUEST_FROM}",
            headers=HEADERS
        )

        if response.status_code == 200:
            try:
                json_data = response.json()
                data = json_data.get("data", [])
                games_found = {g["name"]: g for g in games}

                enriched = [
                    {**g,
                     "jackpot_value": games_found[g["name"]].get("value"),
                     "meter_color": games_found[g["name"]].get("up")}
                    for g in data if g.get("name") in games_found
                ]
            except ValueError:
                print(f"❌ Server did not return JSON: {response.text}")
                json_data = {"error": "Invalid JSON response"}
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            json_data = {"error": f"HTTP {response.status_code}"}

        # print(f"📡 Response >> [{BWHTE}{REQUEST_FROM}{RES}] {json_data}")
        enriched.sort(key=lambda g: g["jackpot_value"], reverse=True)
        return enriched

    except Exception as e:
        print(f"❌ Error calling API: {e}")
        return {"error": str(e)}, REQUEST_FROM
    
def fetch_html_via_selenium(driver: webdriver.Chrome, url: str, provider: str):
    driver.get(url)
    time.sleep(1)
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

    time.sleep(1)
    return driver.page_source

def extract_game_data(driver=None) -> list:
    games = []
    game_blocks = driver.find_elements(By.CSS_SELECTOR, ".game-block")
    for block in game_blocks:
        try:
            name = block.find_element(By.CSS_SELECTOR, ".game-title").text.strip()
            value_text = block.find_element(By.CSS_SELECTOR, ".progress-value").text.strip()
            value = float(value_text.replace("%", ""))

            progress_bar_elem = block.find_element(By.CSS_SELECTOR, ".progress-bar")
            bg = progress_bar_elem.value_of_css_property("background-color").lower()
            up = "red" if "255, 0, 0" in bg else "green"

            if value >= 80:
                games.append({"name": name, "value": value, "up": up})
        except Exception:
            continue

    games.sort(key=lambda g: g["value"], reverse=True)

    return games

# def search_game_data(provider: str, driver=None) -> list:
#     while not stop_event.is_set():
#         try:
                    
#             # provider-specific search games if not found
#             search_games = []
#             if provider == 'JILI':
#                 search_games.append("Pirate Queen 2")
#             elif provider == 'PG':
#                 search_games.extend([
#                     "Queen of Bounty", "Captain's Bounty", "Mystical Spirits", 
#                     "Spirited Wonders", "Gem Saviour", "Gem Saviour Sword", 
#                     "Gem Saviour Conquest", "Galactic Gems", "Garuda Gems"
#                 ])
#             elif provider == 'FC':
#                 search_games.append("Grand Blue")
#             elif provider == 'PP':
#                 pass

#             games = []
#             game_blocks = driver.find_elements(By.CSS_SELECTOR, ".game-block")

#             # loop through search terms
#             for game in search_games:
#                 search_box = driver.find_element(By.ID, "van-search-1-input")
#                 driver.execute_script("arguments[0].value = '';", search_box)
#                 search_box.send_keys(game)
#                 search_btn = driver.find_element(By.CLASS_NAME, "van-search__action")
#                 search_btn.click()

#                 time.sleep(1)

#                 game_blocks = driver.find_elements(By.CSS_SELECTOR, ".game-block")
#                 for block in game_blocks:
#                     try:
#                         name = block.find_element(By.CSS_SELECTOR, ".game-title").text.strip()
#                         value_text = block.find_element(By.CSS_SELECTOR, ".progress-value").text.strip()
#                         value = float(value_text.replace("%", ""))

#                         progress_bar_elem = block.find_element(By.CSS_SELECTOR, ".progress-bar")
#                         bg = progress_bar_elem.value_of_css_property("background-color").lower()
#                         up = "red" if "255, 0, 0" in bg else "green"

#                         if value >= 80:
#                             games.append({"name": name, "value": value, "up": up})
#                     except Exception:
#                         continue

#             games.sort(key=lambda g: g["value"], reverse=True)
#             return games
#         except Exception as e:
#             print(f"🤖❌  {e}")

#         time.sleep(0.5)

def pct(p):
    if p is None:
        return 0.0
    if isinstance(p, str) and '%' in p:
        return float(p.strip('%'))
    try:
        return float(p)
    except (TypeError, ValueError):
        return 0.0

def play_alert(alert_queue, stop_event):
    while not stop_event.is_set():
        if platform.system() == "Darwin":
            while not stop_event.is_set():
                try:
                    say = alert_queue.get_nowait()
                    sound_file = (say)
                    
                    if sound_file == "ping":
                        subprocess.run(["afplay", PING])
                    else:
                        voice = VOICES["Trinoids"] if "trending" in sound_file else VOICES["Samantha"]
                        sound_file = say.replace("trending", "").strip()
                        subprocess.run(["say", "-v", voice, "--", sound_file])
                        
                except Empty:
                    time.sleep(0.05)
                except Exception as e:
                    print(f"\n\t[Alert Thread Error] {e}")
        else:
            pass


if __name__ == "__main__":
    try:
        driver = setup_driver()
        print(f"{CLEAR}", end="")
        print(render_providers())

        url = next((url for url in URLS if 'helpslot' in url), None)
        provider, provider_name = providers_list()
        html = fetch_html_via_selenium(driver, url, provider)

        stop_event = threading.Event()
        alert_queue = ThQueue()
        alert_thread = threading.Thread(target=play_alert, args=(alert_queue, stop_event), daemon=True)
        alert_thread.start()
        alert_queue.put(provider_name)

        last_alerts = {}
        alert_cooldown = 10 # seconds

        while True:
            games_found = False
            games = extract_game_data(driver)
            
            if games:
                # if games not found.. search it
                search_games = []
                if provider == 'JILI':
                    search_games.append("Pirate Queen 2")
                elif provider == 'PG':
                    search_games.extend(["Bounty", "Spirit"])
                    # search_games.extend([
                    #     "Queen of Bounty", "Captain's Bounty", "Mystical Spirits", 
                    #     "Spirited Wonders" "Gem Saviour", "Gem Saviour Sword", 
                    #     "Gem Saviour Conquest", "Galactic Gems", "Garuda Gems"
                    # ])
                elif provider == 'FC':
                    search_games.append("Grand Blue")
                elif provider == 'PP':
                    pass

                for keyword in search_games:
                    fetch_data = fetch_jackpot(provider, keyword, session_id=1)
                    if fetch_data:
                        if "Bounty" in keyword and 'PG' in provider:
                            fetch_data = [g for g in fetch_data if "Wild Bounty Showdown" not in g["name"]]
                        games.extend([g for g in fetch_data])
                        games.sort(key=lambda g: g["value"], reverse=True)

            data = get_game_data_from_local_api(provider, games) if games else None

            if data:
                # alert_cooldown = len(data) * 2 # seconds)
                percent = f"{LGRY}%{RES}"
                for game in data:
                    # potential_trend = (
                    #     game.get('value') >= 90 and game.get('jackpot_value') >= 88
                    #     # and game.get('meter_color') == 'red'
                    # )

                    trending = (
                        # not game.get('up')
                        # and game.get('meter_color') == 'red'
                        game.get('meter_color') == 'red'
                    )

                    # if trending or potential_trend:
                    games_found = True                        
                    clean_name = re.sub(r"\s*\(.*?\)", "", game.get('name'))
                    if "Wild Ape" in clean_name and "PG" in provider:
                        clean_name = clean_name.replace("#3258", "").strip()

                    tag = "💥💥💥 " if trending else "🔥🔥🔥 "
                    signal = f"{LRED}⬇{RES}" if not game.get('up') else f"{LGRE}⬆{RES}"
                    helpslot_signal = f"{LRED}⬇{RES}" if game.get('meter_color') == "red" else f"{LGRE}⬆{RES}"
                    colored_value_10m = f"{RED if game.get('min10') < 0 else GRE if game.get('min10') > 0 else CYN}{' ' + str(game.get('min10')) if game.get('min10') > 0 else game.get('min10')}{RES}"
                    colored_value_1h = f"{RED if game.get('hr1') < 0 else GRE if game.get('hr1') > 0 else CYN}{' ' + str(game.get('hr1')) if game.get('hr1') > 0 else game.get('hr1')}{RES}"
                    colored_value_3h = f"{RED if game.get('hr3') < 0 else GRE if game.get('hr3') > 0 else CYN}{' ' + str(game.get('hr3')) if game.get('hr3') > 0 else game.get('hr3')}{RES}"
                    colored_value_6h = f"{RED if game.get('hr6') < 0 else GRE if game.get('hr6') > 0 else CYN}{' ' + str(game.get('hr6')) if game.get('hr6') > 0 else game.get('hr6')}{RES}"
                    
                    bet_lvl = (
                        f"{'Bonus' if game.get('value') >= 97 and game.get('jackpot_value') >= 87 and game.get('meter_color') == 'red'
                        else 'High' if (game.get('value') >= 80 and game.get('jackpot_value') >= 80) or game.get('min10') <= -60
                        # else 'High' if (game.get('value') >= 80 and not game.get('up')) or game.get('min10') <= -60
                        else 'Mid' if (game.get('value') >= 50 and not game.get('up')) or game.get('min10') <= -30
                        else 'Low'}"
                    )
                    bet_str = f"{BLNK if bet_lvl not in 'Low' else ''}💰 {BLU if bet_lvl in [ 'Mid', 'Low' ] else BLYEL if bet_lvl == 'Bonus' else BGRE}{bet_lvl.upper()}{RES} "
                    
                    print(
                        f"\n\t{tag} {BMAG}{clean_name} {bet_str}{RES}{DGRY}→ {signal} "
                        f"{RED if not game.get('up') else GRE}{game.get('value')}{RES}{percent} "
                        f"({helpslot_signal} {RED if game.get('meter_color') == 'red' else GRE}{game.get('jackpot_value')}{RES}{percent} {DGRY}Helpslot{RES})"
                    )

                    print(f"\t\t{CYN}⏱{RES} {LYEL}10m{RES}:{colored_value_10m}{percent}  {CYN}⏱{RES} {LYEL}1h{RES}:{colored_value_1h}{percent}  {CYN}⏱{RES} {LYEL}3h{RES}:{colored_value_3h}{percent}  {CYN}⏱{RES} {LYEL}6h{RES}:{colored_value_6h}{percent}")

                    now = time.time()

                    if clean_name not in last_alerts or now - last_alerts[clean_name] > alert_cooldown:
                        last_alerts[clean_name] = now
                        if bet_lvl not in 'Low':
                            alert_queue.put(f"{clean_name} {'trending' if trending else ''}")
                            alert_queue.put(f"{bet_lvl} {game.get('value') if bet_lvl == 'Bonus' else ''}")
                            
            print("\n")
            if not games_found:
                print(f"\t🚫 {BLRED}No Trending Games Found !{RES}")
                alert_queue.put("No Trending Games Found")

            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n\n\t🤖❌  {BLRED}Main program interrupted.{RES}")
        stop_event.set()
    finally:
        driver.quit()
        atexit.register(driver.quit)
        