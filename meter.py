#!/usr/bin/env .venv/bin/python

import atexit, os, re, time, platform, shutil
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from config import (PROVIDERS, DEFAULT_PROVIDER_PROPS)


def setup_driver():
    options = Options()
    if platform.system() != "Darwin" or os.getenv("IS_DOCKER") == "1":
        options.binary_location = "/opt/google/chrome/chrome"
        options.add_argument('--disable-dev-shm-usage')

    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--blink-settings=imagesEnabled=false')  # Disable images
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    # options.add_argument(f"--user-data-dir={os.getcwd()}/chrome_profile_{session_id}")
    # options.add_argument(f"--profile-directory=Profile_{game.lower()}")

    service = Service(shutil.which("chromedriver"))
    return webdriver.Chrome(service=service, options=options)

def fetch_html_via_selenium(driver: webdriver.Chrome, game: str, url: str, provider: str):       
    driver.get(url)
    time.sleep(1)

    search_box = driver.find_element(By.ID, "van-search-1-input")
    driver.execute_script("arguments[0].value = '';", search_box)
    search_box.send_keys(game)

    time.sleep(1)

    if "helpslot" in url:
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

def extract_game_data(html: str, game: str, provider: str, driver=None):
    soup = BeautifulSoup(html, "html.parser")
    game_blocks = soup.select("div.game-list .game-block")
    if not game_blocks:
        return None

    target_block = None
    for block in game_blocks:
        name_tag = block.find("div", class_="game-title")
        if not name_tag:
            continue

        name_tag_clean = re.sub(r'\s+', '', name_tag.get_text(strip=True).lower())
        game_clean = game.strip().replace(' ', '').lower()
        if game_clean == name_tag_clean:
            target_block = block
            break

    if not target_block:
        return None

    jackpot_value = None
    progress_value = target_block.find("div", class_="progress-value")
    if progress_value:
        value = progress_value.get_text(strip=True)
        jackpot_value = float(value.replace("%", ""))

    if jackpot_value < 80:
        return None
        
    meter_color = None
    if driver:
        try:
            progress_bar_elem = driver.find_element(By.CSS_SELECTOR,f"div.game-block:nth-of-type({game_blocks.index(target_block)+1}) .progress-bar")
            bg = progress_bar_elem.value_of_css_property("background-color").lower()
            meter_color = "red" if "255, 0, 0" in bg else "green"
        except Exception as e:
            print("Error checking meter color:", e)

    # history = {}
    # history_tags = target_block.select(".game-info-list .game-info-value")

    # if history_tags and len(history_tags) >= 4:
    #     history = {
    #         "10m": history_tags[0].get_text(strip=True),
    #         "1h":  history_tags[1].get_text(strip=True),
    #         "3h":  history_tags[2].get_text(strip=True),
    #         "6h":  history_tags[3].get_text(strip=True)
    #     }
        
    return {
        # "provider": provider,
        "name": game,
        "value": jackpot_value,
        "up": meter_color,
        # "history": history
    }

def extract_game_keyword(driver=None) -> list:
    games = []
    game_blocks = driver.find_elements(By.CSS_SELECTOR, ".game-block")
    for block in game_blocks:
        try:
            name = block.find_element(By.CSS_SELECTOR, ".game-title").text.strip()
            value_text = block.find_element(By.CSS_SELECTOR, ".progress-value").text.strip()
            value = float(value_text.replace("%", ""))

            progress_bar_elem = block.find_element(By.CSS_SELECTOR, ".progress-bar")
            bg = progress_bar_elem.value_of_css_property("background-color").lower()
            up = "red" if "255, 0, 0" in bg else "green"

            if value >= 80:
                games.append({"name": name, "value": value, "up": up})
        except Exception:
            continue

    # games.sort(key=lambda g: g["value"], reverse=True)

    return games

def fetch_jackpot(provider: str, game: str, session_id: int = 1):
    url = f"https://www.helpslot.win"
    driver = setup_driver()

    try:
        if "Wild Ape" in game and "PG" in provider:
            game = f"{game.replace('x10000', '#3258')}" if "x10000" in game else f"{game}#3258"

        html = fetch_html_via_selenium(driver, game, url, provider)
        # data = extract_game_data(html, game, provider, driver=driver)
        data = extract_game_keyword(driver=driver)
        
        return data

    #     return data or {
    #         # "provider": provider,
    #         "name": game,
    #         "value": None,
    #         "up": None,
    #         # "history": None,
    #         # "error": "Game not found"
    #     }
    # except Exception as e:
    #     return {
    #         # "provider": provider,
    #         "name": game,
    #         "value": None,
    #         "up": None,
    #         # "history": None,
    #         "error": str(e)
    #     }
    finally:
        # time.sleep(10) # for debug
        atexit.register(driver.quit)
        