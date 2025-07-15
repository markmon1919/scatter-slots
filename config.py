#!/usr/bin/env .venv/bin/python

import pyautogui
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from collections import namedtuple

def now_time(countdown: bool=False):
    today = datetime.now(timezone.utc).astimezone(ZoneInfo("Asia/Manila"))
    timer_start = (60 - today.second)
    return today if not countdown else timer_start

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
DEFAULT_VOICE = "Samantha"
VOICES = [ "Trinoids", "Kanya", "Karen", "Kathy", "Nora" ]
SOUND_ENABLED = True

# === Default Timeouts ===
SPIN_DELAY_RANGE = (1, 3)  # Used with random.uniform(*SPIN_DELAY_RANGE)
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
    "Fortune Gems": GameConfig(False, True, True, None, False, True, "JILI"),
    "Fortune Gems 2": GameConfig(False, True, True, None, False, True, "JILI"),
    "Fortune Gems 3": GameConfig(False, True, True, None, False, True, "JILI"),
    "Fortune Gems Scratch": GameConfig(False, True, True, None, False, True, "JILI"),
    "Fortune Monkey": GameConfig(False, True, True, None, False, True, "JILI"),
    "Super Rich": GameConfig(False, True, True, None, False, True, "JILI"),
    "Lucky Gaming": GameConfig(False, True, True, None, False, True, "JILI"),
    "Super Ace": GameConfig(False, True, True, None, False, False, "JILI"),
    "Super Ace II": GameConfig(False, True, True, None, False, False, "JILI"),
    "Super Ace Deluxe": GameConfig(False, True, True, None, False, False, "JILI"),
    "Super Ace Joker": GameConfig(False, True, True, None, False, False, "JILI"),
    "Super Ace Scratch": GameConfig(False, True, True, None, False, False, "JILI"),
    "Wild Ace": GameConfig(False, True, True, None, False, False, "JILI"),
    "Mega Ace": GameConfig(False, True, True, None, False, False, "JILI"),
    "Golden Joker": GameConfig(False, True, True, None, False, True, "JILI"),
    "Golden Empire": GameConfig(False, True, True, None, False, True, "JILI"),
    "Golden Queen": GameConfig(False, True, True, None, False, True, "JILI"),
    "Ali Baba": GameConfig(False, True, True, None, False, True, "JILI"),
    "Aztec Priestess": GameConfig(False, True, True, None, False, True, "JILI"),
    "Legacy of Egypt": GameConfig(False, True, True, None, False, True, "JILI"),
    "Pharaoh Treasure": GameConfig(False, True, True, None, False, True, "JILI"),
    "Shōgun": GameConfig(False, True, True, None, False, True, "JILI"),
    "Pirate Queen": GameConfig(False, True, True, None, False, True, "JILI"),
    "Pirate Queen 2": GameConfig(False, True, True, None, False, True, "JILI"),
    "Jungle King": GameConfig(False, True, True, None, False, True, "JILI"),
    "Neko Fortune": GameConfig(False, True, True, None, False, True, "JILI"),
    "Chin Shi Huang": GameConfig(False, True, True, None, False, True, "JILI"),
    "Charge Buffalo": GameConfig(False, True, True, None, False, True, "JILI"),
    "Nightfall Hunting": GameConfig(False, True, True, None, False, True, "JILI"),
    "Night City": GameConfig(False, True, True, None, False, True, "JILI"),
    "Bonus Hunter": GameConfig(False, True, True, None, False, False, "JILI"),
    "Zeus": GameConfig(False, True, True, None, False, False, "JILI"),
    "Crazy777": GameConfig(False, True, True, None, False, True, "JILI"),
    "Money Coming": GameConfig(False, True, True, None, False, True, "JILI"),
    "Money Coming": GameConfig(False, True, True, None, False, True, "JILI"),
    "Money Coming Expand Bets": GameConfig(False, True, True, None, False, True, "JILI"),
    "Golden Bank": GameConfig(False, True, True, None, False, True, "JILI"),
    "Golden Bank 2": GameConfig(False, True, True, None, False, True, "JILI"),
    "Money Pot": GameConfig(False, True, True, None, False, True, "JILI"),
    "Lucky Jaguar": GameConfig(False, True, True, None, False, True, "JILI"),
    "Lucky Goldbricks": GameConfig(False, True, True, None, False, True, "JILI"),
    "Go For Champion": GameConfig(False, True, True, None, False, True, "JILI"),
    "Boxing King": GameConfig(False, True, True, None, False, True, "JILI"),
    "Boxing Extravaganza": GameConfig(False, True, True, None, False, True, "JILI"),
    "Mines": GameConfig(False, True, True, None, False, True, "JILI"),
    "Mega Fishing": GameConfig(False, True, True, None, False, True, "JILI"),
    "Jackpot Fishing": GameConfig(False, True, True, None, False, True, "JILI"),
    "Royal Fishing": GameConfig(False, True, True, None, False, True, "JILI"),
    "Wild Bounty Showdown": GameConfig(False, True, True, None, False, False, "PG"),
    "Wild Bandito": GameConfig(False, True, True, None, False, False, "PG"),
    "Wild Ape": GameConfig(False, True, True, None, False, False, "PG"),
    "Wild Ape x10000": GameConfig(False, True, True, None, False, False, "PG"),
    "Wild Fireworks": GameConfig(False, True, True, None, False, False, "PG"),
    "Wild Coaster": GameConfig(False, True, True, None, False, False, "PG"),
    "Yakuza Honor": GameConfig(False, True, True, None, False, False, "PG"),
    "Asgardian Rising": GameConfig(False, True, True, None, False, False, "PG"),
    "Legendary Monkey King": GameConfig(False, True, True, None, False, False, "PG"),
    "Fortune Mouse": GameConfig(False, True, True, None, False, False, "PG"),
    "Fortune Rabbit": GameConfig(False, True, True, None, False, False, "PG"),
    "Majestic Treasures": GameConfig(False, True, True, None, False, False, "PG"),
    "Jurassic Kingdom": GameConfig(False, True, True, None, False, False, "PG"),
    "Cruise Royale": GameConfig(False, True, True, None, False, False, "PG"),
    "Gemstones Gold": GameConfig(False, True, True, None, False, False, "PG"),
    "Dragon Hatch": GameConfig(False, True, True, None, False, False, "PG"),
    "Dragon Hatch 2": GameConfig(False, True, True, None, False, False, "PG"),
    "Queen of Bounty": GameConfig(False, True, True, None, False, False, "PG"),
    "Captain's Bounty": GameConfig(False, True, True, None, False, False, "PG"),
    "Treasures of Aztec": GameConfig(False, True, True, None, False, False, "PG"),
    "Oishi Delights": GameConfig(False, True, True, None, False, False, "PG"),
    "Ways of the Qilin": GameConfig(False, True, True, None, False, False, "PG"),
    "Heist of Stakes": GameConfig(False, True, True, None, False, False, "PG"),
    "Lucky Neko": GameConfig(False, True, True, None, False, False, "PG"),
    "Egypt's Book of Mystery": GameConfig(False, True, True, None, False, False, "PG"),
    "Grand Blue": GameConfig(True, True, True, None, False, False, "FC"),
    "Golden Genie": GameConfig(True, True, True, None, False, False, "FC"),
    "Egypt Bonanza": GameConfig(True, True, True, None, False, False, "FC"),
    "Fortune Goddess": GameConfig(True, True, True, None, False, False, "FC"),
    "Lucky Fortunes": GameConfig(True, True, True, None, False, False, "FC"),
    "Queen of Inca": GameConfig(True, True, True, None, False, False, "FC"),
    "Gods Grant Fortune": GameConfig(True, True, True, None, False, False, "FC"),
    "Starlight Princess Pachi": GameConfig(False, True, True, True, True, True, "PP"),
    "Starlight Princess 1000": GameConfig(False, True, True, True, True, True, "PP"),
    "Wisdom of Athena 1000": GameConfig(False, True, True, True, True, True, "PP"),
    "Gates of Gatot Kaca 1000": GameConfig(False, True, True, True, True, True, "PP"),
    "Gates of Olympus 1000": GameConfig(False, True, True, True, True, True, "PP"),
    "Gates of Olympus Xmas 1000": GameConfig(False, True, True, True, True, True, "PP"),
    "Zeus vs Hades - Gods of War": GameConfig(False, True, True, True, True, True, "PP"),
    "Sugar Rush™": GameConfig(False, True, True, True, True, True, "PP"),
    "Sugar Rush 1000": GameConfig(False, True, True, True, True, True, "PP"),
    "Sweet Bonanza 1000": GameConfig(False, True, True, True, True, True, "PP"),
    "Sweet Bonanza Xmas": GameConfig(False, True, True, True, True, True, "PP"),
    "Fruity Bonanza Combo": GameConfig(False, True, True, True, True, True, "JDB"),
    "Lucky Diamond": GameConfig(False, True, True, True, True, True, "JDB"),
    "Wonder Elephant": GameConfig(False, True, True, True, True, True, "JDB"),
    "Magic Ace Wild Lock": GameConfig(False, True, True, True, True, True, "JDB"),
    "Super Egypt": GameConfig(False, True, True, None, False, True, "YB"),
    "Power Fortune": GameConfig(False, True, True, None, False, True, "YB"),
    "Dragon Gems": GameConfig(False, True, True, None, False, True, "YB"),
    "Golden Aztec Mega": GameConfig(False, True, True, None, False, True, "YB"),
    "Fortune Gems (JFF)": GameConfig(False, True, True, None, False, True, "JFF"),
    "Fortune Gems 2 (JFF)": GameConfig(False, True, True, None, False, True, "JFF"),
    "Fortune Gems 3 (JFF)": GameConfig(False, True, True, None, False, True, "JFF"),
    "Fortune Gems 4": GameConfig(False, True, True, None, False, True, "RSG"),
    "Super Ace 2": GameConfig(False, True, True, None, False, True, "RSG"),
    "Maya Gems": GameConfig(False, True, True, None, False, True, "R88"),
}

DEFAULT_GAME_CONFIG = GameConfig(False, True, True, None, False, False, None)

ProviderProps = namedtuple("ProviderProps", [ "provider", "color" ])

PROVIDERS = {
    "JILI": ProviderProps("Jili", LRED),
    "FC": ProviderProps("Fa Chai", YEL),
    "PG": ProviderProps("PG Slots", LCYN),
    "PP": ProviderProps("Pragmatic Play", LMAG),
    "JDB": ProviderProps("JDB", LBLU),
    "YB": ProviderProps("Yellow Bat", LYEL),
    "JFF": ProviderProps("JFF", MAG),
    "R88": ProviderProps("R88", GRE),
    "RSG": ProviderProps("Royal Slot Gaming", RED),
}

DEFAULT_PROVIDER_PROPS = ProviderProps(None, WHTE)

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

CASINOS = [ "JLJL9", "Bingo Plus", "Win PH", "Casino Plus", "Rollem 88", "2JL" ]

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