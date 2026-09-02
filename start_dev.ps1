#!/usr/bin/env pwsh
# Inicia SOLO el backend de pruebas en el puerto 8002 (DB separada mimetic_ai_dev)
$ErrorActionPreference = "Stop"
$backendDir = (Join-Path $PSScriptRoot "backend")

Write-Host "Backend de pruebas -> http://127.0.0.1:8002/docs" -ForegroundColor Cyan
Write-Host "DB separada: mimetic_ai_dev" -ForegroundColor Cyan

$env:MONGODB_DB_NAME = "mimetic_ai_dev"
$env:JWT_SECRET       = "mimetic-dev-secret"

Set-Location $backendDir
python -m uvicorn main:app --host 127.0.0.1 --port 8002 --reload
