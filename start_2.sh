#!/bin/bash

xvfb-run -a --server-args='-screen 0 1024x768x24 -nolisten tcp -ac' python vps.py