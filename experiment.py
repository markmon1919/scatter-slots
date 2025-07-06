import time
import pyautogui
import threading
from pynput import mouse, keyboard as pynput_keyboard
from dataclasses import dataclass, field

# Disable PyAutoGUI failsafe and delays
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

@dataclass
class AutoState:
    pressing: bool = False
    current_key: str = None
    position: tuple = (0, 0)
    locations: dict = field(default_factory=dict)
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

    pressed_keys = set()

    def on_press(key):
        nonlocal pressed_keys

        if key == pynput_keyboard.Key.esc:
            state.running = False
            return False

        if key == pynput_keyboard.Key.ctrl_l or key == pynput_keyboard.Key.ctrl_r:
            pressed_keys.add('ctrl')
        if key == pynput_keyboard.Key.shift:
            pressed_keys.add('shift')

        if 'ctrl' in pressed_keys and 'shift' in pressed_keys:
            state.enabled = not state.enabled
            print(f"Automation {'enabled' if state.enabled else 'disabled'}.")
            time.sleep(0.5)
            pressed_keys.clear()
            return

        if hasattr(key, 'char') and key.char in settings.sleep_times:
            if state.current_key != key.char:
                state.current_key = key.char
                print(f"Key {key.char} pressed. Click mouse to set position.")
                wait_for_mouse_click()
            state.pressing = True

    def on_release(key):
        nonlocal pressed_keys

        if hasattr(key, 'char') and key.char == state.current_key:
            state.pressing = False
            state.current_key = None

        if key == pynput_keyboard.Key.ctrl_l or key == pynput_keyboard.Key.ctrl_r:
            pressed_keys.discard('ctrl')
        if key == pynput_keyboard.Key.shift:
            pressed_keys.discard('shift')

    with pynput_keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

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
