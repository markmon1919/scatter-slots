#!/bin/bash

cd "$(dirname "$0")" || exit 1
.venv/bin/uvicorn data:app --host 0.0.0.0 --port 7777 --reload
