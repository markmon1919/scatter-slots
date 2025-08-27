#!/usr/bin/env .venv/bin/python

import atexit, json, os, platform, random, re, requests, shutil, subprocess, threading, time
from queue import Queue as ThQueue, Empty
# from meter import fetch_jackpot
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By 
from config import (PROVIDERS, DEFAULT_PROVIDER_PROPS, URLS, USER_AGENTS, VOICES, BLNK, BLCYN, BLRED, BWHTE, DGRY, LGRY, LRED, LGRE, LCYN, MAG, RED, GRE, YEL, WHTE, CLEAR, RES)

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
                print(f"\n\tSelected: {provider_color}{provider_name}{RES}")
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
                # games = [g for g in json_data if g.get("name", 0) >= 90]
                data = json_data.get("data", [])  # adjust key if needed
                # high_values = [g for g in data if g.get("name") in games]
                # ✅ dict for quick lookup
                games_found = {g["name"]: g for g in games}
                # print(f'GAMES FOUND >> {games_found}')

                # # ✅ single-pass enrich
                enriched = [
                    {**g,
                     "jackpot_value": games_found[g["name"]].get("value"),
                     "meter_color": games_found[g["name"]].get("up")}
                    for g in data if g.get("name") in games_found
                ]

                # print(f'ENRICHED JSON >> {enriched}')


                # print(f'JSON DATA >> {data}')
                # print(f'GAMES >> {games_found}')
                # high_values = [
                #     g for g in data
                #     if float(str(g.get("value", 0)).replace("%", "")) >= 90
                # ]

                # ✅ if you also want only the ones present in your `games` list:
                # if games:
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

# def extract_game_data(data: list) -> dict:
#     if data and isinstance(data, list) and len(data) > 0:
#         trending_games = [(game['name'], game['value'], game['up']) for game in data if game['value'] >= 90]
#         return trending_games
    
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

def extract_game_data(html: str, provider: str, driver=None) -> list:
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

def pct(p):
    if p is None:
        return 0.0
    if isinstance(p, str) and '%' in p:
        return float(p.strip('%'))
    try:
        return float(p)
    except (TypeError, ValueError):
        return 0.0

