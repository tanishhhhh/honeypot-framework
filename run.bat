@echo off
echo Starting ML Honeypot Framework...

:: Activate virtual environment
call .venv\Scripts\activate

:: Start Flask API in a new window
start "Flask API" cmd /k "python src/app.py"

:: Start React Frontend in a new window
start "React Frontend" cmd /k "cd frontend && npm run dev"

echo Services started!
echo Flask API running on http://127.0.0.1:5000
echo React Dashboard running on http://localhost:5173
