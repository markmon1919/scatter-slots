#!/bin/bash

declare -a PIDS=(``)

PIDS+=(`ps aux | grep "'[p]ython'\|uvicorn\|selenium\|webdriver" | grep -v grep | awk '{print $2}'`)
port_pid=(`lsof -i :8080 | awk '{print$2}' | tail -n +2`)

if [[ -n "$port_pid" ]]; then
    PIDS+=("$port_pid")
fi

# Check if list is empty
if [[ ${#PIDS[@]} -eq 0 ]]; then
    echo "No processes found."
    exit 0
fi

# Kill the processes
for pid in "${PIDS[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
        kill -9 "$pid"
        echo "Killing Process: $pid"
    else
        echo "PID $pid does not exist or already terminated."
    fi
done


# if [[ -z "$1" ]]; then
#     ps aux | grep '[p]ython' | awk '{print $2}' | xargs kill -9
# else
#     ps aux | grep '[p]ython' | awk '{print $2}' | grep -v "$1" | xargs kill -9
# fi