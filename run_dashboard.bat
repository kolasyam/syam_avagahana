@echo off
echo =====================================================================
echo Launching AP Essential Commodities Full Stack Intelligence Platform
echo =====================================================================
echo [1/2] Launching Backend API Server on http://127.0.0.1:8000 ...
start "AP Commodities - Backend API" cmd /k "set PYTHONPATH=backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Launching Frontend Development Server on http://127.0.0.1:5173 ...
start "AP Commodities - Frontend Dashboard" cmd /k "cd frontend && npm run dev"

echo.
echo =====================================================================
echo System services started successfully!
echo   - Interactive Dashboard:  http://127.0.0.1:5173
echo   - Backend OpenAPI Docs:   http://127.0.0.1:8000/docs
echo   - Static Mount:           http://127.0.0.1:8000/
echo =====================================================================
