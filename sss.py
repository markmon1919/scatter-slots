#!/usr/bin/env python

import os, platform, time, threading, random, pyautogui, subprocess
from queue import Queue as ThQueue, Empty
from pynput.keyboard import Listener as KeyboardListener, Key, KeyCode
from pynput.mouse import Listener as MouseListener, Button
from dataclasses import dataclass
from config import VOICES


@dataclass
class AutoState:
    game: str = None
    pressing: bool = False
    clicking: bool = False
    current_key: str = None
    move: bool = False
    auto_play: bool = False
    spin: bool = False
    auto_spin: bool = False
    turbo: bool = False
    feature: bool = False
    running: bool = True
    auto_play_menu: bool = False
    enabled: bool = True  # For hotkey toggle
    
@dataclass
class GameSettings:
    sleep_times: dict

def get_sleep_times(auto_play_menu):
    return {
        'q': 0.05,  # 20 cps
        'w': 0.02,  # 50 cps
        'e': 0.01,  # 100 cps
        'a': 0.005, # 200 cps
        's': 0.003, # 300 cps
        'd': 0.001,  # 400 cps
    } if not auto_play_menu else {
        'a': 0.005, # 200 cps
        's': 0.003, # 300 cps
        'd': 0.001  # 400 cps
    }

def configure_game(name):
    state.game = name
    config = {
        "Fortune Goddess": (True, True, True, True, False),
        "Lucky Fortunes": (True, True, True, True, False),
        "Fruity Bonanza": (True, True, True, True, False),
        "Golden Empire": (False, True, True, True, False),
        "Pragmatic Play": (False, True, True, True, True),
    }.get(name, (False, False, False, False, False))

    state.spin, state.auto_spin, state.turbo, state.feature, state.auto_play_menu = config
    return GameSettings(get_sleep_times(state.auto_play_menu))

# Screen center
screen_width, screen_height = pyautogui.size()
center_x = screen_width // 2
center_y = screen_height // 2

def keyboard(settings):
    while state.running:
        if state.enabled and state.pressing and state.current_key: #in settings.sleep_times:
            if state.current_key == 'd':
                pyautogui.doubleClick()
            else:
                if not state.move:
                    pyautogui.click()
                else:
                    set_location(state.current_key)

            time.sleep(settings.sleep_times.get(state.current_key, 0.001))
        else:
            time.sleep(0.001)

# def keyboard():
#     sleep_times = {
#         'q': 0.05,  # 20 cps
#         'w': 0.02,  # 50 cps
#         'e': 0.01,  # 100 cps
#         'a': 0.005, # 200 cps
#         's': 0.003, # 300 cps
#         'd': 0.001  # 400 cps
#     } if not auto_play_menu else {
#         'a': 0.005, # 200 cps
#         's': 0.003, # 300 cps
#         'd': 0.001  # 400 cps
#     }

#     while True:
#         if pressing:
#             if current_key == 'd':
#                 pyautogui.doubleClick()
#             else:
#                 pyautogui.click() if not move else set_location(current_key)

#             # sleep_time = (
#             #     alt_sleep_times.get(current_key, 0.001)
#             #     if auto_play_menu else
#             #     local_sleep_times.get(current_key, 0.001)
#             # )
#             # time.sleep(sleep_time)
#             time.sleep(sleep_times.get(current_key, 0.001))
#         else:
#             time.sleep(0.001)

# def on_key_press(key):
#     global pressing, current_key, move, auto_play

#     if key == Key.space:
#         if spin:
#             pressing = True
#             current_key = 'space'
#             num_clicks = 1
#             move = True
#         else:
#             auto_play = False

#     if isinstance(key, KeyCode):
#         if key.char in [ 'q', 'w', 'e', 'a', 's', 'd' ]:
#             pressing = True
#             current_key = key.char
#             move = True if key.char not in [ 'a', 's', 'd' ] and turbo else False
#             if not auto_play_menu:
#                 num_clicks = { 'q': 20, 'w': 50, 'e': 100, 'a': 200, 's': 300, 'd': 400 }[ key.char ]
#                 auto_play = False
#             else:
#                 num_clicks = { 'q': 1, 'w': 1, 'e': 1, 'a': 200, 's': 300, 'd': 400 }[ key.char ]
#                 auto_play = False if key.char in [ 'a', 's', 'd' ] and turbo else auto_play
#         else:
#             pressing = True
#             current_key = key.char
#             num_clicks = 1
#             if key.char == 'r':
#                 move = True
#                 auto_play = False
#             elif key.char == 'v' and auto_spin:
#                 move = True
#                 auto_play = False
#             # elif key.char in [ '1', '2', '3' ] and turbo is True:
#             #     move = True
#             elif key.char == 'f' and feature:
#                 move = True
#                 auto_play = False
#             else:
#                 auto_play = False
#     elif key in [ Key.tab, Key.shift ]:
#         pressing = True
#         current_key = 'tab' if key == Key.tab else 'shift'
#         num_clicks = 1
#         move = True
#         auto_play = False
#     else:
#         return

