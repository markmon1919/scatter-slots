import asyncio, httpx, json, logging, random, time#, uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
from decimal import Decimal
from config import (URLS, USER_AGENTS, REQUEST_FROMS, LOG_LEVEL)


logging.basicConfig(level=(logging.DEBUG if LOG_LEVEL == "DEBUG" else logging.INFO))
logger = logging.getLogger("data")

# ────────────── IN-MEMORY STORAGE ──────────────
last_min10s = {}        # last min10 per game/requestFrom
last_prev_min10s = {}   # previous min10 per game/requestFrom
latest_data = {}        # latest data per game
ws_connections: dict[str, set[WebSocket]] = {}

# ────────────── HELPER FUNCTIONS ──────────────
async def broadcast(game_name: str, provider: str, data: dict):
    ws_key = (game_name, provider)
    conns = ws_connections.get(ws_key, set()).copy()
    if not conns:
        return
    message = json.dumps(data)
    disconnected = set()
    for ws in conns:
        try:
            await ws.send_text(message)
        except WebSocketDisconnect:
            disconnected.add(ws)
        except Exception as e:
            logger.error(f"⚠️ Failed to send WS message: {e}")
            disconnected.add(ws)
    for ws in disconnected:
        ws_connections[ws_key].remove(ws)

# ────────────── POLLING SINGLE GAME ──────────────
async def poll_single(client, game_name, provider, requestFrom):
    url = f"{URLS[0]}/api/games"
    try:
        user_agent = random.choice(USER_AGENTS)
        headers = {"Accept": "application/json", "User-Agent": user_agent}
        params = {"name": game_name, "manuf": provider, "requestFrom": requestFrom}
        
        resp = await client.get(url, params=params, headers=headers)
        resp.raise_for_status()

        text = (resp.text or "").strip()
        if not text:
            logger.warning(f"⚠️ Empty response body for {game_name} [{requestFrom}]")
            return

        try:
            data_json = resp.json()
        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f"💥 Invalid JSON from API for {game_name} [{requestFrom}]: {e}")
            return

        data_list = data_json.get("data")
        if not data_list:
            logger.warning(f"⚠️ No data returned for {game_name} [{requestFrom}]")
            return

        first = data_list[0]
        min10 = first.get("min10")
        if min10 is None:
            return

        now_time = Decimal(str(time.time()))
        key = (game_name, provider, requestFrom)
        prev_min10_request = last_min10s.get(key)
        prev_prev_min10 = last_prev_min10s.get(key, 0.0)
        
        # compute deltas for this requestFrom
        delta_prev = prev_min10_request - prev_prev_min10 if prev_min10_request is not None else 0.0
        delta_10m = min10 - prev_min10_request if prev_min10_request is not None else 0.0

        # update per-requestFrom tracking
        last_prev_min10s[key] = prev_min10_request or 0.0
        last_min10s[key] = min10

        # check global last min10 to avoid duplicate broadcasts
        last_entry = latest_data.get((game_name, provider))
        last_min10_global = last_entry.get("min10") if last_entry else None
        last_time_global = Decimal(str(last_entry.get("last_updated"))) if last_entry else None

        if last_min10_global == min10:
            return  # skip duplicate global broadcast

        interval = float(now_time - last_time_global) if last_time_global else 0.0
        prev_min10_global = last_min10_global or 0.0

        # prepare broadcast including deltas + prev_min10
        new_data = dict(first)
        new_data["last_updated"] = str(now_time)
        new_data["prev_min10"] = prev_min10_global  # NEW
        new_data["prev_10m_delta"] = delta_prev
        new_data["10m_delta"] = delta_10m
        new_data["interval"] = interval

        # save globally
        latest_data[(game_name, provider)] = new_data

        await broadcast(game_name, provider, new_data)
        logger.info(
            f"⚡ [{game_name} | {requestFrom}] broadcast min10 → {min10} "
            f"(prev_min10={prev_min10_global}, delta_prev={delta_prev:.2f}, "
            f"delta_10m={delta_10m:.2f}, interval={interval:.2f}s)"
        )
    except Exception as e:
        logger.error(f"💥 Poll failed for {game_name} [{requestFrom}]: {e}")

