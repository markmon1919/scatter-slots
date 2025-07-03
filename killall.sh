#!/bin/bash

if [[ -z "$1" ]]; then
    ps aux | grep '[p]ython' | awk '{print $2}' | xargs kill -9
else
    ps aux | grep '[p]ython' | awk '{print $2}' | grep -v "$1" | xargs kill -9
fi
