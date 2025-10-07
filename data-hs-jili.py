import aiofiles, asyncio, httpx, logging, os, random, time
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel
from config import (USER_AGENTS, PROVIDERS, LOGS_PATH, LOG_LEVEL,
                    LRED, LBLU, LCYN, LYEL, LMAG, LGRE, LGRY, RED, MAG, YEL, 
                    GRE, CYN, BLU, WHTE, BLRED, BLYEL, BLGRE, BLMAG, BLBLU, 
                    BLCYN, BYEL, BMAG, BCYN, BWHTE, DGRY, BLNK, CLEAR, RES)


logging.basicConfig(
    level=(logging.DEBUG if LOG_LEVEL == "DEBUG" else logging.INFO),
    # format="%(asctime)s [%(levelname)s] %(message)s",
    # datefmt="%H:%M:%S",
)
logger = logging.getLogger("data")

# ──────────────
# CONSTANTS
# ──────────────
REQUEST_FROMS = ["H5", "H6"]
POLL_SLEEP_SECONDS = 6  # sleep when no change detected

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

registrations = {}          # name -> {"url": ..., "provider": ...}
last_min10s = {}            # (name, requestFrom) → min10 value
last_prev_min10s = {}
last_change_times = {}      # (name, requestFrom) → Decimal(timestamp)
# last_hashes = {}            # (name, requestFrom) → str(hash)
latest_data = {}            # (name, requestFrom) → dict
last_logged = {}


# ──────────────
# POLLING SINGLE ENTRY
# ──────────────

async def poll_single(client, name, reg, requestFrom):
    url = reg["url"]
    provider = reg["provider"]
    user_agent = random.choice(USER_AGENTS)
    poll_url = f"{url}/api/games"  # adjust if needed

    params = {
        "name": name,
        "manuf": provider,
        "requestFrom": requestFrom
    }
    headers = {
        "Accept": "application/json",
        "User-Agent": user_agent
    }

    provider_obj = PROVIDERS.get(provider)
    provider_color = getattr(provider_obj, "color", "") if provider_obj else ""
    
    logger.info(f"\n🕓  Polling {PROVIDERS.get(provider).color}{name}{RES} with requestFrom={WHTE}{requestFrom}{RES} UA={WHTE}{user_agent[:30]}{RES}\n")

    try:
        resp = await client.get(poll_url, params=params, headers=headers)
        resp.raise_for_status()
        json_data = resp.json()
        data = json_data.get("data")

        now_time = Decimal(str(time.time()))
        now_dt = datetime.fromtimestamp(float(now_time))

        if data and isinstance(data, list) and len(data) > 0:
            first = data[0]
            min10 = first.get("min10")
            if min10 is not None:
                key = (name, requestFrom)
                prev_min10 = last_min10s.get(key)
                
                if min10 != prev_min10:
                    if key in last_change_times:
                        interval = now_time - last_change_times[key]
                        logger.info(
                            f"\n✅  <{BYEL}{now_dt.strftime('%I')}{BWHTE}:{BYEL}{now_dt.strftime('%M')}"
                            f"{BWHTE}:{BLYEL}{now_dt.strftime('%S')}{now_dt.strftime('%f')[:3]}{RES}>"
                            f"[{provider_color}{name}{RES} | "
                            f"{WHTE if requestFrom == 'H5' else DGRY}{requestFrom}{RES}] "
                            f"Changed → {LYEL}{min10}{RES} ({LMAG}Δ {BLCYN}{interval}{RES}s)\n"
                        )
                    else:
                        logger.info(
                            f"\n✅  <{BYEL}{now_dt.strftime('%I')}{BWHTE}:{BYEL}{now_dt.strftime('%M')}"
                            f"{BWHTE}:{BLYEL}{now_dt.strftime('%S')}{now_dt.strftime('%f')[:3]}{RES}>"
                            f"[{provider_color}{name}{RES} | "
                            f"{WHTE if requestFrom == 'H5' else DGRY}{requestFrom}{RES}] "
                            f"First → {YEL}{min10}{RES}\n"
                        )
                        
                    new_data = dict(first)
                    new_data["last_updated"] = str(now_time)
                    # hash_val = hashlib.md5(json.dumps(new_data, sort_keys=True).encode()).hexdigest()
                    # latest_data[key] = new_data
                    # last_min10s[key] = min10
                    # last_change_times[key] = now_time
                    # last_hashes[key] = hash_val
                    new_data['prev_10m_delta'] = (last_min10s.get(key) or 0.0) - (last_prev_min10s.get(key) or 0.0)
                    new_data['10m_delta'] = min10 - (last_min10s.get(key) or 0.0)
                    last_prev_min10s[key] = last_min10s.get(key) or 0.0
                        
                    latest_data[key] = new_data
                    last_min10s[key] = min10
                    last_change_times[key] = now_time
                    
                    try:
                        await create_time_log(new_data)
                    except Exception as e:
                        logger.info(f"⚠️ {BLRED}Failed to log CSV for {provider_color}{name}{RES}: {e}")
                else:
                    # No change
                    logger.info(
                        f"\n❌  <{BYEL}{now_dt.strftime('%I')}{BWHTE}:{BYEL}{now_dt.strftime('%M')}"
                        f"{BWHTE}:{BLYEL}{now_dt.strftime('%S')}{now_dt.strftime('%f')[:3]}{RES}>"
                        f"[{provider_color}{name}{RES} | "
                        f"{WHTE if requestFrom == 'H5' else DGRY}{requestFrom}{RES}] "
                        f"Still → {DGRY}{min10}{RES}\n"
                    )
            else:
                logger.info(f"⚠️  Received data but missing 'min10' for {name} [{requestFrom}]")
        else:
            logger.info(f"⚠️  No valid data list for {name} [{requestFrom}]")
    except Exception as e:
        logger.info(f"⚠️  Poll error [{name} / {requestFrom}]: {e}")

