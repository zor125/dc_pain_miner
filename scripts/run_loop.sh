#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

source .venv/bin/activate

while true; do
  python -m src.pipeline
  sleep 180
done
