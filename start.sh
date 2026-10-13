#!/bin/sh
set -eu
cd "$(dirname "$0")"
test -d .venv || python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
test -f .env || cp .env.example .env
.venv/bin/python scripts/manage.py setup-key
exec .venv/bin/python -m backend.run
