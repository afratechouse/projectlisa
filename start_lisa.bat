@echo off
title Project Lisa - Local Server Launcher
cd /d "%~dp0"

echo ===================================================
echo       Starting Project Lisa Local Server
echo ===================================================

echo [1/3] Starting Docker Services (Redis, Qdrant, Evolution API)...
docker compose up -d

echo [2/3] Waiting for services to initialize...
timeout /t 5 /nobreak >nul

echo [3/3] Starting Lisa FastAPI Backend Engine...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

pause
