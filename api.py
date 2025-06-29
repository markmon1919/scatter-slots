#!/usr/bin/env .venv/bin/python
# -*- coding: utf-8 -*-

import asyncio, httpx, time, uvicorn
from config import API_CONFIG
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from pathlib import Path
from pydantic import BaseModel
from typing import Dict, Any, List

# Shared cache and dynamic game registry
CACHE: Dict[str, Any] = {
    "games": [],
    "last_updated": 0
}

# Store registered games as dicts: {name, provider}
REGISTERED_GAMES: List[Dict[str, str]] = []

class GameRegistration(BaseModel):
    url: str
    name: str
    provider: str = 'JILI'

# Optimized fetcher using async parallel calls
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
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(URL, params=PARAMS, headers=HEADERS)
            if response.status_code == 200:
                data = response.json().get("data", [])
                print(f"✅ Fetched '{name}' [{provider}] - {len(data)} game(s)")
                return data
    except Exception as e:
        print(f"❌ Error fetching '{name}' [{provider}]: {e}")
    return []

# Main updater
async def update_games():
    tasks = [fetch_game(game["url"], game["name"], game["provider"]) for game in REGISTERED_GAMES]
    results = await asyncio.gather(*tasks)

    combined = []
    for games in results:
        for game in games:
            if not any(g["id"] == game["id"] for g in combined):
                combined.append(game)

    if combined:
        CACHE["games"] = combined
        CACHE["last_updated"] = time.time()
        print(f"🔄 Updated CACHE with {len(combined)} game(s)")

# Background loop
async def refresh_loop(interval: int = 1):
    while True:
        if REGISTERED_GAMES:
            await update_games()
        await asyncio.sleep(interval)

# FastAPI app with async lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(refresh_loop())
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
        return {"status": "ok", "message": f"Registered '{key}' with provider '{game.provider}'"}
    return {"status": "exists", "message": f"'{key}' already registered"}

@app.get("/game")
async def get_game(name: str = Query(...)):
    for game in CACHE["games"]:
        if game["name"].replace(" ", "").lower() == name.replace(" ", "").lower():
            return game
    return {"error": f"Game '{name}' not found."}

@app.get("/games")
async def get_all_games():
    return {
        "status": 0,
        "data": CACHE["games"],
        "last_updated": CACHE["last_updated"],
        "registered_games": REGISTERED_GAMES  # Now includes provider info
    }

if __name__ == "__main__":
    uvicorn.run(f"{Path(__file__).stem}:app", host=API_CONFIG.get('host'), port=API_CONFIG.get('port'), reload=API_CONFIG.get('reload'))
