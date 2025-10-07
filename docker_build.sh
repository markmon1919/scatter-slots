#!/usr/bin/env bash

docker stop ${API_CONTAINER} >> /dev/null 2<&1
docker rm ${API_CONTAINER} >> /dev/null 2<&1

# Load environment variables from config.py
export $(grep -E '^API_CONTAINER|^API_PORT|^LOG' config.py | tr -d " " | xargs)

# Detect OS
OS_TYPE=$(uname)

if [[ "$OS_TYPE" == "Darwin" ]]; then
    # macOS
    router_interface=$(netstat -rn | grep '^default' | awk '{print $NF}')
    export API_HOST_IP=$(ipconfig getifaddr "$router_interface")
elif [[ "$OS_TYPE" == "Linux" ]]; then
    # Linux
    router_interface=$(ip route | grep '^default' | awk '{print $5}' | head -n1)
    export API_HOST_IP=$(ip -o -4 addr list "$router_interface" | awk '{print $4}' | cut -d/ -f1)
else
    echo "Unsupported OS: $OS_TYPE"
    exit 1
fi

# Build and run docker-compose
docker-compose up -d --build
