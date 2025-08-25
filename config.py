#!/usr/bin/env .venv/bin/python

import pyautogui
from collections import namedtuple
# from datetime import datetime, timezone
# from zoneinfo import ZoneInfo

# def now_time(countdown: bool=False):
#     today = datetime.now(timezone.utc).astimezone(ZoneInfo("Asia/Manila"))
#     timer_start = (60 - today.second)
#     return today if not countdown else timer_start

LOG_LEVEL = ""#DEBUG"
BREAKOUT_FILE = "breakout_data.json"
DATA_FILE = "previous_data.json"

# === Screen Dimensions ===
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
HALF_WIDTH = SCREEN_WIDTH // 2

# == Single Slot Size
SCREEN_POS = {
    "center_x": SCREEN_WIDTH // 2,
    "center_y": SCREEN_HEIGHT // 2,
    "right_x": SCREEN_WIDTH - 1,
    "bottom_y": SCREEN_HEIGHT - 1
}

# == Dual Slot Sizes
LEFT_SLOT_POS = {
    "center_x": HALF_WIDTH // 2,
    "center_y": SCREEN_HEIGHT // 2
}

RIGHT_SLOT_POS = {
    "center_x": HALF_WIDTH + (HALF_WIDTH // 2),
    "center_y": SCREEN_HEIGHT // 2
}

# === Voice and Sound Settings ===
PING = "/System/Library/Sounds/Ping.aiff"
VOICES = {
    "Samantha": "Samantha",
    "Trinoids": "Trinoids",
    "Kanya": "Kanya",
    "Karen": "Karen",
    "Kathy": "Kathy",
    "Nora": "Nora",
}

# === Default Timeouts ===
# HOLD_DELAY_RANGE = (2.6, 3.5)  # Used with random.uniform(*HOLD_DELAY_RANGE)
# SPIN_DELAY_RANGE = (2.8, 3.7)  # Used with random.uniform(*SPIN_DELAY_RANGE)
HOLD_DELAY_RANGE = (2.6, 3.4)  # Used with random.uniform(*HOLD_DELAY_RANGE)
SPIN_DELAY_RANGE = (2.8, 3.5)  # Used with random.uniform(*SPIN_DELAY_RANGE)
TIMEOUT_DELAY_RANGE = (1, 5)  # Used with random.uniform(*TIMEOUT_DELAY_RANGE)

# COLORS
RED='\033[31m'; GRE='\033[32m'; YEL='\033[33m'
BLU='\033[34m'; MAG='\033[35m'; CYN='\033[36m'
LGRY='\033[37m'; DGRY='\033[90m'; LRED='\033[91m'
LGRE='\033[92m'; LYEL='\033[93m'; LBLU='\033[94m'
LMAG='\033[95m'; LCYN='\033[96m'; WHTE='\033[97m'
BLNK='\033[5m'; NBLNK='\033[25m'; RES='\033[0m'
BLRED = '\033[1;91m'; BLGRE = '\033[1;92m'; BLYEL = '\033[1;93m'
BLMAG = '\033[1;95m'; BWHTE = '\033[1;97m'
BLBLU = '\033[1;94m'; BLCYN = '\033[1;96m'; BMAG = '\033[1;35m'
BYEL = '\033[1;33m'; BCYN = '\033[1;36m'; CLEAR = '\033[H\033[J'

GameConfig = namedtuple("GameConfig", [
    "spin", "auto_spin", "turbo", "feature",
    "auto_play_menu", "widescreen", "provider"
])

GAME_CONFIGS = {
    # Jili
    "3 Lucky Piggy": GameConfig(False, True, True, None, False, True, "JILI"),
    "Ali Baba": GameConfig(False, True, True, None, False, True, "JILI"),
    "Aztec Priestess": GameConfig(False, True, True, None, False, True, "JILI"),
    "Bonus Hunter": GameConfig(False, True, True, None, False, False, "JILI"),
    "Boxing Extravaganza": GameConfig(False, True, True, None, False, True, "JILI"),
    "Boxing King": GameConfig(False, True, True, None, False, True, "JILI"),
    "Candy Baby": GameConfig(False, True, True, None, False, False, "JILI"),
    "Charge Buffalo": GameConfig(False, True, True, None, False, True, "JILI"),
    "Chin Shi Huang": GameConfig(False, True, True, None, False, True, "JILI"),
    "Crazy777": GameConfig(False, True, True, None, False, True, "JILI"),
    "Diamond Party": GameConfig(False, True, True, None, False, True, "JILI"),
    "Egypt's Glow": GameConfig(False, True, True, None, False, True, "JILI"),
    "Fortune Gems": GameConfig(False, True, True, None, False, True, "JILI"),
    "Fortune Gems 2": GameConfig(False, True, True, None, False, True, "JILI"),
    "Fortune Gems 3": GameConfig(False, True, True, None, False, True, "JILI"),
    "Fortune Gems Scratch": GameConfig(False, True, True, None, False, True, "JILI"),
    "Fortune Monkey": GameConfig(False, True, True, None, False, True, "JILI"),
    "Gem Party": GameConfig(False, True, True, None, False, True, "JILI"),
    "Golden Bank": GameConfig(False, True, True, None, False, True, "JILI"),
    "Golden Bank 2": GameConfig(False, True, True, None, False, True, "JILI"),
    "Golden Empire": GameConfig(False, True, True, None, False, True, "JILI"),
    "Golden Joker": GameConfig(False, True, True, None, False, True, "JILI"),
    "Golden Queen": GameConfig(False, True, True, None, False, True, "JILI"),
    "Jackpot Joker": GameConfig(False, True, True, None, False, True, "JILI"),
    "Jungle King": GameConfig(False, True, True, None, False, True, "JILI"),
    "King Arthur": GameConfig(False, True, True, None, False, True, "JILI"),
    "Legacy of Egypt": GameConfig(False, True, True, None, False, True, "JILI"),
    "Lucky Coming": GameConfig(False, True, True, None, False, True, "JILI"),
    "Lucky Goldbricks": GameConfig(False, True, True, None, False, True, "JILI"),
    "Lucky Jaguar": GameConfig(False, True, True, None, False, True, "JILI"),
    "Magic Lamp": GameConfig(False, True, True, None, False, True, "JILI"),
    "Mayan Empire": GameConfig(False, True, True, None, False, True, "JILI"),
    "Money Coming": GameConfig(False, True, True, None, False, True, "JILI"),
    "Money Coming Expand Bets": GameConfig(False, True, True, None, False, True, "JILI"),
    "Money Pot": GameConfig(False, True, True, None, False, True, "JILI"),
    "Neko Fortune": GameConfig(False, True, True, None, False, True, "JILI"),
    "Party Star": GameConfig(False, True, True, None, False, False, "JILI"),
    "Pharaoh Treasure": GameConfig(False, True, True, None, False, True, "JILI"),
    "Pirate Queen": GameConfig(False, True, True, None, False, True, "JILI"),
    "Pirate Queen 2": GameConfig(False, True, True, None, False, True, "JILI"),
    "Samba": GameConfig(False, True, True, None, False, True, "JILI"),
    "Shōgun": GameConfig(False, True, True, None, False, True, "JILI"),
    "Super Ace": GameConfig(False, True, True, None, False, False, "JILI"),
    "Super Ace Deluxe": GameConfig(False, True, True, None, False, False, "JILI"),
    "Super Ace II": GameConfig(False, True, True, None, False, False, "JILI"),
    "Super Ace Joker": GameConfig(False, True, True, None, False, False, "JILI"),
    "Wild Ace": GameConfig(False, True, True, None, False, False, "JILI"),
    # PG Slots
    "Asgardian Rising": GameConfig(False, True, True, None, False, False, "PG"),
    "Captain's Bounty": GameConfig(False, True, True, None, False, False, "PG"),
    "Cocktail Nights": GameConfig(False, True, True, None, False, False, "PG"),
    "Cruise Royale": GameConfig(False, True, True, None, False, False, "PG"),
    "Dragon Hatch": GameConfig(False, True, True, None, False, False, "PG"),
    "Dragon Hatch 2": GameConfig(False, True, True, None, False, False, "PG"),
    "Egypt's Book of Mystery": GameConfig(False, True, True, None, False, False, "PG"),
    "Fortune Mouse": GameConfig(False, True, True, None, False, False, "PG"),
    "Fortune Rabbit": GameConfig(False, True, True, None, False, False, "PG"),
    "Gemstones Gold": GameConfig(False, True, True, None, False, False, "PG"),
    "Heist of Stakes": GameConfig(False, True, True, None, False, False, "PG"),
    "Jurassic Kingdom": GameConfig(False, True, True, None, False, False, "PG"),
    "Legendary Monkey King": GameConfig(False, True, True, None, False, False, "PG"),
    "Lucky Neko": GameConfig(False, True, True, None, False, False, "PG"),
    "Majestic Treasures": GameConfig(False, True, True, None, False, False, "PG"),
    "Oishi Delights": GameConfig(False, True, True, None, False, False, "PG"),
    "Queen of Bounty": GameConfig(False, True, True, None, False, False, "PG"),
    "Rise of Apollo": GameConfig(False, True, True, None, False, False, "PG"),
    "The Queen's Banquet": GameConfig(False, True, True, None, False, False, "PG"),
    "Ways of the Qilin": GameConfig(False, True, True, None, False, False, "PG"),
    "Wild Ape": GameConfig(False, True, True, None, False, False, "PG"),
    "Wild Ape x10000": GameConfig(False, True, True, None, False, False, "PG"),
    "Wild Bandito": GameConfig(False, True, True, None, False, False, "PG"),
    "Wild Coaster": GameConfig(False, True, True, None, False, False, "PG"),
    "Wild Fireworks": GameConfig(False, True, True, None, False, False, "PG"),
    "Wild Bounty Showdown": GameConfig(False, True, True, None, False, False, "PG"),
    "Yakuza Honor": GameConfig(False, True, True, None, False, False, "PG"),
    # Fa Chai
    "Egypt Bonanza": GameConfig(True, True, True, None, False, False, "FC"),
    "Fortune Goddess": GameConfig(True, True, True, None, False, False, "FC"),
    "Gods Grant Fortune": GameConfig(True, True, True, None, False, False, "FC"),
    "Golden Genie": GameConfig(True, True, True, None, False, False, "FC"),
    "Grand Blue": GameConfig(True, True, True, None, False, False, "FC"),
    "Lucky Fortunes": GameConfig(True, True, True, None, False, False, "FC"),
    "Luxury The Golden Panther": GameConfig(True, True, True, None, False, False, "FC"),
    "Mines": GameConfig(True, True, True, None, False, False, "FC"),
    "Queen of Inca": GameConfig(True, True, True, None, False, False, "FC"),
    # JDB
    "Fruity Bonanza Combo": GameConfig(False, True, True, True, True, True, "JDB"),
    "Lucky Diamond": GameConfig(False, True, True, True, True, True, "JDB"),
    "Magic Ace Wild Lock": GameConfig(False, True, True, True, True, True, "JDB"),
    "Wonder Elephant": GameConfig(False, True, True, True, True, True, "JDB"),
    # Pragmatic Play
    "Buffalo King Untamed Megaways™": GameConfig(False, True, True, True, True, True, "PP"),
    "Gates of Gatot Kaca 1000": GameConfig(False, True, True, True, True, True, "PP"),
    "Gates of Olympus 1000": GameConfig(False, True, True, True, True, True, "PP"),
    "Gates of Olympus Xmas 1000": GameConfig(False, True, True, True, True, True, "PP"),
    "Starlight Princess 1000": GameConfig(False, True, True, True, True, True, "PP"),
    "Starlight Princess Pachi": GameConfig(False, True, True, True, True, True, "PP"),
    "Sugar Rush 1000": GameConfig(False, True, True, True, True, True, "PP"),
    "Sugar Rush™": GameConfig(False, True, True, True, True, True, "PP"),
    "Sweet Bonanza 1000": GameConfig(False, True, True, True, True, True, "PP"),
    "Sweet Bonanza Xmas": GameConfig(False, True, True, True, True, True, "PP"),
    "Wisdom of Athena 1000": GameConfig(False, True, True, True, True, True, "PP"),
    "Zeus vs Hades - Gods of War": GameConfig(False, True, True, True, True, True, "PP"),
    # JFF
    # "Fortune Gems (JFF)": GameConfig(False, True, True, None, False, True, "JFF"),
    # "Fortune Gems 2 (JFF)": GameConfig(False, True, True, None, False, True, "JFF"),
    # "Fortune Gems 3 (JFF)": GameConfig(False, True, True, None, False, True, "JFF"),
    # R88
    "Maya Gems": GameConfig(False, True, True, None, False, True, "R88"),
    # Royal Slot Gaming
    "Fortune Gems 4": GameConfig(False, True, True, None, False, False, "RSG"),
    "Super Ace 2": GameConfig(False, True, True, None, False, True, "RSG"),
    # Yellow Bat
    "Dragon Gems": GameConfig(False, True, True, None, False, True, "YB"),
    "Golden Aztec Mega": GameConfig(False, True, True, None, False, True, "YB"),
    "Power Fortune": GameConfig(False, True, True, None, False, True, "YB"),
    "Sugar Crush": GameConfig(False, True, True, None, False, True, "YB"),
    "Super Egypt": GameConfig(False, True, True, None, False, True, "YB"),
}

DEFAULT_GAME_CONFIG = GameConfig(False, True, True, None, False, False, None)

ProviderProps = namedtuple("ProviderProps", [ "provider", "color", "img_url" ])

PROVIDERS = {
    "JILI": ProviderProps("Jili", LRED, "41786877e5b48c0f35948ec66abdc1bd"),
    "PG": ProviderProps("PG Slots", LCYN, "02ee299d177a5a4f39645cf0392243b0"),
    "FC": ProviderProps("Fa Chai", YEL, "25bd8e424761c1572da6d990e8515e52"),
    "PP": ProviderProps("Pragmatic Play", LMAG, "aea0a2cbc715c3d2ce3d0e802361d859"),
    "BNG": ProviderProps("BNG", BLCYN, "61ae92544fbe87d4271f20e29ca389a1"),
    "JDB": ProviderProps("JDB", LBLU, "7594bb75a92e18ff81c7c8e1d65a6dad"),
    "YB": ProviderProps("Yellow Bat", LYEL, "92ee026c472b91d14c61e38d32cce3eb"),
    "CQ9": ProviderProps("CQ9", CYN, "cq9"),
    "CEWIN": ProviderProps("CE Win", MAG, "abf4cf415aa6292c7fca502425c987d5"),
    "MW": ProviderProps("Mega Win", GRE, "3bf4202ead643e783126554143bd52e0"),
    "RSG": ProviderProps("Royal Slot Gaming", RED, "4ac8285dc8ba6fb336c5bafb3c10b246"),
    "R88": ProviderProps("R88", DGRY, "7a45dcd8865cc3922917682df217571a"),
    "KA": ProviderProps("KA Gaming", LGRY, "50ea64224d3e6b76c68bdd6e39740661"),
    "SG": ProviderProps("Spadegaming", LGRE, "027a3554136a9f4b03bbf92e25da6396"),
    "NET": ProviderProps("NET Entertainment", WHTE, "2f61a64aa0e14422adf6334f52fc1bf0"),
    "AMS": ProviderProps("Ask Me Slot", WHTE, "d9476193be84830ee6e05b7ebe3df5e6"),
    "DS": ProviderProps("Dragoon Soft", WHTE, "001e5786030e25f207e329ed2a820c5d"),
    "HSG": ProviderProps("Hacksaw Gaming", WHTE, "7b6c3cb2219792a230e1d022c6986cfc"),
    "AMEBA": ProviderProps("AMEBA Entertainment", WHTE, "9be642a0e1d8a3a7c5e015d09f08adfe"),
    "BTG": ProviderProps("BTG", WHTE, "7adfed5a9cd06a581eff167bfbadd630"),
    "MEGA": ProviderProps("MEGA Entertainment", WHTE, "40d155acff304e642252f253993b126e"),
    "DNA": ProviderProps("DNA Slot", WHTE, "a035b23795134651bcd27a923b7453f9"),
    "WM": ProviderProps("World Match", WHTE, "f6823427a35f41b1a378ad050a676db8"),
    "FIVE": ProviderProps("5", WHTE, "014e6a00b1ff714d5e5cd44064d16f48"),
    "NEXT": ProviderProps("Next Spin", WHTE, "6ad041e11133876eda65b5f993a66d4f"),
    "RG": ProviderProps("Rich Game", WHTE, "133480bdccbc68ca1bc4cea932a0e8b7"),
    "MAHA": ProviderProps("MAHA Gaming", WHTE, "fb40ff7da5ca4a8cbd1383d7d89c5b0f"),
    "BT": ProviderProps("BT Gaming", WHTE, "78eaafcc8f8e8bf4716e5dcb416c1abb"),
    # "JFF": ProviderProps("JFF", MAG, ""),
}

DEFAULT_PROVIDER_PROPS = ProviderProps("Jili", WHTE, "41786877e5b48c0f35948ec66abdc1bd")

URLS = [ "https://www.helpslot.win", "https://slimeserveahead.github.io/monitor" ]

API_CONFIG = {
    "host": "0.0.0.0",
    "port": 4444,
    "reload": True,
    "url": next((url for url in URLS if 'helpslot' in url), None),
    "refresh_interval": 1  # fast initial poll interval
}

API_URL = [ "http://localhost:8080", "https://api-jackpot.fly.dev" ]
# API_URL = "https://api-jackpot.fly.dev"
VPS_IP = "66.241.124.83"

USER_AGENTS = [
    # Windows Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/114.0.5735.91 Safari/537.36",
    # Mac Chrome
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/16.1 Safari/605.1.15",
    # Mobile Android Chrome
    "Mozilla/5.0 (Linux; Android 11; Pixel 5) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/113.0.0.0 Mobile Safari/537.36",
    # iPhone Safari
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_3 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/15.3 Mobile/15E148 Safari/604.1"
]