def play_alert(say: str=None):
    if platform.system() == "Darwin":
        while not stop_event.is_set():
            try:
                say = alert_queue.get_nowait()
                sound_file = (say)
                voice = VOICES["Trinoids"] if "trending" in sound_file else VOICES["Samantha"]
                subprocess.run(["say", "-v", voice, "--", sound_file])
                    
            except Empty:
                continue
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
        alert_thread = threading.Thread(target=play_alert, daemon=True)
        alert_thread.start()
        alert_queue.put(provider_name)

        while True:
            games_found = False
            games = extract_game_data(html, provider, driver)
            # print(f'GAMES >> {games}')

            if games:
                data = get_game_data_from_local_api(provider, games)
            # signal = f"{LRED}⬇{RES}" if not up else f"{LGRE}⬆{RES}"
            # helpslot_signal = f"{LRED}⬇{RES}" if fetch_data.get('meter') == "red" else f"{LGRE}⬆{RES}"


            # if data and isinstance(data, dict) and "data" in data:
            if data:
                percent = f"{LGRY}%{RES}"
                for game in data:
                    signal = f"{LRED}⬇{RES}" if not game.get('up') else f"{LGRE}⬆{RES}"
                    helpslot_signal = f"{LRED}⬇{RES}" if game.get('meter_color') == "red" else f"{LGRE}⬆{RES}"
                    trending = True if (not game.get('up') or game.get('value') >= 95) and game.get('meter_color') == 'red' else False
                    tag = f"💥💥💥 " if trending else "🔥 "
                    if trending:
                        games_found = True
                        print(f"\t{tag} {YEL}{game.get('name')}{RES} {DGRY}→ {signal} {RED if not game.get('up') else GRE}{game.get('value')}{RES}{percent} ({helpslot_signal} {RED if game.get('meter_color') == 'red' else GRE}{game.get('jackpot_value')}{RES}{percent} {DGRY}Helpslot{RES})")
                        alert_queue.put(f"{re.sub(r"\s*\(.*?\)", "", game.get('name')), "trending" if trending else ""}")

            if not games_found:
                print(f"\n\t🚫 {BLRED}No Trending Games Found !\n{RES}")
                alert_queue.put("No Trending Games Found")

            # if pct(fetch_data.get('jackpot')) >= 80:
            # games_found = True
            # trending = True if (not up or value >= 95) and fetch_data.get('meter') == 'red' else False
            # tag = f"💥💥💥 " if trending else "🔥 "
            # print(f"\t{tag} {YEL}{name}{RES} {DGRY}→ {signal} {RED if not up else GRE}{value}{RES}{percent} ({helpslot_signal} {RED if fetch_data.get('meter') == 'red' else GRE}{pct(fetch_data.get('jackpot'))}{RES}{percent} {DGRY}Helpslot{RES})")


            # if not games or len(games) == 0:
            #     print(f"\n\t🚫 {BLRED}No Trending Games Found !\n{RES}")
            #     break
            print('\n')
            time.sleep(1)
        
    except KeyboardInterrupt:
        print(f"\n\n\t🤖❌  {BLRED}Main program interrupted.{RES}")
        stop_event.set()
    finally:
        driver.quit()
        atexit.register(driver.quit)
        

        # while True:
        #     data, request_from = get_game_data_from_local_api(provider)
        #     games_found = False
        #     trending = False
        #     percent = f"{LGRY}%{RES}"

        #     if data and isinstance(data, dict) and "data" in data:
        #         parsed_data = extract_game_data(data.get('data'))
        #         print(f'\n\t{LGRY}Checking Trend{BLNK}...{RES} ({provider_color}{provider}{RES})\n')
                
        #         for name, value, up in sorted(parsed_data, key=lambda g: g[1], reverse=True):
        #             if "Wild Ape" in name and "PG" in provider:
        #                 name = f"{name.replace('#3258', '')}"

        #             fetch_data = fetch_jackpot(provider, name, session_id=1)
        #             signal = f"{LRED}⬇{RES}" if not up else f"{LGRE}⬆{RES}"
        #             helpslot_signal = f"{LRED}⬇{RES}" if fetch_data.get('meter') == "red" else f"{LGRE}⬆{RES}"
        #             if pct(fetch_data.get('jackpot')) >= 80:
        #                 games_found = True
        #                 trending = True if (not up or value >= 95) and fetch_data.get('meter') == 'red' else False
        #                 tag = f"💥💥💥 " if trending else "🔥 "
        #                 print(f"\t{tag} {YEL}{name}{RES} {DGRY}→ {signal} {RED if not up else GRE}{value}{RES}{percent} ({helpslot_signal} {RED if fetch_data.get('meter') == 'red' else GRE}{pct(fetch_data.get('jackpot'))}{RES}{percent} {DGRY}Helpslot{RES})")
        #                 alert_queue.put(f"{re.sub(r"\s*\(.*?\)", "", name), "trending" if trending else ""}")
        #             else:
        #                 print(f"\t {LCYN}◉{RES}  {DGRY}Potential Game Trend: {YEL}{name}{RES} {DGRY}→ {signal} {RED if not up else GRE}{value}{RES}{percent} ({helpslot_signal} {RED if fetch_data.get('meter') == 'red' else GRE}{pct(fetch_data.get('jackpot'))}{RES}{percent} {DGRY}Helpslot{RES})")
                
        #         if not games_found:
        #             print(f"\n\t🚫 {BLRED}No Trending Games Found !\n{RES}")
        #             alert_queue.put("No Trending Games Found")

        #     else:
        #         print(f"\n\t❌ {BLRED}Error fetching data: {data}{RES}")

        #     time.sleep(1) # wait before the next check