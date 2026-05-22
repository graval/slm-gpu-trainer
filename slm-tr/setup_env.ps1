# PowerShell Environment Setup Script: SLM Lateral Movement Training
# Uses the active `python` on PATH (tested with Python 3.10–3.13).

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host "          SLM LATERAL MOVEMENT TRAINING - ENVIRONMENT SETUP              " -ForegroundColor Cyan
Write-Host "=======================================================================" -ForegroundColor Cyan

# 1. Resolve Python
Write-Host "[*] Checking for Python installation..." -ForegroundColor Green
$pythonExe = $null

if (Get-Command python -ErrorAction SilentlyContinue) {
    $versionText = & python --version 2>&1 | Out-String
    if ($versionText -match "Python 3\.(\d+)") {
        $minor = [int]$Matches[1]
        if ($minor -ge 10) {
            $pythonExe = (Get-Command python).Source
            Write-Host "[+] Found: $($versionText.Trim()) at $pythonExe" -ForegroundColor Green
        }
    }
}

if (-not $pythonExe) {
    $searchPaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe"
    )
    foreach ($path in $searchPaths) {
        if (Test-Path $path) {
            $pythonExe = $path
            $versionText = & $pythonExe --version 2>&1
            Write-Host "[+] Found: $versionText at $path" -ForegroundColor Green
            break
        }
    }
}

if (-not $pythonExe) {
    Write-Host "[!] Python 3.10+ not found. Install from https://www.python.org/downloads/ or run:" -ForegroundColor Red
    Write-Host "    winget install -e --id Python.Python.3.13" -ForegroundColor Yellow
    exit 1
}

# 2. Virtual environment
Write-Host "`n[*] Creating virtual environment (.venv)..." -ForegroundColor Green
if (Test-Path ".venv") {
    Write-Host "[i] Removing existing .venv (recreate for current Python)..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force .venv
}
& $pythonExe -m venv .venv
$venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "[!] Failed to create .venv" -ForegroundColor Red
    exit 1
}
Write-Host "[+] Virtual environment ready: $(& $venvPython --version)" -ForegroundColor Green

# 3. Dependencies
Write-Host "`n[*] Upgrading pip..." -ForegroundColor Green
& $venvPython -m pip install --upgrade pip

Write-Host "[*] Installing project requirements..." -ForegroundColor Green
& $venvPython -m pip install -r requirements.txt

# 4. Dataset setup
Write-Host "`n[*] Running dataset setup..." -ForegroundColor Green
& $venvPython scripts/setup_dataset.py

Write-Host "`n=======================================================================" -ForegroundColor Cyan
Write-Host "ENVIRONMENT SETUP COMPLETE" -ForegroundColor Cyan
Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host "SOC dashboard:" -ForegroundColor Green
Write-Host "  .\.venv\Scripts\streamlit run app.py" -ForegroundColor Yellow
Write-Host "EDR CLI:" -ForegroundColor Green
Write-Host "  .\.venv\Scripts\python detect.py --interactive" -ForegroundColor Yellow
Write-Host "=======================================================================" -ForegroundColor Cyan
