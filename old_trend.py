#!/usr/bin/env .venv/bin/python

import atexit, json, os, platform, random, re, requests, shutil, subprocess, threading, time
from queue import Queue as ThQueue, Empty
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
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
                print(f"\n\tSelected: {provider_color}{provider_name} {RES}({provider_color}{provider}{RES})\n\n")
                return provider, provider_name
            else:
                print("\t⚠️  Invalid choice. Try again.")
        except ValueError:
            print("\t⚠️  Please enter a valid number.")
    
def scroll_game_list(driver, pause_time: float = 1.0, max_tries: int = 50):
    """Scroll the .scroll-view.with-provider element until all games are loaded."""
    container = driver.find_element(By.CSS_SELECTOR, ".scroll-view.with-provider")

    last_height = 0
    for _ in range(max_tries):
        driver.execute_script("""
            arguments[0].scrollTo(0, arguments[0].scrollHeight);
        """, container)

        time.sleep(pause_time)
        
        new_height = driver.execute_script("return arguments[0].scrollHeight", container)

        if new_height == last_height:
            break
        last_height = new_height

def fetch_html_via_selenium(driver: webdriver.Chrome, url: str, provider: str):
    driver.get(url)
    time.sleep(2)

    provider_items = driver.find_elements(By.CSS_SELECTOR, ".provider-item")

    for item in provider_items:
        try:
            img_elem = item.find_element(By.CSS_SELECTOR, ".provider-icon img")
            img_url = img_elem.get_attribute("src")

            if PROVIDERS.get(provider).img_url.lower() in img_url.lower():
                driver.execute_script("arguments[0].scrollIntoView(true);", item)
                item.click()
                time.sleep(2)
                scroll_game_list(driver)
                break
        except Exception:
            continue

    return driver.page_source

def extract_game_data(driver) -> list:
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
            
            # if value >= 0:  # TEST
            # if "Wild Bounty Showdown" in name:
            if value >= 88 or (value >= 85 and up == "red"):
                games.append({"name": name, "value": value, "up": up})
        except Exception:
            continue
        
    games = sorted([{
        "name": " ".join(w.capitalize() if w.lower() != "of" else w.lower() for w in g["name"].split()), **{k: v for k, v in g.items() if k != "name"}} for g in games],
        key=lambda g: g["name"], reverse=False)
    
    # print(f"\n\tHelpslot Games: \n\t{PROVIDERS.get(provider).color}{'\n\t'.join(g['name'] for g in games)}{RES}")
    
    return games

from concurrent.futures import ThreadPoolExecutor

def get_game_data_from_local_api(provider: str, games: list):
    user_agent = random.choice(USER_AGENTS)
    REQUEST_FROM = random.choice(["H5", "H6"])
    URL = next((url for url in URLS if 'helpslot' in url), None)
    HEADERS = {"Accept": "application/json", "User-Agent": user_agent}

    try:
        response = requests.get(f"{URL}/api/games?manuf={provider}&requestFrom={REQUEST_FROM}", headers=HEADERS)
        if response.status_code != 200:
            print(f"❌ Error {response.status_code}: {response.text}")
            return []

        try:
            json_data = response.json()
            data = json_data.get("data", [])
        except ValueError:
            print(f"❌ Server did not return JSON: {response.text}")
            return []
        
        if provider == "PG":
            data = [g for g in data if g.get("name") != "Wild Ape#3258"]

        # Precompute for fast lookup
        data_names = {g["name"] for g in data}
        games_found = {g["name"]: g for g in games}
        search_games = [name for name in games_found if name not in data_names]

        # Fetch missing games in parallel
        if search_games:
            with ThreadPoolExecutor(max_workers=len(search_games)) as executor:
                results = list(executor.map(search_game_data_from_local_api, search_games))
            data.extend(filter(None, results))
            
        enriched = []
        for g in data:
            name = g.get("name")
            gf = games_found.get(name)
            if not gf:
                continue
            
            if provider in [ "JILI", "PG" ]:
                # if not g.get("value") > 60 or not (g.get("min10") < 0 or g.get("hr1") < -10):
                if not g.get("value") >= 60 or not (g.get("hr1") < g.get("hr3") < g.get("hr6") and g.get("min10") < 0):
                # if not g.get("value") >= 60 or not (g.get("hr1") < g.get("hr3") < g.get("hr6") and g.get("min10") < 0 and g.get("hr6") <= 20):
                    continue
            
            trending = gf.get("up") == "red" and g.get("min10", 0) < 5 and any(
                g.get(hr, 0) < 0 for hr in ["hr1", "hr3", "hr6"]
            )
            
            value = g.get("value", 0)
            gf_value = gf.get("value", 0)
            up = gf.get("up")

            if value >= 95 and gf_value >= 87: #and up == "red":
                bet_lvl = "Bonus"
            elif (value >= 80 and gf_value >= 80) or g.get("min10", 0) <= -60:
                bet_lvl = "High"
            elif (value >= 50 and not g.get("up")) or g.get("min10", 0) <= -30:
                bet_lvl = "Mid"
            else:
                bet_lvl = "Low"

            enriched.append({
                **g,
                "jackpot_value": gf_value,
                "meter_color": up,
                "trending": trending,
                "bet_lvl": bet_lvl
            })
            
        enriched = [g for g in enriched if not (g["bet_lvl"] in ["Mid", "Low"] and not g.get("trending"))]
        priority = {"Bonus": 4, "High": 3, "Mid": 2, "Low": 1}

        enriched.sort(
            key=lambda g: (
                priority[g["bet_lvl"]],
                0 if (g["bet_lvl"] in ["Bonus", "High"] and not g.get("trending")) 
                    or (g["bet_lvl"] in ["Mid", "Low"] and g.get("trending")) else 1,
                g["value"],
                g["jackpot_value"]
            ),
            reverse=True
        )
        
        return enriched
    except Exception as e:
        print(f"❌ Exception: {e}")
        return []
    
