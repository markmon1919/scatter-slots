import asyncio, logging, time, platform, os, shutil, threading
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException, Request
from contextlib import asynccontextmanager
from decimal import Decimal
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from config import (PROVIDERS, LOGS_PATH, LOG_LEVEL, URLS,
                    LRED, LBLU, LCYN, LYEL, LMAG, LGRE, LGRY, RED, MAG, YEL, 
                    GRE, CYN, BLU, WHTE, BLRED, BLYEL, BLGRE, BLMAG, BLBLU, 
                    BLCYN, BYEL, BMAG, BCYN, BWHTE, DGRY, BLNK, CLEAR, RES)

# ──────────────
# LOGGING SETUP
# ──────────────
logging.basicConfig(level=(logging.DEBUG if LOG_LEVEL == "DEBUG" else logging.INFO))
logger = logging.getLogger("data")

# ──────────────
# DATA MODELS
# ──────────────

class RegisterRequest(BaseModel):
    url: str
    name: str
    provider: str = "PG"

# ──────────────
# GLOBALS
# ──────────────
registrations = {}
latest_data = {}
clients = set()
stop_event = threading.Event()

# ──────────────
# SETUP DRIVER
# ──────────────
async def setup_driver():
    options = Options()
    if platform.system() != "Darwin" or os.getenv("IS_DOCKER") == "1":
        options.binary_location = "/opt/google/chrome/chrome"
        options.add_argument('--disable-dev-shm-usage')

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")

    service = Service(shutil.which("chromedriver"))
    return webdriver.Chrome(service=service, options=options)

# ──────────────
# FETCH HTML
# ──────────────
async def fetch_html(driver: webdriver.Chrome, game: str = None):        
    try:
        img_elem = PROVIDERS.get("PG").img_url.lower()
        item = driver.find_element(By.CSS_SELECTOR, f".provider-icon img[src*='{img_elem}']")
        item.click()
    except Exception:
        pass
    time.sleep(1)
    return driver.page_source

# ──────────────
# BACKGROUND FETCH THREAD
# ──────────────
def fetch_game_data(driver: webdriver.Chrome, game: str):
    """Thread-safe background loop for PG game data fetching."""
    logger.info(f"🎮 Starting background fetch for {game} (PG)")
    while not stop_event.is_set():
        try:
            card = driver.find_element(By.CSS_SELECTOR, ".game-block")
            name = card.find_element(By.CSS_SELECTOR, ".game-title").text.strip()
            if name != game:
                continue

            value_text = card.find_element(By.CSS_SELECTOR, ".progress-value").text.strip()
            value = float(value_text.replace("%", ""))
            progress_bar_elem = card.find_element(By.CSS_SELECTOR, ".progress-bar")
            bg = progress_bar_elem.value_of_css_property("background-color").lower()
            up = "red" if "255, 0, 0" in bg else "green"

            game_data = {
                "name": game,
                "jackpot_value": value,
                "meter_color": up,
                "timestamp": time.time()
            }
            latest_data[game] = game_data

            # 🔥 Push to all connected websocket clients
            asyncio.run(push_updates(game_data))

            logger.debug(f"📊 {game_data}")
        except Exception as e:
            logger.warning(f"🤖❌ Fetch error for {game}: {e}")
        time.sleep(1.0)

# ──────────────
# PUSH UPDATES TO WS CLIENTS
# ──────────────
async def push_updates(data):
    disconnected = []
    for ws in clients:
        try:
            await ws.send_json(data)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        clients.remove(ws)

# ──────────────
# LIFESPAN
# ──────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    driver = await setup_driver()
    driver.get(URLS[0])
    logger.info("🌐  Starting up — initializing driver...")

    app.state.driver = driver
    try:
        yield
    finally:
        logger.info("⚠️ App shutdown — driver left running intentionally.")

# ──────────────
# FASTAPI APP
# ──────────────
app = FastAPI(lifespan=lifespan, title="Data HS - Pocket Game Soft (PG)")

# ──────────────
# ROUTES
# ──────────────
@app.get("/hs-pg")
async def root():
    return {"status": "Service active", "title": app.title}

@app.post("/register-pg")
async def register_game(req: RegisterRequest, request: Request):
    if not req.name or not req.url:
        raise HTTPException(status_code=400, detail="Missing name or url")
    if req.provider != "PG":
        raise HTTPException(status_code=400, detail="Only PG supported.")
        
    registrations[req.name] = {"url": req.url, "provider": req.provider}
    driver = request.app.state.driver

    # ✅ Start fetch thread
    fetch_thread = threading.Thread(target=fetch_game_data, args=(driver, req.name), daemon=True)
    fetch_thread.start()
    logger.info(f"🚀 Fetch thread started for {req.name}")
    return {"status": "registered", "name": req.name}

@app.post("/deregister-pg")
async def deregister_game(req: RegisterRequest, request: Request):
    if req.name not in registrations:
        raise HTTPException(status_code=404, detail="Not registered")

    del registrations[req.name]
    latest_data.pop(req.name, None)

    logger.info(f"🗑️ Deregistered {req.name}")

    # 🔁 Reload page if no more games active
    if not registrations:
        driver = request.app.state.driver
        stop_event.set()
        logger.info("🛑 All threads stopped — reloading main page...")
        await asyncio.sleep(2)
        driver.get(URLS[0])
        stop_event.clear()

    return {"status": "deregistered", "name": req.name}

@app.get("/search-pg")
async def search(request: Request, game: str = Query(None)):
    driver = request.app.state.driver
    driver.get(URLS[0])
    await fetch_html(driver, game)
    return {"data": latest_data.get(game, {"message": "No data yet"})}

# ──────────────
# REAL-TIME WEBSOCKET
# ──────────────
@app.websocket("/ws-pg")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    logger.info(f"🌐 WebSocket connected ({len(clients)} clients total)")
    try:
        while True:
            await websocket.receive_text()  # just keep connection alive
    except WebSocketDisconnect:
        clients.remove(websocket)
        logger.info("❌ WebSocket disconnected")
        