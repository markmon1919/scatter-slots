#!/bin/bash

API_PID=$(ps aux | grep uvicorn | grep -v grep | awk '{print $2}')
kill -9 $(($API_PID))