def search_game_data_from_local_api(game: str):
    print(f'{WHTE}GAME STRING: {RES}{game}')
    user_agent = random.choice(USER_AGENTS)
    REQUEST_FROM = random.choice(["H5", "H6"])
    URL = next((url for url in URLS if 'helpslot' in url), None)
    HEADERS = {
        "Accept": "application/json",
        "User-Agent": user_agent
    }
    PARAMS = {
        "name": game,
        "requestFrom": REQUEST_FROM
    }
    
    try:
        response = requests.get(f"{URL}/api/games", headers=HEADERS, params=PARAMS)

        if response.status_code == 200:
            try:
                json_data = response.json()
                data = json_data.get("data", [])
                game_data = data[0] if data else {}
                return game_data
            except ValueError:
                print(f"❌ Server did not return JSON: {response.text}")
                json_data = {"error": "Invalid JSON response"}
    except Exception as e:
        print(f"❌ Error calling API: {e}")
        return {"error": str(e)}, REQUEST_FROM

def play_alert(alert_queue, stop_event):
    if platform.system() == "Darwin":
        while not stop_event.is_set():
            try:
                say = alert_queue.get_nowait()
                sound_file = (say)
                
                if sound_file == "ping":
                    subprocess.run(["afplay", PING])
                else:
                    # voice = VOICES["Trinoids"] if ("Bonus" in sound_file or "Trending" in sound_file) else VOICES["Samantha"]
                    voice = VOICES["Trinoids"] if "Bonus" in sound_file else VOICES["Samantha"]
                    sound_file = sound_file.replace("is_trending", "").strip()
                    subprocess.run(["say", "-v", voice, "--", sound_file])
                    
            except Empty:
                time.sleep(0.05)
            except Exception as e:
                print(f"\n\t[Alert Thread Error] {e}")
    else:
        pass


