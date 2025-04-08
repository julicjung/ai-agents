#!/bin/bash
# Add src directory to PYTHONPATH when running from workspace root
export PYTHONPATH="$PWD/src"
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --app-dir src