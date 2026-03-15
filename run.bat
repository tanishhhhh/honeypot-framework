@echo off
echo Starting ML Honeypot Framework...

:: Activate virtual environment
call .venv\Scripts\activate

:: Start Flask API in a new window
start "Flask API" cmd /k "python src/app.py"

:: Start Streamlit Dashboard in a new window
start "Streamlit Dashboard" cmd /k "streamlit run src/dashboard.py"

echo Services started!
echo Flask API running on http://127.0.0.1:5000
echo Streamlit Dashboard running on http://localhost:8501