#     print(f"\nPressed [{current_key}] ---> {num_clicks} {'click' if num_clicks == 1 else 'clicks'}")

# def on_key_release(key):
#     global pressing, current_key, move, auto_play

#     if key == Key.space:
#         if spin:
#             pressing = False
#             current_key = 'space'
#             num_clicks = 1
#             move = False
#         else:
#             auto_play = False

#     if isinstance(key, KeyCode):
#         pressing = False
#         current_key = key.char
#         if key.char in [ 'q', 'w', 'e' ] and turbo and auto_play_menu:
#             move = False
#         elif key.char == 'r':
#             move = False
#             auto_play = False
#         elif key.char == 'v' and auto_spin:
#             move = False
#             auto_play = False
#         # elif key.char in [ '1', '2', '3' ] and turbo is True:
#         #     move = False
#         elif key.char == 'f' and feature:
#             move = False
#             auto_play = False
#         else:
#             auto_play = False
#     elif key in [ Key.tab, Key.shift ]:
#         pressing = False
#         current_key = 'tab' if key == Key.tab else 'shift'
#         move = False
#         auto_play = False
#     else:
#         return

#     print(f"\nReleased ---> [{ current_key }]")

# def set_location(moveKey):
#     # global current_key

#     # moveKey = current_key

#     x1, x2 = 0, 0
#     y1, y2 = 0, 0

#     random_x = center_x + random.randint(x1, x2)
#     random_y = center_y + random.randint(y1, y2)

#     if moveKey in [ 'r', 'u', 'i', 'o', 'p', 'j', 'k', 'l' 'm', ',', '.', '/' ]: # SLOT SCREEN
#         if game == "Fortune Goddess":
#             if moveKey == 'r':
#                 pyautogui.doubleClick(x=random_x, y=random_y)
#         elif game == "Lucky Fortunes":
#             if moveKey == 'r':
#                 pyautogui.doubleClick(x=random_x, y=random_y)
#             elif moveKey in [ 'u', 'i', 'o', 'p', 'j', 'k', 'l' 'm', ',', '.', '/' ]:
#                 pyautogui.click(x=random_x, y=random_y)
#         elif auto_play_menu:
#             if moveKey == 'r':
#                 pyautogui.moveTo(x=random_x, y=random_y)
#         else:
#             return
#     elif moveKey == 'f' and feature: # FEATURE
#         if game == "Fortune Goddess":
#             pyautogui.click(x=random_x, y=random_y + 200)
#             pyautogui.doubleClick(x=random_x, y=random_y + 315)
#         elif game == "Lucky Fortunes":
#             pyautogui.click(x=random_x, y=random_y + 200)
#             pyautogui.doubleClick(x=random_x, y=random_y + 380)
#         elif auto_play_menu:
#             pyautogui.doubleClick(x=random_x - 600, y=random_y - 70)
#     elif moveKey == 'v' and auto_spin: # AUTO SPIN
#         if game == "Fortune Goddess":
#             pyautogui.click(x=random_x - 150, y=random_y + 290)
#             pyautogui.doubleClick(x=random_x, y=random_y + 315)
#         elif game == "Lucky Fortunes":
#             pyautogui.click(x=random_x - 150, y=random_y + 365)
#             pyautogui.doubleClick(x=random_x, y=random_y + 380)
#         elif auto_play_menu:
#             pyautogui.click(x=random_x + 445, y=random_y + 455)
#             pyautogui.click(x=random_x, y=random_y + 180)
#     elif moveKey == 'space' and spin: # SPIN BUTTON
#         if game == "Fortune Goddess":
#             pyautogui.moveTo(x=random_x, y=random_y + 315)
#         elif game == "Lucky Fortunes":
#             pyautogui.moveTo(x=random_x, y=random_y + 380)
#     elif moveKey in [ 'tab', 'shift', 'q', 'w', 'e', 'a' ] and turbo: # TURBO BUTTON
#         if game == "Fortune Goddess":
#             if moveKey == 'tab':
#                 pyautogui.doubleClick(x=random_x - 210, y=random_y + 350)
#             elif moveKey == 'shift':
#                 pyautogui.click(x=random_x - 210, y=random_y + 350)
#             else:
#                 pyautogui.click(x=random_x - 210, y=random_y + 350)
#         elif game == "Lucky Fortunes":
#             if moveKey == 'tab':
#                 pyautogui.doubleClick(x=random_x - 210, y=random_y + 415)
#             elif moveKey == 'shift':
#                 pyautogui.click(x=random_x - 210, y=random_y + 415)
#             else:
#                 pyautogui.click(x=random_x - 210, y=random_y + 415)
#         elif auto_play_menu:
#             global auto_play

