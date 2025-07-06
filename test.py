import time
import pyautogui
import threading
import keyboard
from pynput import mouse
from dataclasses import dataclass

# Disable PyAutoGUI failsafe and delays
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

@dataclass
class AutoState:
    pressing: bool = False
    current_key: str = None
    position: tuple = (0, 0)
    locations: dict = {}
    game: str = None
    spin: bool = False
    auto_spin: bool = False
    turbo: bool = False
    feature: bool = False
    auto_play_menu: bool = False
    running: bool = True
    enabled: bool = True  # For hotkey toggle

@dataclass
class GameSettings:
    sleep_times: dict

def get_sleep_times(auto_play_menu):
    return {
        'q': 0.05, 'w': 0.02, 'e': 0.01, 'a': 0.005, 's': 0.003, 'd': 0.001
    } if not auto_play_menu else {
        'a': 0.005, 's': 0.003, 'd': 0.001
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

def set_location(key):
    if key in state.locations:
        x, y = pyautogui.position()
        state.locations[key] = (x, y)
        print(f"Set {key} location to: {x}, {y}")

def on_click(x, y, button, pressed):
    if pressed:
        set_location(state.current_key)
        return False

def wait_for_mouse_click():
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()

def click_loop(settings):
    while state.running:
        if state.enabled and state.pressing and state.current_key in settings.sleep_times:
            location = state.locations.get(state.current_key)
            if location:
                pyautogui.click(location)
                time.sleep(settings.sleep_times[state.current_key])
        time.sleep(0.01)

def keyboard_listener(settings):
    print("Press ESC to exit.")
    print("Hold Q/W/E/A/S/D to click. Press once to set location via mouse.")
    print("Press CTRL+SHIFT to toggle automation on/off.")

    while state.running:
        if keyboard.is_pressed('esc'):
            state.running = False
            break

        if keyboard.is_pressed('ctrl') and keyboard.is_pressed('shift'):
            state.enabled = not state.enabled
            print(f"Automation {'enabled' if state.enabled else 'disabled'}.")
            time.sleep(0.5)  # Debounce

        for key in settings.sleep_times.keys():
            if keyboard.is_pressed(key):
                if state.current_key != key:
                    state.current_key = key
                    print(f"Key {key} pressed. Click mouse to set position.")
                    wait_for_mouse_click()
                state.pressing = True
            elif state.current_key == key:
                state.pressing = False
                state.current_key = None

        time.sleep(0.01)

if __name__ == '__main__':
    print("Select a game:")
    games = [
        "Fortune Goddess",
        "Lucky Fortunes",
        "Fruity Bonanza",
        "Golden Empire",
        "Pragmatic Play"
    ]

    for i, g in enumerate(games):
        print(f"{i + 1}. {g}")

    while True:
        try:
            choice = int(input("Enter game number: "))
            if 1 <= choice <= len(games):
                break
            else:
                print("Invalid choice. Try again.")
        except ValueError:
            print("Please enter a valid number.")

    state = AutoState()
    settings = configure_game(games[choice - 1])

    threading.Thread(target=click_loop, args=(settings,), daemon=True).start()
    keyboard_listener(settings)