if __name__ == "__main__":
    try:
        stop_event = threading.Event()
        alert_queue = ThQueue()
        alert_thread = threading.Thread(target=play_alert, args=(alert_queue, stop_event), daemon=True)
        alert_thread.start()
        
        driver = setup_driver()
        print(f"{CLEAR}", end="")
        print(render_providers())

        url = next((url for url in URLS if 'helpslot' in url), None)
        provider, provider_name = providers_list()
        alert_queue.put(provider_name)
        html = fetch_html_via_selenium(driver, url, provider)

        last_alerts = {}

        while True:
            games_found = False
            games = extract_game_data(driver)
            data = get_game_data_from_local_api(provider, games) if games else None
            percent = f"{LGRY}%{RES}"
            
            if data:
                alert_cooldown = min(sum(1 for g in data if g.get("bet_lvl") == "Bonus" or (g.get("bet_lvl") in [ "High", "Mid" ] and g.get("trending"))) * 2, 10)
                now = time.time()
                today = time.localtime(now)
                
                print(
                    f"\n\t\t\t\t⏰  {BYEL}{time.strftime('%I', today)}{BWHTE}:{BYEL}{time.strftime('%M', today)}"
                    f"{BWHTE}:{BLYEL}{time.strftime('%S', today)} {LBLU}{time.strftime('%p', today)} "
                    f"{MAG}{time.strftime('%a', today)}{RES}"
                )
                
                for game in data:
                    games_found = True   
                    clean_name = re.sub(r"\s*\(.*?\)", "", game.get('name'))
                    if "Wild Ape" in clean_name and "PG" in provider:
                        clean_name = clean_name.replace("#3258", "").strip()
                        
                    tag = "💥💥💥 " if game.get('trending') else "🔥🔥🔥 "
                    signal = f"{LRED}⬇{RES}" if not game.get('up') else f"{LGRE}⬆{RES}"
                    helpslot_signal = f"{LRED}⬇{RES}" if game.get('meter_color') == "red" else f"{LGRE}⬆{RES}"
                    colored_value_10m = f"{RED if game.get('min10') < 0 else GRE if game.get('min10') > 0 else CYN}{' ' + str(game.get('min10')) if game.get('min10') > 0 else game.get('min10')}{RES}"
                    colored_value_1h = f"{RED if game.get('hr1') < 0 else GRE if game.get('hr1') > 0 else CYN}{' ' + str(game.get('hr1')) if game.get('hr1') > 0 else game.get('hr1')}{RES}"
                    colored_value_3h = f"{RED if game.get('hr3') < 0 else GRE if game.get('hr3') > 0 else CYN}{' ' + str(game.get('hr3')) if game.get('hr3') > 0 else game.get('hr3')}{RES}"
                    colored_value_6h = f"{RED if game.get('hr6') < 0 else GRE if game.get('hr6') > 0 else CYN}{' ' + str(game.get('hr6')) if game.get('hr6') > 0 else game.get('hr6')}{RES}"
                    bet_str = f"{BLNK if game.get('bet_lvl') not in 'Low' else ''}💰 {BLU if game.get('bet_lvl') in [ 'Mid', 'Low' ] else BLYEL if game.get('bet_lvl') == 'Bonus' else BGRE}{game.get('bet_lvl').upper()}{RES} "
                    
                    print(
                        f"\n\t{tag} {BMAG}{clean_name} {bet_str}{RES}{DGRY}→ {signal} "
                        f"{RED if not game.get('up') else GRE}{game.get('value')}{RES}{percent} "
                        f"({helpslot_signal} {RED if game.get('meter_color') == 'red' else GRE}{game.get('jackpot_value')}{RES}{percent} {DGRY}Helpslot{RES})"
                    )
                    print(f"\t\t{CYN}⏱{RES} {LYEL}10m{RES}:{colored_value_10m}{percent}  {CYN}⏱{RES} {LYEL}1h{RES}:{colored_value_1h}{percent}  {CYN}⏱{RES} {LYEL}3h{RES}:{colored_value_3h}{percent}  {CYN}⏱{RES} {LYEL}6h{RES}:{colored_value_6h}{percent}")
                    
                    alert_queue.put(
                        f"{clean_name} {game.get('bet_lvl')} {game.get('value')}" if game.get("bet_lvl") == "Bonus"
                        else f"{clean_name} is_trending" if game.get("trending")
                        else clean_name
                    )
                    
                    # if clean_name not in last_alerts or now - last_alerts[clean_name] > alert_cooldown:
                    #     last_alerts[clean_name] = now
                    #     if game.get('bet_lvl') == 'Bonus' or (game.get('bet_lvl') in [ 'High', 'Mid' ] and game.get('trending')):
                    #         alert_queue.put(
                    #             f"{clean_name} {game.get('bet_lvl')} {game.get('value')}" if game.get("bet_lvl") == "Bonus"
                    #             else f"{clean_name} Trending" if game.get("trending")
                    #             else clean_name
                    #         )
                                          
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
        