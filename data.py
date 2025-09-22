#!/usr/bin/env .venv/bin/python

import asyncio, hashlib, httpx, json, math, os, random, socket, subprocess, time, uvicorn
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from decimal import Decimal
from datetime import datetime
from config import (USER_AGENTS, PROVIDERS,
                    LRED, LBLU, LCYN, LYEL, LMAG, LGRE, LGRY, RED, MAG, YEL, 
                    GRE, CYN, BLU, WHTE, BLRED, BLYEL, BLGRE, BLMAG, BLBLU, 
                    BLCYN, BYEL, BMAG, BCYN, BWHTE, DGRY, BLNK, CLEAR, RES)

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
last_change_times = {}      # (name, requestFrom) → Decimal(timestamp)
last_hashes = {}            # (name, requestFrom) → str(hash)
latest_data = {}            # (name, requestFrom) → dict

# ──────────────
# HELPER FUNCTIONS
# ──────────────

def _make_safe_attr(name: str, request_from: str) -> str:
    safe_name = "".join(c if c.isalnum() else "_" for c in name)
    safe_req = "".join(c if c.isalnum() else "_" for c in request_from)
    return f"last_known_hash_{safe_name}_{safe_req}"

async def kill_port_8080():
    try:
        result = subprocess.run(
            ["lsof", "-t", "-i", ":8080"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        pids = result.stdout.strip().splitlines()
        if not pids:
            print(f"\n✅  No process using port 8080.")
            return

        for pid in pids:
            subprocess.run(["kill", "-9", pid])
            print(f"\n🛑  Killed process {pid} using port 8080\n")

    except Exception as e:
        print(f"\n❌  Failed to kill port 8080: {e}")

async def align_to_next_7s():
    now = time.time()
    next_t = ((int(now) // 6) + 1) * 6
    wait_time = next_t - now
    print(f"\n⏰  Waiting {BLMAG}{wait_time:.3f}{RES}s to align to next polling boundary...\n")
    await asyncio.sleep(wait_time)

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
    
    print(f"\n🕓  Polling {PROVIDERS.get(provider).color}{name}{RES} with requestFrom={WHTE}{requestFrom}{RES} UA={WHTE}{user_agent[:30]}{RES}\n")

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
                        print(
                            f"\n✅  <{BYEL}{now_dt.strftime('%I')}{BWHTE}:{BYEL}{now_dt.strftime('%M')}"
                            f"{BWHTE}:{BLYEL}{now_dt.strftime('%S')}{now_dt.strftime('%f')[:3]}{RES}>"
                            f"[{provider_color}{name}{RES} | "
                            f"{WHTE if requestFrom == 'H5' else DGRY}{requestFrom}{RES}] "
                            f"Changed → {LYEL}{min10}{RES} ({LMAG}Δ {BLCYN}{interval}{RES}s)\n"
                        )
                    else:
                        print(
                            f"\n✅  <{BYEL}{now_dt.strftime('%I')}{BWHTE}:{BYEL}{now_dt.strftime('%M')}"
                            f"{BWHTE}:{BLYEL}{now_dt.strftime('%S')}{now_dt.strftime('%f')[:3]}{RES}>"
                            f"[{provider_color}{name}{RES} | "
                            f"{WHTE if requestFrom == 'H5' else DGRY}{requestFrom}{RES}] "
                            f"First → {YEL}{min10}{RES}\n"
                        )

                    new_data = dict(first)
                    new_data["last_updated"] = str(now_time)
                    hash_val = hashlib.md5(json.dumps(new_data, sort_keys=True).encode()).hexdigest()

                    latest_data[key] = new_data
                    last_min10s[key] = min10
                    last_change_times[key] = now_time
                    last_hashes[key] = hash_val
                else:
                    # No change
                    print(
                        f"\n❌  <{BYEL}{now_dt.strftime('%I')}{BWHTE}:{BYEL}{now_dt.strftime('%M')}"
                        f"{BWHTE}:{BLYEL}{now_dt.strftime('%S')}{now_dt.strftime('%f')[:3]}{RES}>"
                        f"[{provider_color}{name}{RES} | "
                        f"{WHTE if requestFrom == 'H5' else DGRY}{requestFrom}{RES}] "
                        f"Still → {DGRY}{min10}{RES}\n"
                    )
            else:
                print(f"⚠️  Received data but missing 'min10' for {name} [{requestFrom}]")
        else:
            print(f"⚠️  No valid data list for {name} [{requestFrom}]")
    except Exception as e:
        print(f"⚠️  Poll error [{name} / {requestFrom}]: {e}")

# ──────────────
# POLLER LOOP
# ──────────────

async def poller_loop():
    await align_to_next_7s()
    
    async with httpx.AsyncClient(timeout=1.0) as client:
        rf_index = 0  # alternating index

        while True:
            requestFrom = REQUEST_FROMS[rf_index]
            rf_index = (rf_index + 1) % len(REQUEST_FROMS)

            # Poll all registered games concurrently for current requestFrom
            poll_tasks = [
                poll_single(client, name, reg, requestFrom)
                for name, reg in registrations.items()
            ]
            await asyncio.gather(*poll_tasks)

            now_time = Decimal(str(time.time()))

            # Check stale data for the other requestFrom and refresh immediately
            other_rf = REQUEST_FROMS[rf_index]  # the next one
            stale_names = []
            for (name, rf) in latest_data.keys():
                if rf == other_rf:
                    last_updated = Decimal(str(latest_data[(name, rf)].get("last_updated", "0")))
                    if now_time - last_updated > 10:  # stale threshold seconds
                        stale_names.append(name)

            if stale_names:
                print(f"⏳. {DGRY}Refreshing stale data from {other_rf} for games{RES}: {stale_names}")
                refresh_tasks = [
                    poll_single(client, name, registrations[name], other_rf)
                    for name in stale_names
                    if name in registrations
                ]
                await asyncio.gather(*refresh_tasks)

            # Short sleep to avoid CPU hammering, adjust as needed
            await asyncio.sleep(0.1)

# ──────────────
# LIFESPAN
# ──────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    poller_task = asyncio.create_task(poller_loop())
    try:
        yield
    finally:
        poller_task.cancel()
        try:
            await poller_task
        except asyncio.CancelledError:
            print("\n⛔  Poller loop cancelled cleanly on shutdown.")
        await kill_port_8080()

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

    print(f"\n🎰 Registered: {BWHTE}{BLNK}{req.name}{RES} ({color}{provider_name}{RES}) URL={req.url}\n")

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
            last_change_times.pop(key, None)
            last_hashes.pop(key, None)

    print(f"\n🗑️  Deregistered: {BWHTE}{req.name}{RES}\n")

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

@app.get("/file/game")
async def get_game_csv():
    # Make sure there is at least one registered game
    if not registrations:
        raise HTTPException(status_code=404, detail="No registered games available")
    
    # Take the first registered game
    game = list(registrations.keys())[0]
    logs_folder = os.path.join(os.getcwd(), "logs")
    TIME_DATA = os.path.join(logs_folder, f"{game.strip().replace(' ', '_').lower()}_log.csv")
    
    if not os.path.isfile(TIME_DATA):
        raise HTTPException(status_code=404, detail=f"CSV file for '{game}' not found")
    
    return FileResponse(TIME_DATA, media_type="text/csv")

def get_lan_ip():
    """Get the LAN IP of the machine"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to a public IP (doesn't actually send data)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

if __name__ == "__main__":
    lan_ip = get_lan_ip()
    print(f"🚀 FastAPI running on localhost:8080 (also accessible via LAN: http://{lan_ip}:8080)")
    
    uvicorn.run("data:app", host="0.0.0.0", port=8080, reload=True)
    