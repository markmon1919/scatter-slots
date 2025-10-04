#!/usr/bin/env bash

# Kill all Python chart scripts
pkill -f min10_chart.py
pkill -f delta_chart.py
pkill -f jackpot_chart.py

echo "🛑 All 3 chart scripts stopped."