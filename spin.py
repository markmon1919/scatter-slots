#!/usr/bin/env .venv/bin/python

import math, platform, threading, time, random, re, requests, pyautogui, subprocess, sys
from dataclasses import dataclass, field
from trend import load_trend_memory, search_game_data_from_local_api, enrich_game_data
from queue import Queue as ThQueue, Empty
from concurrent.futures import ThreadPoolExecutor, wait
from pynput.keyboard import Listener as KeyboardListener, Key, KeyCode
from config import (PROVIDERS, DEFAULT_PROVIDER_PROPS, URLS, API_URL, SCREEN_POS, LEFT_SLOT_POS, RIGHT_SLOT_POS, PING, VOICES, HOLD_DELAY_RANGE, SPIN_DELAY_RANGE, TIMEOUT_DELAY_RANGE, VOICES,
                    LRED, LBLU, LCYN, LYEL, LMAG, LGRE, LGRY, RED, MAG, YEL, GRE, CYN, BLU, WHTE, BLRED, BLYEL, BLGRE, BLMAG, BLBLU, BLCYN, BYEL, BGRE, BMAG, BCYN, BWHTE, DGRY, BLNK, CLEAR, RES)


@dataclass
class AutoState:
    manual_select: bool = True
    game_name: str = None
    jackpot_value: str = None
    meter_color: str = None
    min10: float = 0.0
    hr1: float = 0.0
    hr3: float = 0.0
    hr6: float = 0.0
    m10: float = 0.0
    h1: float = 0.0
    h3: float = 0.0
    h6: float = 0.0
    trending: bool = False
    bet_lvl: str = None

def render_providers():
    print(f"\n\n\t📘 {MAG}SCATTER SLOT SPINNER{RES}\n\n")

    providers = list(PROVIDERS.items())
    half = (len(providers) + 1) // 2
    lines = list()
    
    for idx, (left_provider, left_conf) in enumerate(providers[:half], start=1):
        left_color = left_conf.color
        left_str = f"[{WHTE}{idx}{RES}] - {left_color}{left_conf.provider}{RES}\t"

        right_index = idx - 1 + half
        if right_index < len(providers):
            right_provider, right_conf = providers[right_index]
            right_color = right_conf.color
            right_str = f"[{WHTE}{right_index + 1:>2}{RES}] - {right_color}{right_conf.provider}{RES}"
        else:
            right_str = ""

        lines.append(f"\t{left_str:<50}\t{right_str}")
    return "\n".join(lines)

def providers_list():
    providers = list(PROVIDERS.items())

    while True:
        try:
            choice = int(input("\n\t🔔 Choose Provider: "))
            if 1 <= choice <= len(providers):
                provider = providers[choice - 1][0]
                provider_name = providers[choice - 1][1].provider
                provider_color = providers[choice - 1][1].color
                print(f"\n\tSelected: {provider_color}{provider_name} {RES}({provider_color}{provider}{RES})")
                return provider, provider_name
            else:
                print("\t⚠️  Invalid choice. Try again.")
        except ValueError:
            print("\t⚠️  Please enter a valid number.")
            
def providers_list():
    providers = list(PROVIDERS.items())

    while True:
        try:
            choice = int(input("\n\t🔔 Choose Provider: "))
            if 1 <= choice <= len(providers):
                provider = providers[choice - 1][0]
                provider_name = providers[choice - 1][1].provider
                provider_color = providers[choice - 1][1].color
                print(f"\n\tSelected: {provider_color}{provider_name} {RES}({provider_color}{provider}{RES})\n\n")
                return provider, provider_name
            else:
                print("\t⚠️  Invalid choice. Try again.")
        except ValueError:
            print("\t⚠️  Please enter a valid number.")
            
