#!/usr/bin/env bash

docker stop ${API_CONTAINER} >> /dev/null 2<&1
docker rm ${API_CONTAINER} >> /dev/null 2<&1

router_interface=$(netstat -rn | grep '^default' | grep -v ':' | awk '{print $NF}')

export $(echo "API_HOST_IP=$(ipconfig getifaddr $router_interface)" \
  && grep -E '^API_CONTAINER|^API_PORT|^LOG' config.py | tr -d " " | xargs) \
  && docker-compose up -d --build
  