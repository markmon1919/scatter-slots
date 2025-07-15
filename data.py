from fastapi import FastAPI, Query
from pydantic import BaseModel
import random
import httpx
import asyncio
import time
import hashlib
import json
from contextlib import asynccontextmanager
from decimal import Decimal
# import uvicorn
from config import (
    USER_AGENTS, PROVIDERS,
    LRED, LBLU, LCYN, LYEL, LMAG, LGRE, LGRY, RED, MAG, YEL, 
    GRE, CYN, BLU, WHTE, BLRED, BLYEL, BLGRE, BLMAG, BLBLU, 
    BLCYN, BYEL, BMAG, BCYN, BWHTE, DGRY, BLNK, CLEAR, RES
)

# ──────────────
# FASTAPI APP
# ──────────────

app = FastAPI()

# ──────────────
# CONSTANTS
# ──────────────

REQUEST_FROMS = ["H5", "H6"]
POLL_INTERVAL = 10

# ──────────────
# DATA MODELS
# ──────────────

class RegisterRequest(BaseModel):
    url: str
    name: str
    provider: str = "JILI"

# ──────────────
# IN-MEMORY STORAGE
# ──────────────

registrations = {}
last_min10s = {}          # (name, requestFrom) → min10 value
last_change_times = {}    # (name, requestFrom) → Decimal(timestamp)
last_hashes = {}          # (name, requestFrom) → str(hash)
latest_data = {}          # (name, requestFrom) → dict

# ──────────────
# ALIGN FUNCTION
# ──────────────

