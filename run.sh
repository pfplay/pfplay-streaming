#!/bin/bash

export PYTHONPATH="/home/pfplay/backend/pfplay-streaming"
export PATH="$PATH:${PYTHONPATH}"
nohup uvicorn app:app --reload --port 9000 --host=0.0.0.0 --workers=4 &
echo "streaming api start"
