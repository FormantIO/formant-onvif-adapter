#!/usr/bin/env bash

# Check for the setup lock
FILENAME="setup.lock"
 
if [ ! -f "$FILENAME" ]
then
  echo "$FILENAME not found - running setup..."
  ./setup.sh
fi 

# Ensure all prints make it to the journal log
export PYTHONUNBUFFERED=true

# Start the onvif ptz adapter
bash -c "python3 main.py"