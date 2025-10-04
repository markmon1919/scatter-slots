#!/usr/bin/env bash

# Start all 3 chart scripts in background using nohup
nohup ./min10_chart.py 2>&1 &
nohup ./delta_chart.py 2>&1 &
nohup ./jackpot_chart.py 2>&1 &

echo "📊 All 3 chart scripts started."
