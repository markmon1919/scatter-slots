#!/bin/bash

cd "$(dirname "$0")" || exit 1
.venv/bin/uvicorn old_data:app --host 0.0.0.0 --port 8081 --reload
