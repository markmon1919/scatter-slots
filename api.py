#!/usr/bin/env .venv/bin/python
# -*- coding: utf-8 -*-

import asyncio, httpx, time, uvicorn, hashlib, json, copy
# from config import API_CONFIG
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
TIMEOUT_SECONDS = 60  # Auto-deregister timeout

class GameRegistration(BaseModel):
    url: str
    name: str
    provider: str = 'JILI'

# Safe hash function
def hash_games(games: List[Dict[str, Any]]) -> str:
    safe_games = copy.deepcopy(games)
    for g in safe_games:
        for key in ("value", "min10", "hr1", "hr3", "hr6"):
            if key in g and isinstance(g[key], float):
                g[key] = round(g[key], 2)
    stable_games = sorted(safe_games, key=lambda g: g.get("id", 0))
    return hashlib.sha256(json.dumps(stable_games, sort_keys=True).encode()).hexdigest()

# Fetch game data
async def fetch_game(url: str, name: str, provider: str = 'JILI') -> List[Dict[str, Any]]:
    URL = f"{url}/api/games"
    HEADERS = {
        "Accept": "application/json",
        "Referer": url,
        "User-Agent": "Mozilla/5.0"
    }
    PARAMS = {
        "name": name,
        "manuf": provider,
        "requestFrom": "H6"
    }

    timeout = httpx.Timeout(connect=0.5, read=2.0, write=1.0, pool=2.0)

    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(URL, params=PARAMS, headers=HEADERS)
                if response.status_code == 200:
                    data = response.json().get("data", [])
                    print(f"\n✅ Fetched '{name}' [{provider}] - {len(data)} game(s)\n")
                    return data
        except httpx.RequestError as e:
            print(f"\n⚠️ Network error on attempt {attempt+1} for '{name}': {e}\n")
        await asyncio.sleep(1)

    print(f"\n❌ Failed to fetch '{name}' after 2 attempts\n")
    return []

# Combine all games and update cache
async def update_games() -> bool:
    tasks = [fetch_game(game["url"], game["name"], game["provider"]) for game in REGISTERED_GAMES]
    results = await asyncio.gather(*tasks)

    combined = []
    for games in results:
        for game in games:
            if not any(g["id"] == game["id"] for g in combined):
                combined.append(game)

    if not combined:
        print("\n⚠️ No game data returned, skipping update.\n")
        return False

    print("\n🔍 Combined Snapshot:", [(g["id"], g["name"], round(g.get("value", 0), 2)) for g in combined])

    new_hash = hash_games(combined)
    previous_hash = CACHE.get("last_snapshot")
    print(f"\nHash Equal: {'\033[91mTrue\033[0m' if new_hash == previous_hash else 'False'}\n")

    if new_hash == previous_hash:
        print("\n🔁 No changes detected.\n")
        return False

    CACHE["games"] = combined
    CACHE["last_updated"] = time.time()
    CACHE["last_snapshot"] = new_hash
    print(f"\n🔄 CACHE updated with {len(combined)} game(s)")
    return True

# Auto-remove inactive games
def auto_deregister_inactive():
    now = datetime.utcnow()
    inactive_games = []

    for game in REGISTERED_GAMES:
        key = game["name"].replace(" ", "").lower()
        last_seen = LAST_ACCESSED.get(key)
        if not last_seen or (now - last_seen).total_seconds() > TIMEOUT_SECONDS:
            inactive_games.append(game)

    for game in inactive_games:
        REGISTERED_GAMES.remove(game)
        LAST_ACCESSED.pop(game["name"].replace(" ", "").lower(), None)
        print(f"\n🕛 Auto-deregistered: {game['name']} (inactive > {TIMEOUT_SECONDS}s)\n")

# Background polling loop
async def refresh_loop(base_interval: int = 1):
    fail_count = 0
    max_backoff = 25

    while True:
        auto_deregister_inactive()

        if REGISTERED_GAMES:
            changed = await update_games()
            fail_count = 0 if changed else fail_count + 1
        else:
            fail_count += 1

        wait = base_interval + min(fail_count * 5, max_backoff)
        print(f"\n⏳ Sleeping for {wait} seconds...\n")
        await asyncio.sleep(wait)

# FastAPI lifespan manager
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
        LAST_ACCESSED[key.replace(" ", "").lower()] = datetime.utcnow()
        print(f"\n🎰 Registered: {key}\n")
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
            print(f"\n🎰 De-Registered: {key}\n")
            return {"status": "ok", "message": f"Deregistered '{key}'"}
    print(f"\n🎰 {key} not found!")
    return {"status": "not_found", "message": f"'{key}' not found"}

@app.get("/game")
async def get_game(name: str = Query(...)):
    normalized = name.replace(" ", "").lower()
    for game in CACHE["games"]:
        if game["name"].replace(" ", "").lower() == normalized:
            LAST_ACCESSED[normalized] = datetime.utcnow()
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
