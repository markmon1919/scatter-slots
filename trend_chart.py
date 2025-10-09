import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import numpy as np

# ── Configuration ──
WINDOW = 50
MIN10_STD_FACTOR = 1.5
PULL_STD_FACTOR = 1.5
PRE_ALERT_FACTOR = 0.8

# ── Rolling data storage ──
min10_values = deque(maxlen=WINDOW)
pull_values = deque(maxlen=WINDOW)
timestamps = deque(maxlen=WINDOW)

# simulate state updates
class State:
    def __init__(self, min10, pull_delta):
        self.min10 = min10
        self.pull_delta = pull_delta

# ── Example: append new state tick (replace with real WebSocket data)
def append_state(state):
    min10_values.append(state.min10)
    pull_values.append(state.pull_delta)
    timestamps.append(len(timestamps))  # simple index for x-axis

# ── Real-time plotting ──
fig, ax = plt.subplots(figsize=(10,5))

def animate(i):
    if not min10_values: 
        return

    ax.clear()
    min10_array = np.array(min10_values)
    pull_array = np.array(pull_values)

    # dynamic thresholds
    min10_thresh = np.mean(np.abs(min10_array)) + MIN10_STD_FACTOR*np.std(np.abs(min10_array))
    pull_thresh = np.mean(np.abs(pull_array)) + PULL_STD_FACTOR*np.std(np.abs(pull_array))

    # pre-alert thresholds
    min10_pre = PRE_ALERT_FACTOR * min10_thresh
    pull_pre = PRE_ALERT_FACTOR * pull_thresh

    # plot actual values
    ax.plot(timestamps, min10_array, label='min10', color='blue', marker='o')
    ax.plot(timestamps, pull_array, label='pull_delta', color='green', marker='x')

    # plot dynamic thresholds
    ax.axhline(min10_thresh, color='blue', linestyle='--', label='min10 threshold')
    ax.axhline(pull_thresh, color='green', linestyle='--', label='pull threshold')

    # plot pre-alert levels
    ax.axhline(min10_pre, color='blue', linestyle=':', label='min10 pre-alert')
    ax.axhline(pull_pre, color='green', linestyle=':', label='pull pre-alert')

    ax.set_xlabel('Ticks')
    ax.set_ylabel('Values')
    ax.set_title('Real-Time min10 & pull_delta with Dynamic Thresholds')
    ax.legend(loc='upper right')
    ax.grid(True)

ani = animation.FuncAnimation(fig, animate, interval=1000)
plt.show()

# ── Example usage ──
# In your WebSocket loop:
# append_state(State(min10=current_min10, pull_delta=current_pull_delta))