# ──────────────
# POLLER LOOP
# ──────────────

async def poller_loop():
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(connect=2.0, read=5.0, write=5.0, pool=5.0)
        ) as client:
            rf_index = 0  # alternating index
            logger.info("🚀 Poller loop started.")

            while registrations:  # ✅ loop only while something is registered
                requestFrom = REQUEST_FROMS[rf_index]
                rf_index = (rf_index + 1) % len(REQUEST_FROMS)

                # Poll all registered games concurrently
                poll_tasks = [
                    poll_single(client, name, reg, requestFrom)
                    for name, reg in registrations.items()
                ]
                await asyncio.gather(*poll_tasks)

                now_time = Decimal(str(time.time()))
                other_rf = REQUEST_FROMS[rf_index]
                stale_names = []

                # Refresh stale data
                for (name, rf) in list(latest_data.keys()):
                    if rf == other_rf:
                        last_updated = Decimal(str(latest_data[(name, rf)].get("last_updated", "0")))
                        if now_time - last_updated > 10:
                            stale_names.append(name)

                if stale_names:
                    logger.info(f"⏳ Refreshing stale data from {other_rf}: {stale_names}")
                    refresh_tasks = [
                        poll_single(client, name, registrations[name], other_rf)
                        for name in stale_names if name in registrations
                    ]
                    await asyncio.gather(*refresh_tasks)
                    
                await asyncio.sleep(0.1) # Short sleep to avoid CPU hammering, adjust as needed

            logger.info("⏸️ Registrations empty — poller exiting.")
    except asyncio.CancelledError:
        logger.info("⛔ Poller loop cancelled cleanly.")
        raise
    except Exception as e:
        logger.exception(f"💥 Poller loop crashed: {e}")

# ──────────────
# LIFESPAN
# ──────────────
poller_task: asyncio.Task | None = None
monitor_task: asyncio.Task | None = None

async def monitor_registrations():
    """Monitor registration changes and start/stop poller accordingly."""
    global poller_task

    while True:
        try:
            if registrations and (poller_task is None or poller_task.done()):
                logger.info("🚀 Starting poller loop (registrations found).")
                poller_task = asyncio.create_task(poller_loop())

            elif not registrations and poller_task and not poller_task.done():
                logger.info("⏸️ No registrations — cancelling poller loop...")
                poller_task.cancel()
                try:
                    await poller_task
                except asyncio.CancelledError:
                    logger.info("⛔ Poller loop stopped cleanly.")

            # Check every 2 seconds for registration changes
            await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"⚠️ Monitor error: {e}")
            await asyncio.sleep(2)

# ──────────────
# LIFESPAN
# ──────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.poller_task = None

    logger.info("🌐 App starting up...")

    try:
        yield
    finally:
        logger.info("🛑 Shutting down app...")
        if app.state.poller_task:
            app.state.poller_task.cancel()
            try:
                await app.state.poller_task
            except asyncio.CancelledError:
                logger.info("✅ Poller stopped cleanly.")
                
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     poller_task = asyncio.create_task(poller_loop())
#     try:
#         yield
#     finally:
#         poller_task.cancel()
#         try:
#             await poller_task
#         except asyncio.CancelledError:
#             logger.info("\n⛔  Poller loop cancelled cleanly on shutdown.")

# ──────────────
# FastAPI app
# ──────────────

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
    if not req.name or not req.url or not req.provider:
        raise HTTPException(status_code=400, detail="Missing name, url, or provider")
    
    registrations[req.name] = {
        "url": req.url,
        "provider": req.provider
    }

    provider_obj = PROVIDERS.get(req.provider)
    color = getattr(provider_obj, "color", "") if provider_obj else ""
    provider_name = getattr(provider_obj, "provider", req.provider) if provider_obj else req.provider

    logger.info(f"\n🎰 Registered: {BWHTE}{BLNK}{req.name}{RES} ({color}{provider_name}{RES}) URL={req.url}\n")
    
    # ✅ Start poller if not already running
    if not app.state.poller_task or app.state.poller_task.done():
        app.state.poller_task = asyncio.create_task(poller_loop())
        logger.info("🚀 Poller started (on new registration).")
    
    return {"status": "registered", "name": req.name}

