#!/usr/bin/env .venv/bin/python

import json, platform, random, re, requests, subprocess, threading
from queue import Queue as ThQueue, Empty
from meter import fetch_jackpot
from config import (PROVIDERS, DEFAULT_PROVIDER_PROPS, URLS, USER_AGENTS, VOICES, BLNK, BLCYN, BLRED, BWHTE, DGRY, LGRY, MAG, RED, YEL, WHTE, CLEAR, RES)


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

def get_game_data_from_local_api(provider: str):
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
            except ValueError:
                print(f"❌ Server did not return JSON: {response.text}")
                json_data = {"error": "Invalid JSON response"}
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            json_data = {"error": f"HTTP {response.status_code}"}

        # print(f"📡 Response >> [{BWHTE}{REQUEST_FROM}{RES}] {json_data}")
        return json_data, REQUEST_FROM

    except Exception as e:
        print(f"❌ Error calling API: {e}")
        return {"error": str(e)}, REQUEST_FROM

def extract_game_data(data: list) -> dict:
    if data and isinstance(data, list) and len(data) > 0:
        trending_games = [(game['name'], game['value']) for game in data if game['value'] >= 80]
        return trending_games

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
                voice = VOICES["Trinoids"] if "bet max" in sound_file or "bet high" in sound_file else VOICES["Samantha"]
                subprocess.run(["say", "-v", voice, "--", sound_file])
                    
            except Empty:
                continue
            except Exception as e:
                logger.info(f"\n\t[Alert Thread Error] {e}")
    else:
        pass

if __name__ == "__main__":    
    try:
        providers = list(PROVIDERS.items())
        print(f"{CLEAR}", end="")
        print(render_providers())

        stop_event = threading.Event()
        alert_queue = ThQueue()
        alert_thread = threading.Thread(target=play_alert, daemon=True)
        alert_thread.start()

        while True:
            try:
                choice = int(input("\n\t🔔 Choose Provider: "))
                if 1 <= choice <= len(providers):
                    provider = providers[choice - 1][0]
                    provider_name = providers[choice - 1][1].provider
                    provider_color = providers[choice - 1][1].color
                    print(f"\n\tSelected: {provider_color}{provider_name}{RES}")
                    alert_queue.put(provider_name)
                    break
                else:
                    print("\t⚠️  Invalid choice. Try again.")
            except ValueError:
                print("\t⚠️  Please enter a valid number.")

        data, request_from = get_game_data_from_local_api(provider)
        if data and "success" in data:
            games_found = False
            percent = f"{LGRY}%{RES}"
            parsed_data = extract_game_data(data.get('data'))
            print(f'\n\t{LGRY}Checking Trend{BLNK}...{RES} ({provider_color}{provider}{RES})\n')
            
            for name, value in sorted(parsed_data, key=lambda g: g[0]):
                # GET HELPSLOT METER TREND
                fetch_data = fetch_jackpot(provider, name, session_id=1)
                if pct(fetch_data.get('jackpot')) >= 80:
                    games_found = True
                    print(f"\t🔥  {YEL}{name}{RES} {DGRY}→ {RED}{value}{RES}{percent} ({RED}{pct(fetch_data.get('jackpot'))}{RES}{percent} {DGRY}Helpslot{RES})")
                    alert_queue.put(re.sub(r"\s*\(.*?\)", "", name))
                else:
                    print(f"\n\t🚫 {BLRED}No Trending Games Found !\n{RES}") if not games_found else None
                    alert_queue.put("No Trending Games Found") if not games_found else None
                    break
    except KeyboardInterrupt:
        print(f"\n\n\t🤖❌  {BLRED}Main program interrupted.{RES}")
        stop_event.set()
        