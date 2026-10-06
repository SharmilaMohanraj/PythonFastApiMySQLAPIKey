#!/bin/sh
exec /usr/local/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