async def align_to_next_10s():
    now = time.time()
    next_t = ((int(now) // 10) + 1) * 10
    wait_time = next_t - now
    print(f"\n⏰  Waiting {LMAG}{wait_time:.3f}{RES}s to align to next 10s mark...\n")
    await asyncio.sleep(wait_time)

# ──────────────
# POLLER LOOP
# ──────────────

async def poller_loop():
    await align_to_next_10s()
    rf_index = 0

    async with httpx.AsyncClient(timeout=5.0) as client:
        while True:
            if not registrations:
                print(f"\n⚠️  {DGRY}No games registered. Waiting...{RES}\n")
            else:
                for name, reg in registrations.items():
                    url = reg["url"]
                    provider = reg["manuf"]

                    requestFrom = REQUEST_FROMS[rf_index]
                    rf_index = (rf_index + 1) % len(REQUEST_FROMS)

                    user_agent = random.choice(USER_AGENTS)
                    poll_url = f"{url}/api/games"

                    if "Wild Ape" in name and "PG" in provider:
                        name = f"{name.replace('x10000', '#3258')}" if "x10000" in name else f"{name}#3258"
                    elif "Fortune Gems" in name or "Super Ace" in name:
                        name = name.split("(", 1)[0].strip()

                    params = {
                        "name": name,
                        "manuf": provider,
                        "requestFrom": requestFrom
                    }

                    headers = {
                        "Accept": "application/json",
                        "User-Agent": user_agent
                    }

                    print(f"\n🕓 Polling {PROVIDERS.get(provider).color}{name}{RES} with requestFrom={WHTE}{requestFrom}{RES} UA={WHTE}{user_agent[:30]}{RES}\n")

                    try:
                        r = await client.get(poll_url, params=params, headers=headers)
                        r.raise_for_status()
                        json_data = r.json()
                        data = json_data.get("data")

                        if data and isinstance(data, list) and len(data) > 0:
                            min10 = data[0].get("min10")
                            if min10 is not None:
                                key = (name, requestFrom)
                                last_min10 = last_min10s.get(key)
                                now_time = Decimal(str(time.time()))

                                if min10 != last_min10:
                                    if key in last_change_times:
                                        interval = now_time - last_change_times[key]
                                        print(f"\n✅ [{PROVIDERS.get(provider).color}{name}{RES} | {WHTE if requestFrom == 'H5' else DGRY}{requestFrom}{RES}] Changed → {LYEL}{min10} ({LMAG}Δ {BLCYN}{interval}{RES}s)\n")
                                    else:
                                        print(f"\n✅ [{PROVIDERS.get(provider).color}{name}{RES} | {WHTE if requestFrom == 'H5' else DGRY}{requestFrom}{RES}] First → {YEL}{min10}{RES}\n")

                                    # prepare a new data object
                                    new_data = json.loads(json.dumps(data[0]))
                                    new_data["last_updated"] = float(now_time)

                                    # calculate hash
                                    hash_val = hashlib.md5(
                                        json.dumps(new_data, sort_keys=True).encode()
                                    ).hexdigest()

                                    # save
                                    latest_data[key] = new_data
                                    last_min10s[key] = min10
                                    last_change_times[key] = now_time
                                    last_hashes[key] = hash_val

                                else:
                                    print(f"\n❌ [{PROVIDERS.get(provider).color}{name}{RES} | {WHTE if requestFrom == 'H5' else DGRY}{requestFrom}{RES}] Still → {DGRY}{min10}{RES}\n")

                        else:
                            print(f"⚠️ [{name} | {WHTE if requestFrom == 'H5' else DGRY}{requestFrom}{RES}] No data returned.")

                    except Exception as e:
                        print(f"⚠️ [{name} | {WHTE if requestFrom == 'H5' else DGRY}{requestFrom}{RES}] Request error: {e}")

            # align to next poll interval
            now = time.time()
            next_t = ((int(now) // POLL_INTERVAL) + 1) * POLL_INTERVAL
            sleep_time = next_t - now
            print(f"\n⏳  Sleeping {LMAG}{sleep_time:.3f}{RES}s to align with next boundary...\n")
            await asyncio.sleep(sleep_time)

# ──────────────
# LIFESPAN
# ──────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(poller_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)

# ──────────────
# ROUTES
# ──────────────

@app.get("/")
async def root():
    return {
        "message": "FastAPI poller running. Use /register to register games and /game to fetch latest data."
    }

@app.post("/register")
async def register_game(req: RegisterRequest):
    registrations[req.name] = {
        "url": req.url,
        "name": req.name,
        "manuf": req.provider
    }

    print(f"\n🎰 Registered: {BWHTE}{BLNK}{req.name}{RES} ({PROVIDERS.get(req.provider).color}{PROVIDERS.get(req.provider).provider}{RES})\n")
    return {"status": "registered", "message": f"Registered {req.name} with provider {req.provider}"}

@app.get("/game")
async def get_latest_game(
    name: str = Query(..., description="Game name"),
    requestFrom: str = Query(..., description="Source: H5 or H6")
):
    if "Wild Ape" in name:
        name = f"{name.replace('x10000', '#3258')}" if "x10000" in name else f"{name}#3258"
    elif "Fortune Gems" in name or "Super Ace" in name:
        name = name.split("(", 1)[0].strip()

    key = (name, requestFrom)

    if key not in latest_data:
        return {
            "error": f"Game '{name}' with requestFrom '{WHTE if requestFrom == 'H5' else DGRY}{requestFrom}{RES}' has no data yet. Make sure it's registered and polled at least once."
        }

    new_hash = last_hashes.get(key)
    last_known_hash_attr = f"last_known_hash_{name}_{requestFrom}"
    last_known_hash = getattr(get_latest_game, last_known_hash_attr, None)

    if new_hash != last_known_hash:
        setattr(get_latest_game, last_known_hash_attr, new_hash)
        return latest_data[key]
    else:
        return {
            "error": f"Game '{name}' with requestFrom '{WHTE if requestFrom == 'H5' else DGRY}{requestFrom}{RES}' has no data changes yet. Please wait.."
        }

# ──────────────
# RUN UVICORN
# ──────────────

# if __name__ == "__main__":
#     uvicorn.run("data:app", host="0.0.0.0", port=8080, reload=True)