def spin(combo_spin: bool = False, spam_spin: bool = False):
    # while not stop_event.is_set():
    if spin_in_progress.is_set():
        print("\t⚠️ Spin still in action, skipping")
        return
    
    spin_in_progress.set()

    try:
        # cmd, combo_spin = spin_queue.get_nowait()
        # spin_in_progress, combo_spin = spin_queue.get(timeout=1)
        spin_types = [ "normal_spin", "spin_hold", "spin_delay", "spin_hold_delay", "turbo_spin", "board_spin", "board_spin_hold", "board_spin_delay", "board_spin_hold_delay", "board_spin_turbo", "spin_slide", "auto_spin" ]
        
        if not combo_spin and "PG" in provider:
            spin_types = [s for s in spin_types if not s.startswith("board")]

        if combo_spin:
            spin_types = [s for s in spin_types if s.startswith("board")]
            spin_types.extend(["combo_spin", "spam_spin", "turbo_spin"])

        spin_type = random.choice(spin_types) if not spam_spin else "spam_spin"
        cx, cy = CENTER_X, CENTER_Y

        shrink_percentage = 60 if widescreen else 32
        width = int(max(RIGHT_X, BTM_Y) * (shrink_percentage / 100))
        height = int(min(RIGHT_X, BTM_Y) * (shrink_percentage / 100))
        border_space_top = cy // 3 if widescreen else 0
        radius_x, radius_y = width // 2, height // 2 #if widescreen else width // 2
        # rand_x = cx + random.randint(-radius_x, radius_x)
        # rand_y = cy + random.randint(-radius_y, radius_y) + (border_space_top if radius_y <= 0 else -border_space_top)
        # rand_x2 = cx - random.randint(-radius_x, radius_x)
        # rand_y2 = cy - random.randint(-radius_y, radius_y) + (border_space_top if radius_y <= 0 else -border_space_top)
        rand_x = cx - random.randint(-radius_x, radius_x)
        rand_y = random.randint(200, cy)
        # mystic = 100
        # cruise_royal = 100
        # queen of bounty = cy

        rand_x2 = cx - random.randint(-radius_x, radius_x)
        rand_y2 = random.randint(200, cy)

        # print(f'\theight >>> {height}')
        # print(f'\tBTM_Y >>> {BTM_Y}')
        # print(f'\tcx >>> {cx}')
        # print(f'\tcy >>> {cy}')
        # print(f'\tradius_x >>> {radius_x}')
        # print(f'\tradius_y >>> {radius_y}')
        # print(f'\trand_x >>> {rand_x}')
        # print(f'\trand_y >>> {rand_y}')
        # print(f'\trand_x2 >>> {rand_x2}')
        # print(f'\trand_y2 >>> {rand_y2}')
        
        action = []

        hold_delay = random.uniform(*HOLD_DELAY_RANGE)
        spin_delay = random.uniform(*SPIN_DELAY_RANGE)
        timeout_delay = random.uniform(*TIMEOUT_DELAY_RANGE)
        # print(f'widescreen: {widescreen}')
        # print(f'spin_btn: {spin_btn}')
        # spin_type = "normal_spin"
        
        if spin_type == "normal_spin":
            if widescreen:
                action.extend([
                    lambda: pyautogui.click(x=cx + 520, y=cy + 325, button='left'),
                    lambda: pyautogui.click(x=cx + 520, y=cy + 325, button='right'),
                    lambda: pyautogui.press('space'),
                    lambda: (pyautogui.keyDown('space'), pyautogui.keyUp('space')),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='left'), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='right'), pyautogui.mouseUp())
                ])
            else:
                # NO RIGHT CLICK FOR BUTTON IN PG (BUT MOUSEDOWN IS GOOD)
                action.extend([
                    lambda: pyautogui.click(x=cx, y=BTM_Y - 105, button='left'),
                    # lambda: pyautogui.click(x=cx, y=BTM_Y - 105, button='right'),
                    lambda: pyautogui.press('space'),
                    lambda: (pyautogui.keyDown('space'), pyautogui.keyUp('space')),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), pyautogui.mouseUp())
                ]) if not spin_btn else \
                action.extend([
                    lambda: pyautogui.click(x=cx, y=BTM_Y - 105, button='left'),
                    lambda: pyautogui.click(x=cx, y=BTM_Y - 105, button='right'),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), pyautogui.mouseUp())
                ])
        elif spin_type == "spin_hold":
            if widescreen:
                action.extend([
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), pyautogui.mouseDown(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), pyautogui.mouseDown(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), pyautogui.mouseDown(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), pyautogui.mouseDown(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'))
                ])
                
            else:
                action.extend([
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.mouseDown(button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.mouseDown(button='right')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.mouseDown(button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.mouseDown(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.press('space'), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.press('space'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.keyDown('space'), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.keyDown('space'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'))
                ]) if not spin_btn else \
                action.extend([
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.mouseDown(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.mouseDown(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.mouseDown(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.mouseDown(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'))
                ])
        elif spin_type == "spin_delay":
            if widescreen:
                action.extend([
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(button='left')),
                    # lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(button='right')),
                    # lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='left')),
                    # lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='right')),
                    # lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.keyUp('space')),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='right'), time.sleep(hold_delay), pyautogui.mouseUp())
                ])
            else:
                action.extend([
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.press('space')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(button='right')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(button='right')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.keyUp('space')),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.mouseUp())
                ]) if not spin_btn else \
                action.extend([
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(button='left')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(button='right')),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.mouseUp())
                ])
        elif spin_type == "spin_hold_delay":
            if widescreen:
                action.extend([
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.press('space')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='left')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 325, button='right')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='right')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='right'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='right'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 325, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),                       
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),                        
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right'))
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='right'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='right'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='right'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='right'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'))
                ])
            else:
                action.extend([
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.press('space')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.press('space')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),                       
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),                        
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right'))
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'))
                ]) if not spin_btn else \
                action.extend([
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),                       
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),                        
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right'))
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'), time.sleep(hold_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'))
                ])
        elif spin_type == "board_spin":
            if widescreen:
                action.extend([
                    lambda: pyautogui.click(x=rand_x, y=rand_y, button='left'),
                    lambda: pyautogui.click(x=rand_x, y=rand_y, button='right'),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), pyautogui.mouseUp())
                ])
            else:
                action.extend([
                    lambda: pyautogui.click(x=rand_x, y=rand_y, button='left'),
                    # lambda: pyautogui.click(x=rand_x, y=rand_y, button='right'),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), pyautogui.mouseUp())
                ]) if not spin_btn else \
                action.extend([
                    lambda: pyautogui.click(x=rand_x, y=rand_y, button='left'),
                    lambda: pyautogui.click(x=rand_x, y=rand_y, button='right'),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), pyautogui.mouseUp())
                ])
        elif spin_type == "board_spin_hold":
            if widescreen:
                action.extend([
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.mouseDown(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.mouseDown(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.mouseDown(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.mouseDown(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y), pyautogui.mouseDown(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y), pyautogui.mouseDown(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y), pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y), pyautogui.mouseDown(x=cx + 520, y=cy + 325, button='right'))
                ])
            else:
                action.extend([
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.mouseDown(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.mouseDown(button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.mouseDown(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.mouseDown(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y), pyautogui.mouseDown(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y), pyautogui.mouseDown(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'))
                ]) if not spin_btn else \
                action.extend([
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.mouseDown(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.mouseDown(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.mouseDown(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.mouseDown(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y), pyautogui.mouseDown(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y), pyautogui.mouseDown(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y), pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button='right'))
                ])
        elif spin_type == "board_spin_delay":
            if widescreen:
                action.extend([
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.mouseUp())
                ])
            else:
                action.extend([
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.press('space')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.mouseUp())
                ]) if not spin_btn else \
                action.extend([
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.mouseUp())
                ])
        elif spin_type == "board_spin_hold_delay":
            if widescreen:
                action.extend([
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='left')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='left')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(button='right'))
                ])
            else:
                action.extend([
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.press('space')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.keyDown('space')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(button='right'))
                ]) if not spin_btn else \
                action.extend([
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(button='right')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(button='left')),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(button='right'))
                ])
        elif spin_type == "spin_slide":
            if widescreen:
                action.extend([
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.moveTo(x=rand_x2, y=rand_y2), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.moveTo(x=rand_x2, y=rand_y2), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), pyautogui.moveTo(x=rand_x2, y=rand_y2), time.sleep(hold_delay), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), pyautogui.moveTo(x=rand_x2, y=rand_y2), time.sleep(hold_delay), pyautogui.mouseUp())
                ])
            else:
                action.extend([
                    lambda: (pyautogui.press('space'), time.sleep(timeout_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), pyautogui.moveTo(x=rand_x2, y=rand_y2), pyautogui.mouseUp()),
                    lambda: (pyautogui.press('space'), time.sleep(timeout_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), pyautogui.moveTo(x=rand_x2, y=rand_y2), pyautogui.mouseUp()),
                    lambda: (pyautogui.press('space'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), pyautogui.moveTo(x=rand_x2, y=rand_y2), time.sleep(hold_delay), pyautogui.mouseUp()),
                    lambda: (pyautogui.press('space'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), pyautogui.moveTo(x=rand_x2, y=rand_y2), time.sleep(hold_delay), pyautogui.mouseUp()),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(timeout_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), pyautogui.moveTo(x=rand_x2, y=rand_y2), pyautogui.mouseUp()),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(timeout_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), pyautogui.moveTo(x=rand_x2, y=rand_y2), pyautogui.mouseUp()),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(timeout_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), pyautogui.moveTo(x=rand_x2, y=rand_y2), pyautogui.mouseUp()),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), time.sleep(timeout_delay), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), pyautogui.moveTo(x=rand_x2, y=rand_y2), pyautogui.mouseUp()),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), pyautogui.moveTo(x=rand_x2, y=rand_y2), time.sleep(hold_delay), pyautogui.mouseUp()),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), pyautogui.moveTo(x=rand_x2, y=rand_y2), time.sleep(hold_delay), pyautogui.mouseUp()),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), pyautogui.moveTo(x=rand_x2, y=rand_y2), time.sleep(hold_delay), pyautogui.mouseUp()),
                    # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), pyautogui.moveTo(x=rand_x2, y=rand_y2), time.sleep(hold_delay), pyautogui.mouseUp())
                ]) if not spin_btn else \
                action.extend([
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.moveTo(x=rand_x2, y=rand_y2), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.moveTo(x=rand_x2, y=rand_y2), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), pyautogui.moveTo(x=rand_x2, y=rand_y2), time.sleep(hold_delay), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), pyautogui.moveTo(x=rand_x2, y=rand_y2), time.sleep(hold_delay), pyautogui.mouseUp())
                ])
        elif spin_type == "board_spin_turbo":
            if widescreen:
                action.extend([
                    lambda: pyautogui.doubleClick(x=rand_x, y=rand_y, button='left'),
                    lambda: pyautogui.doubleClick(x=rand_x, y=rand_y, button='right'),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(x=cx + 520, y=cy + 325, button='right'))
                ])
            else:
                action.extend([
                    lambda: pyautogui.doubleClick(x=rand_x, y=rand_y, button='left'),
                    # lambda: pyautogui.doubleClick(x=rand_x, y=rand_y, button='right'),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.press('space')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.keyDown('space')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'))
                ]) if not spin_btn else \
                action.extend([
                    lambda: pyautogui.doubleClick(x=rand_x, y=rand_y, button='left'),
                    lambda: pyautogui.doubleClick(x=rand_x, y=rand_y, button='right'),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'))
                ])
        elif spin_type == "turbo_spin":
            if widescreen:
                action.extend([
                    lambda: pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='left'),
                    lambda: pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='right'),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.press('space')),
                    lambda: (pyautogui.press('space'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.click(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.click(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.press('space')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.click(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.click(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.click(x=rand_x, y=rand_y, button='right'))
                ])
            else:
                if "PG" in provider:
                    action.extend([
                        lambda: pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left'),
                        # lambda: pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right'),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(button='left')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(button='right')),
                        # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(button='left')),
                        # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(button='right')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(button='left')),
                        # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(button='right')),
                        # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(button='left')),
                        # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(button='right')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                        # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                        # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                        # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                        # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                        # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                        # lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                        # TURBO ENABLED
                        lambda: (pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left')),
                        # lambda: (pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left')),
                        # lambda: (pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left')),
                        # lambda: (pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left')),
                        # lambda: (pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='right'), pyautogui.press('space'), pyautogui.click(x=cx - 200, y=BTM_Y - 105, button='left')),
                        # TURBO ENABLED
                        lambda: (pyautogui.press('space'), pyautogui.press('space')),
                        lambda: (pyautogui.press('space'), pyautogui.keyDown('space')),
                        
                        lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                        # lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),

                        lambda: (pyautogui.press('space'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(button='left')),
                        # lambda: (pyautogui.press('space'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(button='right')),
                        # lambda: (pyautogui.press('space'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(button='left')),
                        # lambda: (pyautogui.press('space'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(button='right'))
                    ])
                else:
                    action.extend([
                        lambda: pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left'),
                        lambda: pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right'),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.press('space')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.press('space')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.keyDown('space')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.keyDown('space')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(button='left')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(button='right')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(button='left')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(button='right')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(button='left')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(button='right')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(button='left')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(button='right')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                        lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                        lambda: (pyautogui.press('space'), pyautogui.press('space')),
                        lambda: (pyautogui.press('space'), pyautogui.keyDown('space')),
                        lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                        lambda: (pyautogui.press('space'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.press('space'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                        lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                        lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                        lambda: (pyautogui.press('space'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                        lambda: (pyautogui.press('space'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                        lambda: (pyautogui.keyDown('space'), pyautogui.press('space')),
                        lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                        lambda: (pyautogui.keyDown('space'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.keyDown('space'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                        lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                        lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                        lambda: (pyautogui.keyDown('space'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                        lambda: (pyautogui.keyDown('space'), pyautogui.click(x=rand_x, y=rand_y, button='right'))
                    ]) if not spin_btn else \
                action.extend([
                    #
                ])
        elif spin_type == "auto_spin":
            if widescreen:
                action.extend([
                    lambda: pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='left'),
                    lambda: pyautogui.doubleClick(x=cx + 380, y=cy + 325, button='right'),
                    lambda: (pyautogui.click(x=cx + 380, y=cy + 325, button='left'), pyautogui.click(x=cx + 380, y=cy + 325,button='left')),
                    lambda: (pyautogui.click(x=cx + 380, y=cy + 325, button='right'), pyautogui.click(x=cx + 380, y=cy + 325,button='right'))
                ])
            else:
                if "PG" in provider:
                    action.extend([
                        lambda: (pyautogui.click(x=cx + 195, y=BTM_Y - 105, button='left'), time.sleep(0.3), pyautogui.click(x=cx - 195, y=BTM_Y - 205, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(1.5), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.click(x=cx + 195, y=BTM_Y - 105, button='left'), time.sleep(0.3), pyautogui.click(x=cx - 100, y=BTM_Y - 205, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(1.5), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.click(x=cx + 195, y=BTM_Y - 105, button='left'), time.sleep(0.3), pyautogui.click(x=cx, y=BTM_Y - 205, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(1.5), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.click(x=cx + 195, y=BTM_Y - 105, button='left'), time.sleep(0.3), pyautogui.click(x=cx + 100, y=BTM_Y - 205, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(1.5), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.click(x=cx + 195, y=BTM_Y - 105, button='left'), time.sleep(0.3), pyautogui.click(x=cx + 195, y=BTM_Y - 205, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(1.5), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                        # lambda: (pyautogui.click(x=cx + 195, y=BTM_Y - 105, button='right'), time.sleep(0.3), pyautogui.click(x=cx - 195, y=BTM_Y - 205, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(0.9), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                        # lambda: (pyautogui.click(x=cx + 195, y=BTM_Y - 105, button='right'), time.sleep(0.3), pyautogui.click(x=cx - 100, y=BTM_Y - 205, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(0.9), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                        # lambda: (pyautogui.click(x=cx + 195, y=BTM_Y - 105, button='right'), time.sleep(0.3), pyautogui.click(x=cx, y=BTM_Y - 205, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(0.9), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                        # lambda: (pyautogui.click(x=cx + 195, y=BTM_Y - 105, button='right'), time.sleep(0.3), pyautogui.click(x=cx + 100, y=BTM_Y - 205, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(0.9), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                        # lambda: (pyautogui.click(x=cx + 195, y=BTM_Y - 105, button='right'), time.sleep(0.3), pyautogui.click(x=cx + 195, y=BTM_Y - 205, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), time.sleep(0.9), pyautogui.click(x=cx, y=BTM_Y - 105, button='left'))
                    ])
                else:
                    action.extend([
                        lambda: pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='left'),
                        lambda: pyautogui.doubleClick(x=cx + 95, y=BTM_Y - 105, button='right'),
                        lambda: (pyautogui.click(x=cx + 95, y=BTM_Y - 105, button='left'), pyautogui.click(x=cx + 95, y=BTM_Y - 105, button='left')),
                        lambda: (pyautogui.click(x=cx + 95, y=BTM_Y - 105, button='right'), pyautogui.click(x=cx + 95, y=BTM_Y - 105, button='right'))
                    ]) if not spin_btn else \
                action.extend([
                    #
                ])
        elif spin_type == "combo_spin":
            action.extend([
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.moveTo(x=rand_x2, y=rand_y2), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.moveTo(x=rand_x2, y=rand_y2), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), pyautogui.moveTo(x=rand_x2, y=rand_y2), time.sleep(hold_delay), pyautogui.mouseUp()),
                    lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='right'), pyautogui.moveTo(x=rand_x2, y=rand_y2), time.sleep(hold_delay), pyautogui.mouseUp()),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.press('space')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.keyUp('space')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    # spam
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_y2, y=rand_y2, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.click(x=rand_y2, y=rand_y2, button='right')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_y2, y=rand_y2, button='left')),
                    # lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), time.sleep(hold_delay), pyautogui.click(x=rand_y2, y=rand_y2, button='right')),
                    lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.click(x=rand_y2, y=rand_y2, button='left')),
                    # lambda: (pyautogui.press('space'), time.sleep(hold_delay), pyautogui.click(x=rand_y2, y=rand_y2, button='right')),
                    # lambda: (pyautogui.keyDown('space'), time.sleep(hold_delay), pyautogui.click(x=rand_y2, y=rand_y2, button='right')),
            ])
        elif spin_type == "spam_spin":
            action.extend([
                lambda: pyautogui.typewrite(['space'] * 6, interval=0),
                lambda: pyautogui.click(x=rand_x, y=rand_y, clicks=6, interval=0, button="left"),
                # lambda: pyautogui.doubleClick(x=rand_x, y=rand_y, clicks=3, interval=0, button="left"),
                lambda: pyautogui.click(x=cx, y=BTM_Y - 105, clicks=6, interval=0, button="left"),
                # lambda: pyautogui.doubleClick(x=cx, y=BTM_Y - 105, clicks=3, interval=0, button="left"),
                
                lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button='left'), time.sleep(hold_delay), pyautogui.moveTo(x=rand_x2, y=rand_y2), pyautogui.mouseUp()),
                lambda: (pyautogui.mouseDown(x=cx, y=BTM_Y - 105, button="left"), pyautogui.typewrite(['space'] * 6, interval=0)),
                lambda: (pyautogui.mouseDown(x=rand_x, y=rand_y, button="left"), pyautogui.typewrite(['space'] * 6, interval=0)),
                lambda: (pyautogui.keyDown('space'), pyautogui.click(x=rand_x, y=rand_y, clicks=6, interval=0, button="left")),
                lambda: (pyautogui.keyDown('space'), pyautogui.click(x=cx, y=BTM_Y - 105, clicks=6, interval=0, button="left")),
                
                lambda: [ (pyautogui.press("space"), pyautogui.click(x=rand_x, y=rand_y, button="left")) for _ in range(3) ],
                # lambda: [ (pyautogui.press("space"), pyautogui.doubleClick(x=rand_x, y=rand_y, button="left")) for _ in range(3) ],
                lambda: [ (pyautogui.press("space"), pyautogui.click(x=cx, y=BTM_Y - 105, button="left")) for _ in range(3) ],
                # lambda: [ (pyautogui.press("space"), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button="left")) for _ in range(3) ],
                lambda: [ (pyautogui.click(x=cx, y=BTM_Y - 105, button="left"), pyautogui.click(x=rand_x, y=rand_y, button="left")) for _ in range(3) ],
            ])
        elif spin_type == "quick_spin":
            if widescreen:
                action.extend([
                    lambda: pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='left'),
                    lambda: pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='right'),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='left'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx + 520, y=cy + 325, button='right'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.press('space')),
                    lambda: (pyautogui.press('space'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.click(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.click(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.press('space')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.click(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.click(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: pyautogui.doubleClick(x=rand_x, y=rand_y, button='left'),
                    lambda: pyautogui.doubleClick(x=rand_x, y=rand_y, button='right'),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(x=cx + 520, y=cy + 325, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(x=cx + 520, y=cy + 325, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(x=cx + 520, y=cy + 325, button='right'))
                ])
            else:
                action.extend([
                    lambda: pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left'),
                    lambda: pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right'),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.press('space')),
                    lambda: (pyautogui.press('space'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.press('space'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.press('space'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.press('space')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.keyDown('space'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: pyautogui.doubleClick(x=rand_x, y=rand_y, button='left'),
                    lambda: pyautogui.doubleClick(x=rand_x, y=rand_y, button='right'),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.press('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.keyDown('space')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'))
                ]) if not spin_btn else \
                action.extend([
                    lambda: pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left'),
                    lambda: pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right'),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.doubleClick(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='left'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x, y=rand_y, button='left')),
                    lambda: (pyautogui.click(x=cx, y=BTM_Y - 105, button='right'), pyautogui.click(x=rand_x, y=rand_y, button='right')),
                    lambda: pyautogui.doubleClick(x=rand_x, y=rand_y, button='left'),
                    lambda: pyautogui.doubleClick(x=rand_x, y=rand_y, button='right'),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.doubleClick(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='left'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='left')),
                    lambda: (pyautogui.click(x=rand_x, y=rand_y, button='right'), pyautogui.click(x=cx, y=BTM_Y - 105, button='right'))
                ])

        if not action:
            print(f"\t⚠️ No available spin actions for {spin_type}")
            return
            # continue
            
        # random.choice(init_action)()
        random.choice(action)()
        return spin_type
        
        # now_time = time.time()
        # current_sec = int(now_time) % 60

        # print(f"\tHold Delay: {hold_delay:.2f}")
        # print(f"\tSpin Delay: {spin_delay:.2f}")
        # print(f"\tTimeout Delay: {timeout_delay:.2f}")
        # print(f"\tCombo Spin: {combo_spin}")
        # print(f"\n\t\t<{BLNK}🌀{RES} {RED}{spin_type.replace('_', ' ').upper()} {RES}>\n")
        # alert_queue.put(f"{spin_type}")
        # spin_in_progress.clear()
    finally:
        spin_in_progress.clear()
        # print(f"\n\tHold Delay: {hold_delay:.2f}")
        # print(f"\tSpin Delay: {spin_delay:.2f}")
        # print(f"\tTimeout Delay: {timeout_delay:.2f}")
        # print(f"\tCombo Spin: {combo_spin}")
        print(f"\n\t\t<{BLNK}🌀{RES} {RED}{spin_type.replace('_', ' ').upper()} {RES}>\n")
        # sys.stdout.flush()
        alert_queue.put(spin_type)
    # except Empty:
    #     continue

def play_alert(alert_queue, stop_event):
    if platform.system() == "Darwin":
        while not stop_event.is_set():
            try:
                say = alert_queue.get_nowait()
                sound_file = (say)
                
                if sound_file == "ping":
                    subprocess.run(["afplay", PING])
                else:
                    voice = (
                        VOICES["Karen"] if state.trending or state.bet_lvl == "Bonus" else
                        VOICES["Samantha"]
                    )
                    subprocess.run(["say", "-v", voice, "--", sound_file])
            except Empty:
                time.sleep(0.05)
            except Exception as e:
                print(f"\n\t[Alert Thread Error] {e}")
    else:
        pass

def on_key_press(key):
    try:
        pyautogui.PAUSE = 0
        pyautogui.FAILSAFE = False
        global games, selected_game
        # if hasattr(key, "char") and key.char == "s":
        if key == Key.shift:
            threading.Thread(target=spin, args=(False, False,), daemon=True)
            spin(False, False)
        if key == Key.caps_lock:
            threading.Thread(target=spin, args=(True, False,), daemon=True)
            spin(True, False)
        if key == Key.tab:
            threading.Thread(target=spin, args=(False, True,), daemon=True)
            spin(False, True)
        if key.char.isdigit():
            idx = int(key.char) - 1
            if 0 <= idx < len(games):
                selected_game = games[idx]
                alert_queue.put((f"{selected_game} selected"))
                print(f"\n\t\t🎮 Selected: {YEL}{selected_game.title()}{RES}")
    except AttributeError:
        pass
        # print(f"\n\tError: SPECIAL KEY: {key}")
        
def integrate_game(game: str, url: str, provider: str):
    api_server = API_URL[0]
    
    try:
        response = requests.get(
            f"{api_server}/search",
            params={
                "url": url,
                "game": game,
                "provider": provider
            }
        )
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                return json_data
            except ValueError:
                print(f"❌ Server did not return JSON: {response.text}")
                json_data = {"error": "Invalid JSON response"}
    except Exception as e:
        print(f"❌ Error calling API: {e}")
        
def log_data(game: list):    
    clean_name = re.sub(r"\s*\(.*?\)", "", game.get('name'))
    if "Wild Ape" in clean_name and "PG" in provider:
        clean_name = clean_name.replace("#3258", "").strip()
        
    tag = "💥💥💥 " if game.get('trending') else "🔥🔥🔥 "
    signal = f"{LRED}⬇{RES}" if not game.get('up') else f"{LGRE}⬆{RES}"
    colored_value_10m = f"{RED if game.get('min10') < 0 else GRE if game.get('min10') > 0 else CYN}{' ' + str(game.get('min10')) if game.get('min10') > 0 else game.get('min10')}{RES}"
    colored_value_1h = f"{RED if game.get('hr1') < 0 else GRE if game.get('hr1') > 0 else CYN}{' ' + str(game.get('hr1')) if game.get('hr1') > 0 else game.get('hr1')}{RES}"
    colored_value_3h = f"{RED if game.get('hr3') < 0 else GRE if game.get('hr3') > 0 else CYN}{' ' + str(game.get('hr3')) if game.get('hr3') > 0 else game.get('hr3')}{RES}"
    colored_value_6h = f"{RED if game.get('hr6') < 0 else GRE if game.get('hr6') > 0 else CYN}{' ' + str(game.get('hr6')) if game.get('hr6') > 0 else game.get('hr6')}{RES}"
    
    helpslot_signal = f"{LRED}⬇{RES}" if game.get('meter_color') == "red" else f"{LGRE}⬆{RES}"
    colored_value_10min = f"{RED if game.get('10min') < 0 else GRE if game.get('10min') > 0 else CYN}{' ' + str(game.get('10min')) if game.get('10min') > 0 else game.get('10min')}{RES}"
    colored_value_1hr = f"{RED if game.get('1hr') < 0 else GRE if game.get('1hr') > 0 else CYN}{' ' + str(game.get('1hr')) if game.get('1hr') > 0 else game.get('1hr')}{RES}"
    colored_value_3hrs = f"{RED if game.get('3hrs') < 0 else GRE if game.get('3hrs') > 0 else CYN}{' ' + str(game.get('3hrs')) if game.get('3hrs') > 0 else game.get('3hrs')}{RES}"
    colored_value_6hrs = f"{RED if game.get('6hrs') < 0 else GRE if game.get('6hrs') > 0 else CYN}{' ' + str(game.get('6hrs')) if game.get('6hrs') > 0 else game.get('6hrs')}{RES}"
    percent = f"{LGRY}%{RES}"
    # bet_str = f"{BLNK if game.get('bet_lvl') != 'Low' else ''}💰 {BLU if game.get('bet_lvl') in [ 'Mid', 'Low' ] else BLYEL if game.get('bet_lvl') == 'Bonus' else BGRE}{game.get('bet_lvl').upper()}{RES} "
    
    print(
        f"\n\t{tag} {BMAG}{clean_name} {RES}{DGRY}→ {signal} "
        f"{RED if not game.get('up') else GRE}{game.get('value')}{RES}{percent} "
        f"({helpslot_signal} {RED if game.get('meter_color') == 'red' else GRE}{game.get('jackpot_value')}{RES}{percent} {DGRY}Helpslot{RES})"
    )
    print(f"\t\t{CYN}⏱{RES} {LYEL}10m{RES}:{colored_value_10m}{percent}  {CYN}⏱{RES} {LYEL}1h{RES}:{colored_value_1h}{percent}  {CYN}⏱{RES} {LYEL}3h{RES}:{colored_value_3h}{percent}  {CYN}⏱{RES} {LYEL}6h{RES}:{colored_value_6h}{percent}")
    print(f"\t\t{CYN}⏱{RES} {LYEL}10m{RES}:{colored_value_10min}{percent}  {CYN}⏱{RES} {LYEL}1h{RES}:{colored_value_1hr}{percent}  {CYN}⏱{RES} {LYEL}3h{RES}:{colored_value_3hrs}{percent}  {CYN}⏱{RES} {LYEL}6h{RES}:{colored_value_6hrs}{percent} {DGRY}Helpslot{RES})")
    
    # alert_queue.put(clean_name) if state.game_name is None else None
        
def countdown_timer(seconds: int = 10):
    while not stop_event.is_set():
        now_time = time.time()
        current_sec = int(now_time) % seconds
        time_left = seconds - current_sec
        
        blink = BLNK if current_sec % 2 == 0 else ""

        timer = (
            f"\t⏳ Spinning In: "
            f"{BYEL}{time_left // seconds:02d}{BWHTE}{blink}:{RES}"
            f"{BLYEL}{time_left:02d}{RES}  "
            # f"( {LGRY}{re.sub(r'\\s*\\(.*?\\)', '', game)}{RES} "
            f"{DGRY}| {PROVIDERS.get(provider).color}{provider}{RES} )"
        )
        
        sys.stdout.write(f"\r{timer}")
        sys.stdout.flush()
        
        # print(f"\n\tjackpot_value --> {state.jackpot_value}")
        # print(f"\tmeter_color --> {state.meter_color}")
        # print(f"\t10m --> {state.min10 {state.m10}}")
        # print(f"\t1h --> {state.hr1} {state.h1}")
        # print(f"\t3h --> {state.hr3} {state.h3}")
        # print(f"\t6h --> {state.hr6} {state.h6}")
        if current_sec % 10 == 9:
            if state.trending or state.manual_select:
                threading.Thread(target=spin, args=(False, False,), daemon=True)
                chosen_spin = spin(False, False)
                if chosen_spin == "normal_spin" and random.random() < 0.1:
                    spin(*random.choice([(True, False), (False, True)]))
                # if chosen_spin == "normal_spin" and state.bet_lvl in [ "Bonus", "High" ] and random.random() < 0.5:
                #     spin(*random.choice([(True, False), (False, True)]))
                # if chosen_spin in [ "combo_spin", "spam_spin", "turbo_spin" ]:
                #     time.sleep(random.uniform(*SPIN_DELAY_RANGE))
        # else: # THIS IS TEST                
        #     if state.trending and state.bet_lvl in [ "Bonus", "High" ] and random.random() < 0.1:
        #     # if current_sec % 10 == 3 and current_sec % 10 != 9 and random.random() < 0.1:
        #         # if state.trending and state.bet_lvl in [ "Bonus", "High" ]:
        #         threading.Thread(target=spin, args=(False, False,), daemon=True)
        #         chosen_spin = spin(False, False)
        #         if chosen_spin in [ "combo_spin", "spam_spin", "turbo_spin" ]:
        #             time.sleep(random.uniform(*SPIN_DELAY_RANGE))
        #     else:
        #         if current_sec % 10 == 3 and state.game_name is not None:
        #             alert_queue.put((f"{state.game_name} {f"trending {state.bet_lvl}" if state.trending else 'no longer trending'}"))
                
            # if current_sec % 10 == 0 and state.game_name is not None:
            #     alert_queue.put((f"{state.game_name} {"trending" if state.trending else 'no longer trending'}"))
            # if state.game_name is not None:
            #     alert_queue.put((f"{state.game_name} {"trending" if state.trending else 'not trending'}"))

                # chosen_spin = spin(False, False)
                # if chosen_spin == "normal_spin":
                #     if random.random() < 0.1:
                #         spin(*random.choice([(True, False), (False, True)]))
            
        next_sec = math.ceil(now_time)
        sleep_time = max(0, next_sec - time.time())
        time.sleep(sleep_time)

def start_listeners(stop_event):
    with KeyboardListener(on_press=on_key_press) as kb_listener:
        while not stop_event.is_set():
            kb_listener.join(0.1)
            

if __name__ == "__main__":
    state = AutoState()
    stop_event = threading.Event()
    spin_in_progress = threading.Event()
    
    alert_queue = ThQueue()
    
    alert_thread = threading.Thread(target=play_alert, args=(alert_queue, stop_event,), daemon=True)
    kb_thread = threading.Thread(target=start_listeners, args=(stop_event,), daemon=True)
    countdown_thread = threading.Thread(target=countdown_timer, daemon=True)

    alert_thread.start()
    
    print(f"{CLEAR}", end="")
    print(render_providers())
    provider, provider_name = providers_list()
    alert_queue.put(provider_name)
    spin_btn = True if "FC" in provider else False
    user_input = input(f"\tDo you want to enable {CYN}Wide Screen{RES} ❓ ({DGRY}y/N{RES}): \n").strip().lower()
    widescreen = user_input in ("y", "yes")
    
    CENTER_X, CENTER_Y = SCREEN_POS.get("center_x"), SCREEN_POS.get("center_y")
    LEFT_X, RIGHT_X, TOP_Y, BTM_Y = 0, SCREEN_POS.get("right_x"), 0, SCREEN_POS.get("bottom_y")
    
    kb_thread.start()
    countdown_thread.start()
    
    games = []
    prev_games = []
    selected_game = None
    url = next((url for url in URLS if 'helpslot' in url), None)
    
    try:
        while not stop_event.is_set():
            # games = sorted(load_trend_memory().keys(), key=str.lower)            
            games = list(load_trend_memory().keys())
            if not games:
                state.manual_select = True # should not run trend.py
            # Detect new game list
            if games != prev_games and not state.trending:
                prev_games = games.copy()
                # state.trending = False
                selected_game = None  # reset selection
                
                if games and state.game_name is None:
                    print(f"\n\n\tPress number [{WHTE}1-{len(games)}{RES}] to integrate game data:\n")
                    for i, game in enumerate(games, start=1):
                        if "Wild Ape" in game:
                            game = game.replace("#3258", "").strip()
                        print(f"\t[{WHTE}{i}{RES}] - {PROVIDERS.get(provider).color}{game.title()}{RES}")
                    print("\n")

            if selected_game:
                if selected_game in games:
                    state.game_name = selected_game
                    game = load_trend_memory()
                    # state.jackpot_value = game.get('jackpot_value')
                    # state.meter_color = game.get('meter_color')
                    state.min10 = game.get('min10')
                    # state.hr1 = game.get('hr1')
                    # state.hr3 = game.get('hr3')
                    # state.hr6 = game.get('hr6')
                    state.m10 = game.get('10min')
                    state.h1 = game.get('1hr')
                    state.h3 = game.get('3hrs')
                    state.h6 = game.get('6hrs')
                    # state.trending = game.get(state.game_name)["trending"]
                    state.bet_lvl = game.get(state.game_name)["bet_lvl"]
                    state.game_name = selected_game
                    state.trending = True
                else:
                    state.game_name = None
                    state.trending = False
                    
                # with ThreadPoolExecutor(max_workers=2) as executor:
                #     future1 = executor.submit(integrate_game, selected_game, url, provider)
                #     future2 = executor.submit(search_game_data_from_local_api, selected_game)
                #     wait([future1, future2])

                # helpslot_data = future1.result() or {}
                # api_data = future2.result() or {}

                # # Flatten helpslot_data['data'] if it exists
                # helpslot_list = helpslot_data.get('data', []) if isinstance(helpslot_data, dict) else helpslot_data
                # print('helpslot_list 1: ', helpslot_list)
                # helpslot_list = helpslot_list if isinstance(helpslot_list, list) else [helpslot_list]
                # print('helpslot_list 2: ', helpslot_list)
                
                # api_list = api_data if isinstance(api_data, list) else [api_data]

                # # Build dict for API data keyed by name
                # api_dict = {d["name"]: d for d in api_list if isinstance(d, dict) and "name" in d}
                # print('api_dict: ', api_dict)

                # # Merge helpslot + api
                # combined_games = []
                # for g in helpslot_list:
                #     name = g.get("name")
                #     if not name:
                #         continue
                #     merged = {**api_dict.get(name, {}), **g}  # helpslot overrides api
                #     combined_games.append(merged)

                # # Filter only entries with 'name'
                # combined_games = [g for g in combined_games if g.get("name")]
                # print('Combined: ', combined_games)
                # log_data(combined_games[0])
                
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n\n\t🤖❌  {BLRED}Main program interrupted.{RES}")
        stop_event.set()
    finally:
        print(f"\n\n\t🤖❌  {LYEL}All threads shut down...{RES}")
        