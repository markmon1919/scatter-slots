import os, platform, time, threading, random, pyautogui
from pynput.keyboard import Listener as KeyboardListener, Key, KeyCode
from pynput.mouse import Listener as MouseListener, Button
from dataclasses import dataclass


@dataclass
class GameSettings:
    turbo_speeds: dict
    auto_play_menu: bool = False
    hotkeys: dict = None

settings = GameSettings(
    turbo_speeds={
        'q': 0.05,  # 20 cps
        'w': 0.02,  # 50 cps
        'e': 0.01,  # 100 cps
        'a': 0.005, # 200 cps
        's': 0.003, # 300 cps
        'd': 0.001  # 400 cps
    },
    hotkeys={
        'spin': KeyCode.from_char('z'),
        'turbo': KeyCode.from_char('x'),
        'auto': KeyCode.from_char('c'),
    }
)

# States
clicking = False
pressing = False
current_key = None
move = False
auto_play = False

screen_width, screen_height = pyautogui.size()
center_x, center_y = screen_width // 2, screen_height // 2


def keyboard():
    global pressing, current_key, move

    while True:
        if pressing and current_key:
            if current_key == 'd':
                pyautogui.doubleClick()
            else:
                if not move:
                    pyautogui.click()
                else:
                    set_location(current_key)

            sleep_time = (
                settings.turbo_speeds.get(current_key, 0.05)
                if not settings.auto_play_menu
                else 0.01
            )
            time.sleep(sleep_time)
        else:
            time.sleep(0.01)

def mouse():
    # global clicking, auto_play

    while True:
        if clicking and auto_play:
            print("[ MOUSE ] Mouse clicked")
            auto_play = False
        time.sleep(0.02)

def on_key_press(key):
    global clicking, pressing, current_key, auto_play, move

    if key == Key.esc:
        os._exit(0)  # Clean exit

    if hasattr(key, 'char'):
        char = key.char.lower()
        if char in settings.turbo_speeds:
            pressing = True
            current_key = char
        elif char == 'm':  # toggle move mode
            move = not move
        elif char == 'p':  # toggle auto-play
            auto_play = not auto_play

def on_key_release(key):
    global pressing, current_key
    
    if hasattr(key, 'char') and key.char.lower() == current_key:
        pressing = False
        current_key = None

def on_click(x, y, button, pressed):
    global clicking

    if button == Button.left:
        clicking = pressed

def set_location(key_char):
    x = center_x + (50 if key_char == 'l' else -50)
    y = center_y
    pyautogui.moveTo(x, y)
    pyautogui.click()

def start_listeners():
    kb_thread = threading.Thread(target=keyboard, daemon=True)
    mouse_thread.Thread(target=mouse, daemon=True)
    kb_thread.start()
    mouse_thread.start()

    try:
        with KeyboardListener(on_press=on_key_press, on_release=on_key_release) as kb_listener, \
             MouseListener(on_click=on_click) as mouse_listener:
            kb_listener.join()
            mouse_listener.join()
    except KeyboardInterrupt:
        print("\n\n[!] Program interrupted by user. Exiting cleanly...\n")


if __name__ == "__main__":
    os.system('cls' if platform.system() == "Windows" else 'clear')

    print("\n\n>>> Scatter Spammer by: MMM <<<\n")
    print("\n>>> Select Game <<<\n")
    start_listeners()

