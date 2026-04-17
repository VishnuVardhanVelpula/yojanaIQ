@echo off
set PORT=8000
set PYTHONIOENCODING=utf-8

echo Starting Telegram Bot Worker...
start /B .\venv\Scripts\python.exe bot.py

echo Starting FastAPI Web Service on port %PORT%...
start /B .\venv\Scripts\uvicorn.exe main:app --host 0.0.0.0 --port %PORT%

echo Starting React Frontend...
cd frontend
start /B npm run dev
cd ..

echo All services started! Close this window to kill all.
pause
