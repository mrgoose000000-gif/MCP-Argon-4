@echo off
setlocal
title BANG DIEU KHIEN GEMINI 4 ARGON MULTI-ACCOUNT

cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set PY_CMD=.venv\Scripts\python.exe
) else (
    set PY_CMD=python
)

echo ==============================================================================
echo   DANG MO BANG DIEU KHIEN GEMINI 4 ARGON MULTI-ACCOUNT...
echo   URL: http://127.0.0.1:8000/dashboard
echo ==============================================================================

%PY_CMD% run_dashboard.py
pause