#             if not auto_play:
#                 pyautogui.click(x=random_x + 445, y=random_y + 455)
#                 auto_play = True

#             if moveKey == 'q':
#                 pyautogui.click(x=random_x - 250, y=random_y - 120)
#             elif moveKey == 'w':
#                 pyautogui.click(x=random_x - 60, y=random_y - 120)
#             elif moveKey == 'e':
#                 pyautogui.click(x=random_x + 150, y=random_y - 120)

#             pyautogui.moveTo(x=random_x, y=random_y + 180)

# def mouse_click(x, y, button, pressed):
#     if button == Button.left:
#         if pressed:
#             clicking_event.set()
#         else:
#             clicking_event.clear()

# def mouse():
#     global clicking, auto_play
#     while True:
#         if clicking and auto_play:
#             print("[ MOUSE ] Mouse clicked")
#             auto_play = False
#         time.sleep(0.02)

# def on_click(x, y, button, pressed):
#     global clicking

#     if button == Button.left:
#         clicking = pressed

def on_key_press(key):
    if key == Key.esc:
        state.running = False
        os._exit(0)

    if key == Key.right:
        print("Turbo: ON")
        pyautogui.PAUSE = 0
        pyautogui.FAILSAFE = False
    elif key == Key.left:
        print("Normal Speed: ON")
        pyautogui.PAUSE = 0.1
        pyautogui.FAILSAFE = True

    if key == Key.space:
        if state.spin:
            state.pressing = True
            state.current_key = 'space'
            num_clicks = 1
            state.move = True
        else:
            state.auto_play = False

    if isinstance(key, KeyCode):
        if key.char in [ 'q', 'w', 'e', 'a', 's', 'd' ]:
            state.pressing = True
            state.current_key = key.char
            state.move = True if key.char not in [ 'a', 's', 'd' ] and state.turbo else False
            if not state.auto_play_menu:
                num_clicks = { 'q': 20, 'w': 50, 'e': 100, 'a': 200, 's': 300, 'd': 400 }[ key.char ]
                state.auto_play = False
            else:
                num_clicks = { 'q': 1, 'w': 1, 'e': 1, 'a': 200, 's': 300, 'd': 400 }[ key.char ]
                state.auto_play = False if key.char in [ 'a', 's', 'd' ] and state.turbo else state.auto_play
        else:
            state.pressing = True
            state.current_key = key.char
            num_clicks = 1
            if key.char == 'r':
                state.move = True
                state.auto_play = False
            elif key.char == 'v' and state.auto_spin:
                state.move = True
                state.auto_play = False
            # elif key.char in [ '1', '2', '3' ] and turbo is True:
            #     move = True
            elif key.char == 'f' and state.feature:
                state.move = True
                state.auto_play = False
            else:
                state.auto_play = False
    elif key in [ Key.tab, Key.shift ]:
        state.pressing = True
        state.current_key = 'tab' if key == Key.tab else 'shift'
        num_clicks = 1
        state.move = True
        state.auto_play = False
    else:
        return

    print(f"\nPressed [{ state.current_key }] ---> { num_clicks } {'click' if num_clicks == 1 else 'clicks'}")

