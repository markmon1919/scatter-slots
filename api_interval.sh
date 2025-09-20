#!/bin/bash

# User-Agent pool
USER_AGENTS=(
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.91 Safari/537.36"
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15"
    "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Mobile Safari/537.36"
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Mobile/15E148 Safari/604.1"
)

# RequestFrom pool
requestFroms=("H5" "H6")
rf_index=0

api_url="https://www.helpslot.win/api/games"
name="JILI CAISHEN"
manuf="JILI"

# ──────────────────────────────
# ALIGN TO NEXT 10-SECOND MARK
# ──────────────────────────────
# align_to_next_10s() {
#     now=$(date +%s)
#     next=$(( (now / 10 + 1) * 10 ))
#     wait_time=$(( next - now ))
#     echo "⏰ Waiting $wait_time seconds to align to next 10s mark..."
#     sleep "$wait_time"
# }

poll_interval=10
# min_poll=10
# max_poll=60

echo "🔄 Starting aligned polling every ~10s..."

# Initial alignment
# align_to_next_10s

last_min10=""
last_change_time=""

while true; do
    # Pick requestFrom
    requestFrom="${requestFroms[$rf_index]}"
    (( rf_index=(rf_index+1) % ${#requestFroms[@]} ))

    # Pick random user agent
    rand_index=$(( RANDOM % ${#USER_AGENTS[@]} ))
    user_agent="${USER_AGENTS[$rand_index]}"

    echo -e "\n🕓 $(date '+%H:%M:%S') | Using requestFrom=$requestFrom | UA=${user_agent:0:30}..."

    json=$(curl -sG --max-time 5 "$api_url" \
        -H "Accept: application/json" \
        -H "User-Agent: $user_agent" \
        --data-urlencode "name=$name" \
        --data-urlencode "manuf=$manuf" \
        --data-urlencode "requestFrom=$requestFrom")

    if [[ $? -ne 0 || -z "$json" ]]; then
        echo "⚠️ Curl error or empty response."
    else
        min10=$(echo "$json" | jq -r '.data[0].min10')
        if [[ "$min10" != "null" && -n "$min10" ]]; then
            if [[ "$min10" != "$last_min10" ]]; then
                now_time=$(date +%s.%3N)
                if [[ -n "$last_change_time" ]]; then
                    interval=$(echo "$now_time - $last_change_time" | bc)
                    echo -e "✅ min10 changed → $min10 (Δ ${interval}s)"
                else
                    echo "✅ First min10: $min10"
                fi
                last_min10="$min10"
                last_change_time="$now_time"
            else
                echo "→ min10 still $min10"
            fi
        else
            echo "⚠️ Invalid min10: $min10"
        fi
    fi

    # Align to next 10s boundary from now
    now=$(date +%s)
    next=$(( (now / poll_interval + 1) * poll_interval ))
    sleep_time=$(( next - now ))
    echo "🕛 Sleeping $sleep_time seconds to align with next boundary..."
    sleep "$sleep_time"
done
