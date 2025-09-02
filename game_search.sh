#!/bin/bash

cd "$(dirname "$0")" || exit 1
.venv/bin/uvicorn service:app --host 0.0.0.0 --port 8080 --reload
