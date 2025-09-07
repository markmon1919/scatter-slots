#!/usr/bin/env .venv/bin/python

import time, platform, os, shutil
from fastapi import FastAPI, Query
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from config import (PROVIDERS)

app = FastAPI()

# -------------------------
# Setup driver (shared)
# -------------------------
def setup_driver():
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

driver = setup_driver()

# -------------------------
# Fetch HTML via Selenium
# -------------------------
def fetch_html(driver: webdriver.Chrome, url: str, game: str = None, provider: str = "JILI"):
    driver.get(url)
    time.sleep(1)
    
    if game:
        try:
            search_box = driver.find_element(By.ID, "van-search-1-input")
            driver.execute_script("arguments[0].value = '';", search_box)
            search_box.send_keys(game)
            time.sleep(1)
        except Exception:
            pass
        
    provider_items = driver.find_elements(By.CSS_SELECTOR, ".provider-item")
    for item in provider_items:
        try:
            img_elem = item.find_element(By.CSS_SELECTOR, ".provider-icon img")
            img_url = img_elem.get_attribute("src")
            
            if PROVIDERS.get(provider).img_url in img_url.lower():
                item.click()
                break
        except Exception:
            continue
    
    time.sleep(1)
    return driver.page_source

# -------------------------
# Extract Game Data
# -------------------------
def extract_game_data(driver: webdriver.Chrome) -> list:
    games = []
    try:
        game_cards = driver.find_elements(By.CSS_SELECTOR, ".game-block")
        for card in game_cards:
            try:
                name = card.find_element(By.CSS_SELECTOR, ".game-title").text.strip()
                value_text = card.find_element(By.CSS_SELECTOR, ".progress-value").text.strip()
                value = float(value_text.replace("%", ""))

                progress_bar_elem = card.find_element(By.CSS_SELECTOR, ".progress-bar")
                bg = progress_bar_elem.value_of_css_property("background-color").lower()
                up = "red" if "255, 0, 0" in bg else "green"

                history = {}
                history_tags = card.find_elements(By.CSS_SELECTOR, ".game-info-list .game-info-item")
                
                for item in history_tags:
                    label = item.find_element(By.CSS_SELECTOR, ".game-info-label").text.strip().rstrip(":").replace(" ", "").lower()
                    val_elem = item.find_element(By.CSS_SELECTOR, ".game-info-value")
                    val_text = val_elem.text.strip()
                    val = float(val_text.replace("%", ""))
                    history[label] = val
                games.append({"name": name, "jackpot_value": value, "meter_color": up, **history})
            except Exception:
                continue
    except Exception:
        pass
    return games

# -------------------------
# API Endpoints
# -------------------------
@app.get("/")
def home():
    return {"status": "ok", "message": "Helpslot fetcher running"}

@app.get("/search")
def get_page(
    url: str = Query(..., description="Target URL"),
    game: str = Query(None, description="Game name (optional)"),
    provider: str = Query("JILI", description="Provider name (optional)")
):
    """Fetch a page via Selenium and return parsed game data"""
    fetch_html(driver, url, game, provider)
    data = extract_game_data(driver)
    
    return {"data": data}

# -------------------------
# Run via Uvicorn
# -------------------------
# uvicorn myserver:app --host 0.0.0.0 --port 8000