def on_key_release(key):
    if key == Key.space:
        if state.spin:
            state.pressing = False
            state.current_key = 'space'
            num_clicks = 1
            state.move = False
        else:
            state.auto_play = False

    if isinstance(key, KeyCode):
        state.pressing = False
        state.current_key = key.char
        if key.char in [ 'q', 'w', 'e' ] and state.turbo and state.auto_play_menu:
            state.move = False
        elif key.char == 'r':
            state.move = False
            state.auto_play = False
        elif key.char == 'v' and state.auto_spin:
            state.move = False
            state.auto_play = False
        # elif key.char in [ '1', '2', '3' ] and turbo is True:
        #     move = False
        elif key.char == 'f' and state.feature:
            state.move = False
            state.auto_play = False
        else:
            state.auto_play = False
    elif key in [ Key.tab, Key.shift ]:
        state.pressing = False
        state.current_key = 'tab' if key == Key.tab else 'shift'
        state.move = False
        state.auto_play = False
    else:
        return

    print(f"\nReleased ---> [{ state.current_key }]")

def set_location(key):
    x1, x2 = 0, 0
    y1, y2 = 0, 0

    random_x = center_x + random.randint(x1, x2)
    random_y = center_y + random.randint(y1, y2)

    if key in [ 'r', 'u', 'i', 'o', 'p', 'j', 'k', 'l' 'm', ',', '.', '/' ]: # SLOT SCREEN
        if state.game == "Fortune Goddess":
            if key == 'r':
                pyautogui.doubleClick(x=random_x, y=random_y)
        elif state.game == "Lucky Fortunes":
            if key == 'r':
                pyautogui.doubleClick(x=random_x, y=random_y)
            elif key in [ 'u', 'i', 'o', 'p', 'j', 'k', 'l' 'm', ',', '.', '/' ]:
                pyautogui.click(x=random_x, y=random_y)
        elif state.auto_play_menu:
            if key == 'r':
                pyautogui.moveTo(x=random_x, y=random_y)
        else:
            pyautogui.doubleClick(x=random_x, y=random_y)
    elif key == 'f' and state.feature: # FEATURE
        if state.game == "Fortune Goddess":
            pyautogui.click(x=random_x, y=random_y + 200)
            pyautogui.doubleClick(x=random_x, y=random_y + 315)
        elif state.game == "Lucky Fortunes":
            pyautogui.click(x=random_x, y=random_y + 200)
            pyautogui.doubleClick(x=random_x, y=random_y + 380)
        elif state.auto_play_menu:
            pyautogui.doubleClick(x=random_x - 600, y=random_y - 70)
    elif key == 'v' and state.auto_spin: # AUTO SPIN
        if state.game == "Fortune Goddess":
            pyautogui.click(x=random_x - 150, y=random_y + 290)
            pyautogui.doubleClick(x=random_x, y=random_y + 315)
        elif state.game == "Lucky Fortunes":
            pyautogui.click(x=random_x - 150, y=random_y + 365)
            pyautogui.doubleClick(x=random_x, y=random_y + 380)
        elif state.auto_play_menu:
            pyautogui.click(x=random_x + 445, y=random_y + 455)
            pyautogui.click(x=random_x, y=random_y + 180)
    elif key == 'space' and state.spin: # SPIN BUTTON
        if state.game == "Fortune Goddess":
            pyautogui.moveTo(x=random_x, y=random_y + 315)
        elif state.game == "Lucky Fortunes":
            pyautogui.moveTo(x=random_x, y=random_y + 380)
    elif key in [ 'tab', 'shift', 'q', 'w', 'e', 'a' ] and state.turbo: # TURBO BUTTON
        if state.game == "Fortune Goddess":
            if key == 'tab':
                pyautogui.doubleClick(x=random_x - 210, y=random_y + 350)
            elif key == 'shift':
                pyautogui.click(x=random_x - 210, y=random_y + 350)
            else:
                pyautogui.click(x=random_x - 210, y=random_y + 350)
        elif state.game == "Lucky Fortunes":
            if key == 'tab':
                pyautogui.doubleClick(x=random_x - 210, y=random_y + 415)
            elif key == 'shift':
                pyautogui.click(x=random_x - 210, y=random_y + 415)
            else:
                pyautogui.click(x=random_x - 210, y=random_y + 415)
        elif state.auto_play_menu:
            if not state.auto_play:
                pyautogui.click(x=random_x + 445, y=random_y + 455)
                state.auto_play = True

            if key == 'q':
                pyautogui.click(x=random_x - 250, y=random_y - 120)
            elif key == 'w':
                pyautogui.click(x=random_x - 60, y=random_y - 120)
            elif key == 'e':
                pyautogui.click(x=random_x + 150, y=random_y - 120)

            pyautogui.moveTo(x=random_x, y=random_y + 180)

