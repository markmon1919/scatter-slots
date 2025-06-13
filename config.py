import pyautogui
from collections import namedtuple

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
SOUND_ENABLED = True

# === Default Timeouts ===
DELAY_RANGE = (2, 4)  # Used with random.randint(*DELAY_RANGE)

GameConfig = namedtuple("GameConfig", [
    "spin", "auto_spin", "turbo", "feature",
    "auto_play_menu", "widescreen", "provider"
])

GAME_CONFIGS = {
    "Fortune Gems": GameConfig(False, True, True, None, False, True, "JILI"),
    "Fortune Gems 2": GameConfig(False, True, True, None, False, True, "JILI"),
    "Fortune Gems 3": GameConfig(False, True, True, None, False, True, "JILI"),
    "Fortune Monkey": GameConfig(False, True, True, None, False, True, "JILI"),
    "Super Ace": GameConfig(False, True, True, None, False, False, "JILI"),
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
    "Neko Fortune": GameConfig(False, True, True, None, False, True, "JILI"),
    "Chin Shi Huang": GameConfig(False, True, True, None, False, True, "JILI"),
    "Charge Buffalo": GameConfig(False, True, True, None, False, True, "JILI"),
    "Crazy777": GameConfig(False, True, True, None, False, True, "JILI"),
    "Golden Bank": GameConfig(False, True, True, None, False, True, "JILI"),
    "Golden Bank 2": GameConfig(False, True, True, None, False, True, "JILI"),
    "Lucky Jaguar": GameConfig(False, True, True, None, False, True, "JILI"),
    "Lucky Goldbricks": GameConfig(False, True, True, None, False, True, "JILI"),
    "Go For Champion": GameConfig(False, True, True, None, False, True, "JILI"),
    "Boxing Extravaganza": GameConfig(False, True, True, None, False, True, "JILI"),
    "Wild Bounty Showdown": GameConfig(False, True, True, None, False, False, "PG"),
    "Legendary Monkey King": GameConfig(False, True, True, None, False, False, "PG"),
    "Majestic Treasures": GameConfig(False, True, True, None, False, False, "PG"),
    "Grand Blue": GameConfig(True, True, True, None, False, False, "FC"),
    "Golden Genie": GameConfig(True, True, True, None, False, False, "FC"),
    "Egypt Bonanza": GameConfig(True, True, True, None, False, False, "FC"),
    "Fortune Goddess": GameConfig(True, True, True, None, False, False, "FC"),
    "Lucky Fortunes": GameConfig(True, True, True, None, False, False, "FC"),
    "Gods Grant Fortune": GameConfig(True, True, True, None, False, False, "FC"),
    "Starlight Princess Pachi": GameConfig(False, True, True, True, True, True, "PP"),
    "Starlight Princess 1000": GameConfig(False, True, True, True, True, True, "PP"),
    "Wisdom of Athena 1000": GameConfig(False, True, True, True, True, True, "PP"),
    "Gates of Gatot Kaca 1000": GameConfig(False, True, True, True, True, True, "PP"),
    "Gates of Olympus Xmas 1000": GameConfig(False, True, True, True, True, True, "PP"),
    "Sugar Rush™": GameConfig(False, True, True, True, True, True, "PP"),
    "Sugar Rush 1000": GameConfig(False, True, True, True, True, True, "PP"),
    "Fruity Bonanza Combo": GameConfig(False, True, True, True, True, True, "JDB"),
    "Lucky Diamond": GameConfig(False, True, True, True, True, True, "JDB"),
    "Wonder Elephant": GameConfig(False, True, True, True, True, True, "JDB"),
    "Magic Ace Wild Lock": GameConfig(False, True, True, True, True, True, "JDB"),
}

DEFAULT_GAME_CONFIG = GameConfig(False, True, True, None, False, False, None)

PROVIDERS = {
    "JILI": "Jili",
    "FC": "Fa Chai",
    "PG": "PG Slots",
    "PP": "Pragmatic Play",
    "JDB": "JDB"
}

URLS = [ "https://www.helpslot.win/home", "https://slimeserveahead.github.io/monitor" ]

CASINOS = [ "JLJL9", "Bingo Plus", "Casino Plus", "Rollem 88", "2JL" ]
