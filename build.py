#!/usr/bin/env .venv/bin/python

import subprocess

compile_api = [
    'pyinstaller',
    '--onefile',
    '--clean',
    '--noconfirm',
    # '--windowed',
    '--icon=monitor.ico',
    '--name', 'Scatter Slot API Service',
    'api.py'
]

compile_app = [
    'pyinstaller',
    '--onefile',
    '--clean',
    '--noconfirm',
    # '--windowed',
    '--icon=slot.ico',
    '--name', 'Scatter Slot Monitor',
    'monitor.py'
]

subprocess.run(compile_api)
subprocess.run(compile_app)

# Execute Application
# print('\nStarting Scatter Slot Monitor...')

# try:
#     subprocess.run(["./monitor.py"], check=True)
# except (FileNotFoundError):
#     print(f"python3 not found, trying with 'python'...")
#     subprocess.run(["venv/bin/python3", "monitor.py"], check=True)
