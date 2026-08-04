$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

if (-not (Test-Path ".env")) {
    throw "Missing .env. Copy .env.prod.example to .env and set secrets first."
}

docker compose -f docker-compose.prod.yml config | Out-Null
docker compose -f docker-compose.prod.yml up -d --build

$port = if ($env:NGINX_HTTP_PORT) { $env:NGINX_HTTP_PORT } else { "80" }
$baseUrl = "http://127.0.0.1:$port"

Write-Host "Waiting for nginx health..."
$deadline = (Get-Date).AddMinutes(3)
do {
    $status = docker compose -f docker-compose.prod.yml ps nginx
    if ($status -match "\(healthy\)") { break }
    Start-Sleep -Seconds 5
} while ((Get-Date) -lt $deadline)

Invoke-RestMethod -Uri "$baseUrl/health"
Invoke-WebRequest -Uri "$baseUrl/login" -UseBasicParsing | Out-Null
Invoke-WebRequest -Uri "$baseUrl/api/health/ready" -UseBasicParsing | Out-Null

Write-Host "Deploy smoke checks passed."
