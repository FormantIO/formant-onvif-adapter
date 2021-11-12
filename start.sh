#!/usr/bin/env bash

# Ensure all prints make it to the journal log
export PYTHONUNBUFFERED=true

# Start the onvif ptz adapter
bash -c "python3 main.py"