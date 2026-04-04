Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $repoRoot

function Try-Run([scriptblock]$Block) {
  try {
    & $Block
    return $true
  } catch {
    return $false
  }
}

Write-Output "== EDI workspace sanity =="
Write-Output "Repo: $repoRoot"
Write-Output ""

# 1) Node + npm
Write-Output "[1/5] Node + npm"
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
  Write-Output "- node: NOT FOUND on PATH"
} else {
  $nodeVersion = node -v
  Write-Output "- node: $nodeVersion"
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
  Write-Output "- npm: NOT FOUND on PATH"
} else {
  $npmVersion = npm -v
  Write-Output "- npm: $npmVersion"
}
Write-Output ""

# 2) Python venv
Write-Output "[2/5] Python venv (.venv)"
$pythonExe = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $pythonExe)) {
  Write-Output "- .venv python: NOT FOUND at $pythonExe"
} else {
  $pyVersion = & $pythonExe -V 2>&1
  Write-Output "- .venv python: $pyVersion"
}
Write-Output ""

# 3) Expected run dirs + entrypoints
Write-Output "[3/5] Run dirs + entrypoints"
$backendDir = Join-Path $repoRoot 'backend'
$backendMain = Join-Path $backendDir 'app\main.py'
if (Test-Path $backendMain) {
  Write-Output "- backend entrypoint: OK ($backendMain)"
  Write-Output "- backend start (from backend/): uvicorn app.main:app --reload --port 8000"

  if (Test-Path $pythonExe) {
    Push-Location $backendDir
    try {
      $importResult = & $pythonExe -c "from app.main import app; print(app.title)" 2>&1
      Write-Output "- backend import (from backend/): OK ($importResult)"
    } catch {
      Write-Output "- backend import (from backend/): FAILED ($($_.Exception.Message))"
    } finally {
      Pop-Location
    }
  }
} else {
  Write-Output "- backend entrypoint: MISSING ($backendMain)"
}
Write-Output "- frontend start (from repo root): npm run dev"
Write-Output ""

# 4) Vite proxy sanity + infer backend port
Write-Output "[4/5] Vite proxy"
$viteConfig = Join-Path $repoRoot 'vite.config.ts'
$backendPort = 8000
if (-not (Test-Path $viteConfig)) {
  Write-Output "- vite.config.ts: MISSING"
} else {
  $viteText = Get-Content -Raw $viteConfig
  $required = @('/api', '/auth', '/files', '/fix')
  foreach ($k in $required) {
    if ($viteText -match [regex]::Escape("'$k'")) {
      Write-Output "- proxy key present: $k"
    } else {
      Write-Output "- proxy key MISSING: $k"
    }
  }

  $ports = @()
  foreach ($m in [regex]::Matches($viteText, 'localhost:(\d+)')) {
    $ports += [int]$m.Groups[1].Value
  }
  $ports = @($ports | Select-Object -Unique)
  if ($ports.Count -ge 1) {
    if ($ports.Count -eq 1) {
      $backendPort = $ports[0]
      Write-Output "- backend target port inferred: $backendPort"
    } else {
      Write-Output "- backend target ports inferred (multiple): $($ports -join ', ')"
    }
  } else {
    Write-Output "- backend target port inferred: (defaulting) $backendPort"
  }
}
Write-Output ""

# 5) Record likely ports + (optional) ping backend if running
Write-Output "[5/5] Ports"
$frontendPort = 5173
if (Test-Path $viteConfig) {
  $viteText = Get-Content -Raw $viteConfig
  $portMatch = [regex]::Match($viteText, '\bport\s*:\s*(\d+)')
  if ($portMatch.Success) {
    $frontendPort = [int]$portMatch.Groups[1].Value
  }
}
Write-Output "- backend:   http://localhost:$backendPort"
Write-Output "- frontend:  http://localhost:$frontendPort (typical; Vite may pick 5174 if 5173 is taken)"

$backendUrls = @(
  "http://127.0.0.1:$backendPort/",
  "http://localhost:$backendPort/"
)

$reachable = $false
foreach ($u in $backendUrls) {
  if (Try-Run { Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 3 | Out-Null }) {
    Write-Output "- backend ping: OK ($u)"
    $reachable = $true
    break
  }
}

if (-not $reachable) {
  Write-Output "- backend ping: not reachable ($($backendUrls -join ' or '))"
}

Write-Output ""
Write-Output "Done. See docs/ports.md for the recorded ports/commands."