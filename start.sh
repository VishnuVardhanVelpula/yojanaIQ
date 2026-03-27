#!/bin/bash

# Cloud services like Render, Railway assign their own PORT environment variable.
# We default to 8000 if it's not set.
PORT=${PORT:-8000}

echo "🤖 Starting Telegram Bot Worker..."
python bot.py &

echo "🚀 Starting FastAPI Web Service on port $PORT..."
uvicorn main:app --host 0.0.0.0 --port $PORT
