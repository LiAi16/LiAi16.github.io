#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
python -m pip install -r requirements.txt
python run_experiments.py
python backend/app.py