# ────────────── IMMEDIATE POLL ON WS CONNECT ──────────────
async def _poll_first_response(game_name: str, provider: str):
    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=2.0, read=5.0, write=5.0, pool=5.0)) as client:
        for requestFrom in REQUEST_FROMS:
            await poll_single(client, game_name, provider, requestFrom)

# ────────────── POLLER LOOP ──────────────
async def poller_loop():
    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=2.0, read=5.0, write=5.0, pool=5.0)) as client:
        while True:
            if not ws_connections:
                await asyncio.sleep(0.1)
                continue

            # poll all games for all requestFrom
            poll_tasks = []
            for (game_name, provider) in ws_connections.keys():
                for requestFrom in REQUEST_FROMS:
                    poll_tasks.append(poll_single(client, game_name, provider, requestFrom))

            await asyncio.gather(*poll_tasks)
            await asyncio.sleep(0.05)
            # • 0.1 seconds (current) → polls roughly every 100 ms, very responsive, low CPU.
            # • 0.05 seconds → slightly faster updates.
            # • 0.01 seconds → almost “instantaneous” feel, but can spike CPU if many games/clients are connected.

# ────────────── FASTAPI LIFESPAN ──────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.poller_task = asyncio.create_task(poller_loop())
    logger.info("🚀 Poller started (on first WS connection).")
    try:
        yield
    finally:
        if app.state.poller_task:
            app.state.poller_task.cancel()
            try:
                await app.state.poller_task
            except asyncio.CancelledError:
                logger.info("✅ Poller stopped cleanly.")

app = FastAPI(lifespan=lifespan, title="Data API")

# ────────────── ROUTES ──────────────
@app.get("/")
async def root():
    return {"message": "FastAPI poller running. Connect via WebSocket to receive min10 updates.", "title": app.title}

@app.get("/game")
async def get_latest_game(name: str, provider: str):
    entry = latest_data.get((name, provider))
    if not entry:
        return {"detail": "No data yet"}
    return entry

# ────────────── WEBSOCKET ──────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    game_name = "<unknown>"
    provider = "<unknown>"
    await ws.accept()
    try:
        init_msg = await ws.receive_text()

        # guard: ensure client sent valid JSON on connect
        try:
            data = json.loads(init_msg)
        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f"💥 WS initial message not valid JSON: {e} -- received: {init_msg!r}")
            await ws.close(code=1003)
            return

        game_name = data.get("game")
        provider = data.get("provider")

        if not game_name or not provider:
            logger.warning(f"⚠️ WS connect missing required fields: {data!r}")
            await ws.close(code=1003)
            return

        # Use a tuple (game, provider) as the key to separate connections
        ws_key = (game_name, provider)
        if ws_key not in ws_connections:
            ws_connections[ws_key] = set()
        ws_connections[ws_key].add(ws)
        logger.info(f"🔗 WS connected for game: {game_name}, provider: {provider}")

        # ⚡ Immediately poll first response for this game/provider
        asyncio.create_task(_poll_first_response(game_name, provider))

        while True:
            await asyncio.sleep(10)  # keep alive

    except WebSocketDisconnect:
        logger.info(f"❌ WS disconnected for game: {game_name}, provider: {provider}")
        ws_connections.get(ws_key, set()).discard(ws)
    except Exception as e:
        logger.error(f"⚠️ WS error for game {game_name}, provider {provider}: {e}")
        ws_connections.get(ws_key, set()).discard(ws)


# for local testing only
# if __name__ == "__main__":
#     uvicorn.run("data-api:app", host="0.0.0.0", port=3333)
