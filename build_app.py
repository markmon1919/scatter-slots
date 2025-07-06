#!/usr/bin/env .venv/bin/python
# -*- coding: utf-8 -*-

import os
import shutil
import stat

# --- CONFIG ---
APP_NAME = "Scatter Slot Launcher.app"
BUNDLE_ID = "com.example.scatterlauncher"
APP_VERSION = "1.0"

MONITOR_BINARY = "Scatter Slot Monitor"
API_SCRIPT = "api.sh"
ICON_FILE = "slot.ico"   # Your icon file (must exist in your project folder)

# --- FOLDERS ---
APP_ROOT = APP_NAME
CONTENTS = os.path.join(APP_ROOT, "Contents")
MACOS = os.path.join(CONTENTS, "MacOS")
RESOURCES = os.path.join(CONTENTS, "Resources")
PLIST_PATH = os.path.join(CONTENTS, "Info.plist")

# --- CLEAN OLD APP ---
if os.path.exists(APP_ROOT):
    shutil.rmtree(APP_ROOT)

# --- MAKE FOLDERS ---
os.makedirs(MACOS, exist_ok=True)
os.makedirs(RESOURCES, exist_ok=True)

# --- INFO.PLIST ---
plist_data = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
"http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Scatter Slot Launcher</string>
    <key>CFBundleIdentifier</key>
    <string>{BUNDLE_ID}</string>
    <key>CFBundleVersion</key>
    <string>{APP_VERSION}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleExecutable</key>
    <string>start.command</string>
    <key>CFBundleIconFile</key>
    <string>{ICON_FILE}</string>
</dict>
</plist>
"""
with open(PLIST_PATH, "w") as f:
    f.write(plist_data)

# --- COPY ICON ---
if os.path.exists(ICON_FILE):
    shutil.copy(ICON_FILE, os.path.join(RESOURCES, ICON_FILE))
    print(f"✅ Copied icon: {ICON_FILE}")
else:
    print(f"⚠️  Icon not found: {ICON_FILE}")

# --- CREATE start.command ---
start_command_path = os.path.join(MACOS, "start.command")
start_command = f"""#!/bin/bash

APP_DIR="$(cd "$(dirname "$0")" && pwd)"

# Start API service in new Terminal window
open -a Terminal "{os.path.abspath(API_SCRIPT)}"

# Start monitor binary in new Terminal window
open -a Terminal "$APP_DIR/{MONITOR_BINARY}"
"""

with open(start_command_path, "w") as f:
    f.write(start_command)

# Make it executable
st = os.stat(start_command_path)
os.chmod(start_command_path, st.st_mode | stat.S_IEXEC)

# --- COPY MONITOR BINARY ---
monitor_src = os.path.join("dist", MONITOR_BINARY)
monitor_dst = os.path.join(MACOS, MONITOR_BINARY)

if os.path.exists(monitor_src):
    shutil.copy(monitor_src, monitor_dst)
    print(f"✅ Copied binary: {MONITOR_BINARY}")
else:
    print(f"❌ ERROR: Monitor binary not found at {monitor_src}")

print(f"\n🎉 Done! App created: {APP_NAME}")
print(f"👉 Double-click it in Finder to launch both services.")