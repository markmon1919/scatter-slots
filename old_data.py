import asyncio, hashlib, httpx, json, math, random, time#, uvicorn
from fastapi import FastAPI, Query
from pydantic import BaseModel
from contextlib import asynccontextmanager
from decimal import Decimal
from datetime import datetime
from config import (USER_AGENTS, PROVIDERS,
                    LRED, LBLU, LCYN, LYEL, LMAG, LGRE, LGRY, RED, MAG, YEL, 
                    GRE, CYN, BLU, WHTE, BLRED, BLYEL, BLGRE, BLMAG, BLBLU, 
                    BLCYN, BYEL, BMAG, BCYN, BWHTE, DGRY, BLNK, CLEAR, RES)

# ──────────────
# FASTAPI APP
# ──────────────

app = FastAPI()

# ──────────────
# CONSTANTS
# ──────────────

REQUEST_FROMS = ["H5", "H6"]
# POLL_INTERVAL = 3

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

async def align_to_next_7s():
    now = time.time()
    next_t = ((int(now) // 6) + 1) * 6
    wait_time = next_t - now
    print(f"\n⏰  Waiting {BLMAG}{wait_time:.3f}{RES}s to align to next 10s mark...\n")
    await asyncio.sleep(wait_time)

# ──────────────
# POLLER LOOP
# ──────────────

async def poller_loop():
    await align_to_next_7s ()
    rf_index = 0

    async with httpx.AsyncClient(timeout=1.0) as client:
        while True:
            now = time.time()
            current_sec = int(now) % 60
            changed = False

            # Only poll when current second ends in 8 or 9 or 0
            # if current_sec % 10 in (8, 9, 0, 1):
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

                    # if "Wild Ape" in name and "PG" in provider:
                    #     name = f"{name.replace('x10000', '#3258')}" if "x10000" in name else f"{name}#3258"
                    # elif "Fortune Gems" in name or "Super Ace" in name:
                    #     name = name.split("(", 1)[0].strip()

                    params = {
                        "name": name,
                        "manuf": provider,
                        "requestFrom": requestFrom
                    }

                    headers = {
                        "Accept": "application/json",
                        "User-Agent": user_agent
                    }

                    print(f"\n🕓  Polling {PROVIDERS.get(provider).color}{name}{RES} with requestFrom={WHTE}{requestFrom}{RES} UA={WHTE}{user_agent[:30]}{RES}\n")

                    try:
                        r = await client.get(poll_url, params=params, headers=headers)
                        r.raise_for_status()
                        json_data = r.json()
                        data = json_data.get("data")

                        now_time = Decimal(str(time.time()))
                        if data and isinstance(data, list) and len(data) > 0:
                            min10 = data[0].get("min10")
                            if min10 is not None:
                                key = (name, requestFrom)
                                last_min10 = last_min10s.get(key)

                                if min10 != last_min10:
                                    last_min10 = min10
                                    if key in last_change_times:
                                        interval = now_time - last_change_times[key]
                                        print(f"\n✅  <{BYEL}{datetime.fromtimestamp(float(now_time)).strftime('%I')}{BWHTE}:{BYEL}{datetime.fromtimestamp(float(now_time)).strftime('%M')}{BWHTE}:{BLYEL}{datetime.fromtimestamp(float(now_time)).strftime('%S')}{datetime.fromtimestamp(float(now_time)).strftime('%f')[:3]}{RES}>[{PROVIDERS.get(provider).color}{name}{RES} | {WHTE if requestFrom == 'H5' else DGRY}{requestFrom}{RES}] Changed → {LYEL}{min10} ({LMAG}Δ {BLCYN}{interval}{RES}s)\n")
                                        changed = True
                                    else:
                                        print(f"\n✅  <{BYEL}{datetime.fromtimestamp(float(now_time)).strftime('%I')}{BWHTE}:{BYEL}{datetime.fromtimestamp(float(now_time)).strftime('%M')}{BWHTE}:{BLYEL}{datetime.fromtimestamp(float(now_time)).strftime('%S')}{datetime.fromtimestamp(float(now_time)).strftime('%f')[:3]}{RES}>[{PROVIDERS.get(provider).color}{name}{RES} | {WHTE if requestFrom == 'H5' else DGRY}{requestFrom}{RES}] First → {YEL}{min10}{RES}\n")

                                    new_data = json.loads(json.dumps(data[0]))
                                    new_data["last_updated"] = str(now_time)
                                    hash_val = hashlib.md5(json.dumps(new_data, sort_keys=True).encode()).hexdigest()

                                    latest_data[key] = new_data
                                    last_min10s[key] = min10
                                    last_change_times[key] = now_time
                                    last_hashes[key] = hash_val

                                else:
                                    print(f"\n❌  <{BYEL}{datetime.fromtimestamp(float(now_time)).strftime('%I')}{BWHTE}:{BYEL}{datetime.fromtimestamp(float(now_time)).strftime('%M')}{BWHTE}:{BLYEL}{datetime.fromtimestamp(float(now_time)).strftime('%S')}{datetime.fromtimestamp(float(now_time)).strftime('%f')[:3]}{RES}>[{PROVIDERS.get(provider).color}{name}{RES} | {WHTE if requestFrom == 'H5' else DGRY}{requestFrom}{RES}] Still → {DGRY}{min10}{RES}\n")
                                    changed = False
                        else:
                            print(f"⚠️  No data returned for [{name}]")
                    except Exception as e:
                        print(f"⚠️  Request error for [{name}]: {e}")
                        
            # if current_sec % 10 not in (8, 9):
            # if not changed:
            if not changed:
                print(f"\nChanged: {LBLU}{changed}{RES}")
                # if current_sec % 10 == 1:
                #     next_t = ((int(now) // 5) + 1) * 5
                #     sleep_time = next_t - now
                    
                #     print(f"\n⏳  Sleeping {LMAG}{sleep_time:.3f}{RES} to re-check polling condition...\n")
                #     await asyncio.sleep(sleep_time)
                # if current_sec % 10 not in (8, 9):
                if current_sec % 10 not in (8, 9):
                    next_sec = math.ceil(now)
                    sleep_time = max(0, next_sec - time.time())
                
                    # if current_sec % 10 == 1:
                    #     sleep_time = 6
                    # await asyncio.sleep(sleep_time)
                    # print(f"\n⏳  {DGRY}Waiting... current_sec={current_sec} not 0, 9, 8{RES}\n")
                    print(f"\n⏳  Sleeping {LMAG}{sleep_time:.3f}{RES}s to align with next boundary...\n")
                    
                    # await asyncio.sleep(1)
                    await asyncio.sleep(sleep_time)
            else:
                print(f"\nChanged: {BLRED}{changed}{RES}")
                # if current_sec % 10 == 8:
                #     poll_interval = 5
                # elif current_sec % 10 == 9:
                #     poll_interval = 8
                # elif current_sec % 10 == 0:
                #     poll_interval = 7
                # elif current_sec % 10 == 1:
                #     poll_interval = 5
                # if current_sec % 10 not in (8, 9, 0):
                # if current_sec % 10 not in (8, 9, 0):
                    # next_sec = ((int(now) // 7) + 1) * current_sec
                next_t = ((int(now) // 6) + 1) * 6
                sleep_time = next_sec - now
                # else: 
                #     next_sec = math.ceil(now)
                #     sleep_time = max(0, next_sec - time.time())
                
                print(f"\n⏳   Sleeping {LMAG}{sleep_time:.3f}{RES}s to align with next boundary... Current_sec % 10: {current_sec % 10}. Next T: {next_t}\n")
                await asyncio.sleep(sleep_time)
                
            # else:
            #     # next_t = ((int(now) // POLL_INTERVAL) + 1) * POLL_INTERVAL
            #     next_sec = math.ceil(now)
            #     sleep_time = max(0, next_sec - time.time())
            #     # await asyncio.sleep(sleep_time)
            #     print(f"\n⏳  {DGRY}Waiting... current_sec={current_sec} not 0, 9, 8{RES}\n")
            #     print(f"\n⏳  Sleeping {LMAG}{sleep_time:.3f}{RES}s to align with next boundary...\n")
                
            #     # await asyncio.sleep(1)
            #     await asyncio.sleep(sleep_time)
                
            #     await asyncio.sleep(sleep_time)


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
    # if "Wild Ape" in name:
    #     name = f"{name.replace('x10000', '#3258')}" if "x10000" in name else f"{name}#3258"
    # elif "Fortune Gems" in name or "Super Ace" in name:
    #     name = name.split("(", 1)[0].strip()

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
