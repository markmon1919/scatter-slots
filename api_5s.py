#!/usr/bin/env .venv/bin/python
# -*- coding: utf-8 -*-

import asyncio, httpx, random, time, uvicorn, hashlib, json, copy
from config import (
    datetime_now, USER_AGENTS,
    LRED, LBLU, LCYN, LYEL, LMAG, LGRE, LGRY, RED, MAG, YEL, CYN, BLU,
    WHTE, BLRED, BLYEL, BLGRE, BLMAG, BLBLU, BLCYN, BYEL, BMAG,
    BCYN, BWHTE, DGRY, BLNK, CLEAR, RES
)
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
# from pathlib import Path
from pydantic import BaseModel
from typing import Dict, Any, List

# Shared state
CACHE: Dict[str, Any] = {
    "games": [],
    "last_updated": 0,
    "last_snapshot": None
}
REGISTERED_GAMES: List[Dict[str, str]] = []
LAST_ACCESSED: Dict[str, datetime] = {}
TIMEOUT_SECONDS = 120  # Auto-deregister timeout

class GameRegistration(BaseModel):
    url: str
    name: str
    provider: str = 'JILI'

def hash_games(games: List[Dict[str, Any]]) -> str:
    safe_games = copy.deepcopy(games)
    for g in safe_games:
        for key in ("value", "min10", "hr1", "hr3", "hr6"):
            if key in g and isinstance(g[key], float):
                g[key] = round(g[key], 2)
    stable_games = sorted(safe_games, key=lambda g: g.get("id", 0))
    return hashlib.sha256(json.dumps(stable_games, sort_keys=True).encode()).hexdigest()

async def fetch_game(
    url: str,
    name: str,
    provider: str = 'JILI',
    user_agent: str = None,
    requestFrom: str = None
) -> List[Dict[str, Any]]:
    REQ_FROM = ["H5", "H6"]

    if user_agent is None or requestFrom is None:
        user_agent = random.choice(USER_AGENTS)
        requestFrom = random.choice(REQ_FROM)

    if "Wild Ape" in name and "PG" in provider:
        name = f"{name.replace('x10000', '#3258')}" if "x10000" in name else f"{name}#3258"
    elif "Fortune Gems" in name or "Super Ace" in name:
        name = name.split("(", 1)[0].strip()

    URL = f"{url}/api/games"

    HEADERS = {
        "Accept": "application/json",
        "Referer": url,
        "User-Agent": user_agent
    }

    PARAMS = {
        "name": name,
        "manuf": provider,
        "requestFrom": requestFrom
    }

    secs = datetime_now().second
    print('Secs:', secs)
    print('Secs Round:', round(secs / 5) * 5)

    # Shorter timeouts to fit 5s cycle
    timeout = httpx.Timeout(connect=0.1, read=0.3, write=0.3, pool=1.0)

    for attempt in range(1, 3):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                HEADERS.update({
                    "User-Agent": random.choice(USER_AGENTS),
                    "requestFrom": random.choice(REQ_FROM)
                })
                response = await client.get(URL, params=PARAMS, headers=HEADERS)

                print(f"\n{WHTE}Attempt #{attempt}{RES} → HTTP {BWHTE}{response.status_code}{RES} \n→ {BLU}{response.url}{RES}")

                if response.status_code == 200:
                    try:
                        data = response.json().get("data", [])
                    except ValueError:
                        print(f"\n❌ Response not JSON for '{name}': {response.text}")
                        return []

                    print(f"\n✅ Fetched {BMAG}'{name}' [{provider}]{RES} - {len(data)} game(s)\n")
                    return data
                else:
                    print(f"\n❌ Non-200 response for '{name}': {response.status_code} → {response.text[:200]}")

        except httpx.RequestError as e:
            print(f"\n⚠️ Network error on attempt {attempt} for '{name}': {e}\n")

        await asyncio.sleep(0.5)

    print(f"\n❌ Failed to fetch '{name}' after 2 attempts\n")
    return []

async def update_games() -> bool:
    tasks = [fetch_game(game["url"], game["name"], game["provider"]) for game in REGISTERED_GAMES]
    results = await asyncio.gather(*tasks)
    combined = []

    for games in results:
        for game in games:
            if not any(g["id"] == game["id"] for g in combined):
                combined.append(game)

    if not combined:
        print(f"\n⚠️ {DGRY}No game data returned, skipping update.{RES}\n")
        return False

    print("\n🔍 Combined Snapshot:", [(g["id"], g["name"], round(g.get("value", 0), 2)) for g in combined])

    new_hash = hash_games(combined)
    previous_hash = CACHE.get("last_snapshot")

    if new_hash == previous_hash:
        print(f"\n🔁 {DGRY}No changes detected.{RES}\n")
        return False

    CACHE["games"] = combined
    CACHE["last_updated"] = time.time()
    CACHE["last_snapshot"] = new_hash
    dt = datetime.fromtimestamp(time.time())
    print(dt.second)
    print(f"\n🔄 [{BWHTE}{dt.second}{RES}] CACHE updated with {len(combined)} game(s) -->"
          f"{BLYEL}{[(g['name'], round(g.get('value', 0), 2)) for g in combined]}{RES}")
    return True

