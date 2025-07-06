#!/bin/bash

# Determine path inside bundle
APP_DIR="$(dirname "$0")"

# Launch API Service in Terminal
open -a Terminal "$APP_DIR/Scatter Slot API Service"

# Launch Monitor in Terminal
open -a Terminal "$APP_DIR/Scatter Slot Monitor"
