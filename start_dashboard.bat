@echo off
REM Start Job Search Dashboard on Windows

echo.
echo ========================================
echo  Job Search Automation - Web Dashboard
echo ========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies if needed
echo Installing dependencies...
pip install -q fastapi uvicorn

REM Start the web server
echo.
echo Starting server...
echo.
echo Open your browser and go to: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn web.app:app --reload --host 0.0.0.0 --port 8000

pause
