@echo off
echo =====================================================================
echo Starting AP Essential Commodities Price Intelligence Platform (FastAPI)
echo Backend API: http://127.0.0.1:8000
echo Swagger UI:  http://127.0.0.1:8000/docs
echo ReDoc UI:    http://127.0.0.1:8000/redoc
echo Web App UI:  http://127.0.0.1:8000/
echo =====================================================================
set PYTHONPATH=backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
