# CivicAI PowerShell Startup Script
Write-Host "===========================================================================" -ForegroundColor Cyan
Write-Host " CIVICAI - PROFESSIONAL AI-POWERED SMART CIVIC MANAGEMENT PLATFORM" -ForegroundColor White
Write-Host " Smart Cities. Smarter Decisions. Faster Resolutions." -ForegroundColor Cyan
Write-Host "===========================================================================" -ForegroundColor Cyan

$pythonExe = "$env:LOCALAPPDATA\Python\bin\python.exe"
if (Test-Path $pythonExe) {
    & $pythonExe backend/app.py
} else {
    python backend/app.py
}
