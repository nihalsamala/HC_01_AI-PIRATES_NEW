# WardPulse: Start Backend and Frontend together (PowerShell)
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
Set-Location $RepoRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Starting WardPulse Hospital Ward Early Warning System   " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check Python virtual environment
$PythonExe = Join-Path $RepoRoot "backend/.venv/Scripts/python.exe"
if (-not (Test-Path $PythonExe)) {
    Write-Host "[INFO] Creating virtual environment in backend/.venv..." -ForegroundColor Yellow
    python -m venv (Join-Path $RepoRoot "backend/.venv")
    & $PythonExe -m pip install -r (Join-Path $RepoRoot "backend/requirements.txt")
}

# 2. Seed database
Write-Host "[1/3] Seeding SQLite database from 20-bed simulator..." -ForegroundColor Green
& $PythonExe -m app.db.seed --cwd (Join-Path $RepoRoot "backend")
Push-Location (Join-Path $RepoRoot "backend")
& $PythonExe -m app.db.seed
Pop-Location

# 3. Start backend in a background job or separate process
Write-Host "[2/3] Starting FastAPI Backend on http://localhost:8000..." -ForegroundColor Green
$BackendProcess = Start-Process -FilePath $PythonExe -ArgumentList "-m", "uvicorn", "app.main:app", "--port", "8000", "--reload" -WorkingDirectory (Join-Path $RepoRoot "backend") -PassThru

# 4. Start frontend
Write-Host "[3/3] Starting Vite React Console on http://localhost:5173..." -ForegroundColor Green
Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Console:  http://localhost:5173" -ForegroundColor White
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  To test:  python scripts/check_stories.py" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop both servers." -ForegroundColor Yellow

$env:VITE_USE_MOCK = "false"
$env:VITE_API_URL = "http://localhost:8000"

try {
    Set-Location (Join-Path $RepoRoot "frontend")
    npm.cmd run dev
} finally {
    Write-Host "`nStopping backend process (PID: $($BackendProcess.Id))..." -ForegroundColor Yellow
    Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
    Write-Host "WardPulse shut down cleanly." -ForegroundColor Green
}
