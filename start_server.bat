@echo off
title CivicAI - Smart Civic Management Platform
echo ===========================================================================
echo  CIVICAI - PROFESSIONAL AI-POWERED SMART CIVIC MANAGEMENT PLATFORM
echo  Smart Cities. Smarter Decisions. Faster Resolutions.
echo ===========================================================================
echo Starting server on http://localhost:8000 ...

if exist "%LOCALAPPDATA%\Python\bin\python.exe" (
    "%LOCALAPPDATA%\Python\bin\python.exe" backend/app.py
) else (
    python backend/app.py
)
pause
