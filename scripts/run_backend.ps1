$ErrorActionPreference = "Stop"

# Change to repo root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $ScriptDir "..")

if (Test-Path "backend/.venv/Scripts/Activate.ps1") {
    & "backend/.venv/Scripts/Activate.ps1"
}

Set-Location "backend"
uvicorn app.main:app --reload --port 8000
