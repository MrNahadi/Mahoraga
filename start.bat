@echo off
echo 🚀 Starting Mahoraga System...

:: Start Backend in new window
echo 🐍 Starting Backend...
start "Mahoraga Backend" cmd /k "cd backend && (if not exist venv python -m venv venv) && venv\Scripts\activate && pip install -q -r requirements.txt && python -m uvicorn main:app --reload --port 8000"

:: Start Frontend in new window
echo ⚛️ Starting Frontend...
start "Mahoraga Frontend" cmd /k "cd frontend && (if not exist node_modules npm install) && npm run dev"

echo ✅ System starting in new windows!
echo    Backend: http://localhost:8000
echo    Frontend: http://localhost:5173
echo.
echo Close the new windows to stop the servers.
pause
