#!/usr/bin/env pwsh
# Inicia el entorno de DESARROLLO completo en tu maquina local
# Backend: http://127.0.0.1:8002  |  Frontend: http://127.0.0.1:5174
# Base de datos separada: mimetic_ai_dev (no afecta el prototipo)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$backendDir = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  MIMETIC PRUEBAS - Entorno local" -ForegroundColor Cyan
Write-Host "  Backend:  http://127.0.0.1:8002" -ForegroundColor Cyan
Write-Host "  Frontend: http://127.0.0.1:5174" -ForegroundColor Cyan
Write-Host "  DB:       mimetic_ai_dev (separada)" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Verificar Python
try { python --version 2>&1 | Out-Null } catch { Write-Host "ERROR: Python no encontrado" -ForegroundColor Red; exit 1 }
# Verificar Node
try { node --version 2>&1 | Out-Null } catch { Write-Host "ERROR: Node.js no encontrado" -ForegroundColor Red; exit 1 }

# Dependencias Python
Write-Host "[1/3] Verificando dependencias Python..." -ForegroundColor Yellow
python -c "import fastapi, motor, dotenv, uvicorn, pydantic, passlib, jose" 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Instalando..." -ForegroundColor Gray
    Push-Location $backendDir
    pip install -r requirements.txt --quiet
    Pop-Location
}

# Dependencias Node
Write-Host "[2/3] Verificando dependencias Node..." -ForegroundColor Yellow
if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    Push-Location $frontendDir
    npm install --silent
    Pop-Location
}

# Iniciar backend (8002) con DB separada mimetic_ai_dev
Write-Host "[3/3] Iniciando backend en 8002 y frontend en 5174..." -ForegroundColor Yellow

# Backend en background
$env:MONGODB_DB_NAME = "mimetic_ai_dev"
$env:JWT_SECRET       = "mimetic-dev-secret"
$backendProc = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8002", "--reload" -WorkingDirectory $backendDir -PassThru -NoNewWindow

# Frontend en background
$env:VITE_API_URL = "http://127.0.0.1:8002"
$frontendProc = Start-Process -FilePath "npx.cmd" -ArgumentList "vite", "--port", "5174" -WorkingDirectory $frontendDir -PassThru -NoNewWindow

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  ENTORNO LOCAL ACTIVO" -ForegroundColor Green
Write-Host "  Backend:  http://127.0.0.1:8002/docs" -ForegroundColor Green
Write-Host "  Frontend: http://127.0.0.1:5174" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

try {
    while ($true) { Start-Sleep -Seconds 5 }
} finally {
    if (-not $backendProc.HasExited) { Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue }
    if (-not $frontendProc.HasExited) { Stop-Process -Id $frontendProc.Id -Force -ErrorAction SilentlyContinue }
    Write-Host "Servicios detenidos." -ForegroundColor Gray
}