async def refresh_loop(cycle_seconds: int = 1):
    fail_count = 0
    max_backoff = 5

    while True:
        cycle_start = time.time()

        if REGISTERED_GAMES:
            changed = await update_games()
            fail_count = 0 if changed else fail_count + 1
        else:
            print(f"\n⚠️ No registered games. Skipping fetch.\n")
            fail_count += 1

        elapsed = time.time() - cycle_start
        backoff = min(fail_count * 1, max_backoff)
        wait = max(0, cycle_seconds - elapsed + backoff)

        print(f"\n⏳ Sleeping {wait:.2f}s until next refresh cycle.\n")
        await asyncio.sleep(wait)

def auto_deregister_inactive():
    # now = datetime.utcnow()
    today = datetime.fromtimestamp(time.time())
    inactive_games = []

    for game in REGISTERED_GAMES:
        key = game["name"].replace(" ", "").lower()
        last_seen = LAST_ACCESSED.get(key)
        if not last_seen or (now - last_seen).total_seconds() > TIMEOUT_SECONDS:
            inactive_games.append(game)

    for game in inactive_games:
        REGISTERED_GAMES.remove(game)
        LAST_ACCESSED.pop(game["name"].replace(" ", "").lower(), None)
        print(f"\n🕛 Auto-deregistered: {LGRY}{game['name']}{RES} (inactive > {TIMEOUT_SECONDS}s)\n")

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(refresh_loop(1))
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)

@app.post("/register")
async def register_game(game: GameRegistration):
    key = game.name.strip()
    entry = {"url": game.url.strip(), "name": key, "provider": game.provider}
    if key and all(g["name"] != key for g in REGISTERED_GAMES):
        REGISTERED_GAMES.append(entry)
        # LAST_ACCESSED[key.replace(" ", "").lower()] = datetime.utcnow()
        LAST_ACCESSED[key.replace(" ", "").lower()] = datetime.fromtimestamp(time.time())
        print(f"\n🎰 Registered: {BLRED}{key}{RES}\n")
        return {"status": "ok", "message": f"Registered '{key}' with provider '{game.provider}'"}
    print(f"\n🎰 {key} already registered.\n")
    return {"status": "exists", "message": f"'{key}' already registered"}

@app.post("/deregister")
async def deregister_game(game: GameRegistration):
    key = game.name.strip()
    for i, g in enumerate(REGISTERED_GAMES):
        if g["name"] == key:
            REGISTERED_GAMES.pop(i)
            LAST_ACCESSED.pop(key.replace(" ", "").lower(), None)
            print(f"\n🎰 De-Registered: {LGRY}{key}{RES}\n")
            return {"status": "ok", "message": f"Deregistered '{key}'"}
    print(f"\n🎰 {key} not found!")
    return {"status": "not_found", "message": f"'{key}' not found"}

@app.get("/game")
async def get_game(name: str = Query(...)):
    if "Wild Ape" in name:
        name = f"{name.replace('x10000', '#3258')}" if "x10000" in name else f"{name}#3258"
    elif "Fortune Gems" in name or "Super Ace" in name:
        name = name.split("(", 1)[0].strip()

    normalized = name.replace(" ", "").lower()

    for game in CACHE["games"]:
        if game["name"].replace(" ", "").lower() == normalized:
            # LAST_ACCESSED[normalized] = datetime.utcnow()
            LAST_ACCESSED[normalized] = datetime.fromtimestamp(time.time())
            game.update({"last_updated": CACHE["last_updated"]})
            return game
    return {"error": f"Game '{name}' not found."}

@app.get("/games")
async def get_all_games():
    return {
        "status": 0,
        "data": CACHE["games"], 
        "last_updated": CACHE["last_updated"],
        "registered_games": REGISTERED_GAMES
    }

# if __name__ == "__main__":
#     uvicorn.run(
#         f"{Path(__file__).stem}:app",
#         host=API_CONFIG.get("host"),
#         port=API_CONFIG.get("port"),
#         reload=API_CONFIG.get("reload")
#     )