@app.post("/deregister")
async def deregister_game(req: RegisterRequest):
    if req.name not in registrations:
        raise HTTPException(status_code=404, detail=f"{req.name} not registered")
    
    del registrations[req.name]
    
    # Clean up associated data keys in latest_data, last_min10s, last_change_times, last_hashes
    for key in list(latest_data.keys()):
        if key[0] == req.name:
            latest_data.pop(key, None)
            last_min10s.pop(key, None)
            last_prev_min10s.pop(key, None)
            last_change_times.pop(key, None)
            # last_hashes.pop(key, None)

    logger.info(f"\n🗑️  Deregistered: {BWHTE}{req.name}{RES}\n")

    if not registrations and app.state.poller_task:
        app.state.poller_task.cancel()
        try:
            await app.state.poller_task
        except asyncio.CancelledError:
            logger.info("✅ Poller stopped cleanly.")
        app.state.poller_task = None

    return {"status": "deregistered", "name": req.name}

@app.get("/game")
async def get_latest_game(
    name: str = Query(..., description="Game name"),
    requestFrom: str = Query(..., description="Source: H5 or H6")
):
    key = (name, requestFrom)
    if key not in latest_data:
        raise HTTPException(status_code=404, detail=f"Game '{name}' with requestFrom '{requestFrom}' has no data yet.")
    
    return latest_data[key]

@app.get("/fetch_hs")
async def fetch_hs_game(
    name: str = Query(..., description="Game name")
):
    if name not in registrations:
        raise HTTPException(status_code=404, detail=f"Game {name} not found in registry.")    

    
    return latest_data[key]

@app.get("/file/game")
async def get_game_csv():
    if not registrations:
        raise HTTPException(status_code=404, detail="No registered games available")

    if not os.path.exists(LOGS_PATH):
        os.makedirs(LOGS_PATH, exist_ok=True)
        
    game = list(registrations.keys())[0]
    game_logs = os.path.join(LOGS_PATH, f"{game.strip().replace(' ', '_').lower()}_log.csv")
    
    if not os.path.isfile(game_logs):
        raise HTTPException(status_code=404, detail=f"CSV file for '{game}' not found")
    
    return game

@app.get("/file")
async def get_game_csv():
    if not registrations:
        raise HTTPException(status_code=404, detail="No registered games available")

    if not os.path.exists(LOGS_PATH):
        os.makedirs(LOGS_PATH, exist_ok=True)

    game = list(registrations.keys())[0]    
    game_logs = os.path.join(LOGS_PATH, f"{game.strip().replace(' ', '_').lower()}_log.csv")
    
    if not os.path.isfile(game_logs):
        raise HTTPException(status_code=404, detail=f"CSV file for '{game}' not found")
    
    return FileResponse(game_logs, media_type="text/csv")

@app.get("/file/jackpot")
async def get_hs_csv():
    # Make sure there is at least one registered game
    if not registrations:
        raise HTTPException(status_code=404, detail="No registered games available")
    
    if not os.path.exists(LOGS_PATH):
        os.makedirs(LOGS_PATH, exist_ok=True)
    
    # Take the first registered game
    game = list(registrations.keys())[0]
    game_logs = os.path.join(LOGS_PATH, f"{game.strip().replace(' ', '_').lower()}_log-hs.csv")
    
    if not os.path.isfile(game_logs):
        raise HTTPException(status_code=404, detail=f"CSV file for '{game}' not found")
    
    return FileResponse(game_logs, media_type="text/csv")

async def create_time_log(data: dict):
    if not os.path.exists(LOGS_PATH):
        os.makedirs(LOGS_PATH, exist_ok=True)
        
    # 🔑 check if same as last written
    if last_logged.get("min10") == data.get("min10"):
        return  # skip writing identical row
    
    # update last_logged cache
    last_logged["min10"] = data.get("min10")
    
    csv_file = os.path.join(LOGS_PATH, f"{data.get("name").strip().replace(' ', '_').lower()}_log.csv")
    write_header = not os.path.exists(csv_file)
    
    fieldnames = [ "timestamp", "jackpot_meter", "color", "10m", "1h", "3h", "6h", "10m_delta" ]
    row = {
        "timestamp": datetime.fromtimestamp(float(data.get("last_updated", time.time()))).strftime("%Y-%m-%d %I:%M:%S %p"),
        "jackpot_meter": data.get("value"),
        "color": "green" if data.get("up") is True else "red",
        "10m": data.get("min10"),
        "1h": data.get("hr1"),
        "3h": data.get("hr3"),
        "6h": data.get("hr6"),
        "10m_delta": data.get("10m_delta", 0.0)
    }

    async with aiofiles.open(csv_file, mode="a", newline="") as f:
        if write_header:
            await f.write(",".join(fieldnames) + "\n")
        await f.write(",".join(str(row.get(fn, "")) for fn in fieldnames) + "\n")
        