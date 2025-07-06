#!/bin/bash

cd "$(dirname "$0")" || exit 1
rm -rf ./build ./dist *.spec ./__pycache__
.venv/bin/python3 ./build.py
.venv/bin/python3 ./build_app.py