def mouse():
    while state.running:
        if state.clicking and state.auto_play:
            print("[ MOUSE ] Mouse clicked")
            state.auto_play = False
        time.sleep(0.02)

def on_click(x, y, button, pressed):
    if button == Button.left:
        state.clicking = pressed

# def on_click(x, y, button, pressed):
#     if pressed:
#         set_location(state.current_key)
#         return False

# def wait_for_mouse_click():
#     with pynput_mouse.Listener(on_click=on_click) as listener:
#         listener.join()
#     # with pynput_keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
#     #     listener.join()

# def keyboard_listener(settings):
#     print("Press ESC to exit.")
#     print("Hold Q/W/E/A/S/D to click. Press once to set location via mouse.")
#     print("Press CTRL+SHIFT to toggle automation on/off.")

#     pressed_keys = set()

#     def on_press(key):
#         nonlocal pressed_keys

#         if key == pynput_keyboard.Key.esc:
#             state.running = False
#             return False

#         if key == pynput_keyboard.Key.ctrl_l or key == pynput_keyboard.Key.ctrl_r:
#             pressed_keys.add('ctrl')
#         if key == pynput_keyboard.Key.shift:
#             pressed_keys.add('shift')

#         if 'ctrl' in pressed_keys and 'shift' in pressed_keys:
#             state.enabled = not state.enabled
#             print(f"Automation {'enabled' if state.enabled else 'disabled'}.")
#             time.sleep(0.5)
#             pressed_keys.clear()
#             return

#         if hasattr(key, 'char') and key.char in settings.sleep_times:
#             if state.current_key != key.char:
#                 state.current_key = key.char
#                 print(f"Key {key.char} pressed. Click mouse to set position.")
#                 wait_for_mouse_click()
#             state.pressing = True

#     def on_release(key):
#         nonlocal pressed_keys

#         if hasattr(key, 'char') and key.char == state.current_key:
#             state.pressing = False
#             state.current_key = None

#         if key == pynput_keyboard.Key.ctrl_l or key == pynput_keyboard.Key.ctrl_r:
#             pressed_keys.discard('ctrl')
#         if key == pynput_keyboard.Key.shift:
#             pressed_keys.discard('shift')

#     with pynput_keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
#         listener.join()

def play_alert(alert_queue, stop_event):
    if platform.system() == "Darwin":
        while not stop_event.is_set():
            try:
                say = alert_queue.get_nowait()
                sound_file = (say)
                voice = VOICES["Samantha"]
                subprocess.run(["say", "-v", voice, "--", sound_file])
                    
            except Empty:
                time.sleep(0.05)
            except Exception as e:
                print(f"\n\t[Alert Thread Error] {e}")
    else:
        pass

def start_listeners(settings):
    # stop_event = threading.Event()
    # alert_queue = ThQueue()
    # alert_thread = threading.Thread(target=play_alert, args=(alert_queue, stop_event), daemon=True)
    # alert_thread.start()

    try:
        with KeyboardListener(on_press=on_key_press, on_release=on_key_release) as kb_listener, \
             MouseListener(on_click=on_click) as mouse_listener:
            kb_listener.join()
            mouse_listener.join()
    except KeyboardInterrupt:
        print("\n\n[!] Program interrupted by user. Exiting cleanly...\n")
        # stop_event.set()


if __name__ == "__main__":
    os.system('cls' if platform.system() == "Windows" else 'clear')

    print("\n\n>>> Scatter Spammer by: MMM <<<\n")
    print("\n>>> Select Game <<<\n")

    games = [ 
        "Fortune Goddess",
        "Lucky Fortunes",
        "Fruity Bonanza",
        "Golden Empire",
        "Pragmatic Play"
    ]

    for i, game in enumerate(games, start=1):
        print(f"{ i }. { game }")

    while True:
        try:
            choice = int(input("\nEnter the game of your choice: "))
            if 1 <= choice <= len(games):
                game = games[ choice - 1 ]
                print(f"\nSelected: { game.upper() }")
                break
            else:
                print("Invalid choice. Try again.")
        except ValueError:
            print("Please enter a valid number.")

    print("\nPress Ctrl+C to exit.\n")

    state = AutoState()
    settings = configure_game(game)

    threading.Thread(target=keyboard, args=(settings,), daemon=True).start()
    threading.Thread(target=mouse, daemon=True).start()

    start_listeners(settings)
