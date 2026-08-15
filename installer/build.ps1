# ==============================================================================
# SENTIENT_OS v2 — Automated Full Build & Packaging Script
# ==============================================================================

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  SENTIENT_OS v2 — Packaging & Release Pipeline  " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$PythonEngineDir = Join-Path $ProjectRoot "python-engine"
$ElectronAppDir = Join-Path $ProjectRoot "electron-app"

# 1. Run Python Unit & Integration Tests
Write-Host "`n[1/4] Running Python Engine Test Suite..." -ForegroundColor Yellow
Set-Location $PythonEngineDir
pytest -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Python test suite failed. Aborting build." -ForegroundColor Red
    exit 1
}

# 2. Build Python Binary with PyInstaller
Write-Host "`n[2/4] Compiling Python Engine binary (sentient.exe)..." -ForegroundColor Yellow
pyinstaller sentient.spec --clean --noconfirm
if (-not (Test-Path "$PythonEngineDir\dist\sentient.exe")) {
    Write-Host "[ERROR] PyInstaller compilation failed. sentient.exe not found." -ForegroundColor Red
    exit 1
}
Write-Host "[SUCCESS] Python binary built at $PythonEngineDir\dist\sentient.exe" -ForegroundColor Green

# 3. Compile TypeScript
Write-Host "`n[3/4] Compiling Electron TypeScript..." -ForegroundColor Yellow
Set-Location $ElectronAppDir
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] TypeScript build failed." -ForegroundColor Red
    exit 1
}

# 4. Package Electron App (Installer & Portable)
Write-Host "`n[4/4] Generating Installer & Portable packages..." -ForegroundColor Yellow
npx electron-builder --config electron-builder.yml

Write-Host "`n==================================================" -ForegroundColor Green
Write-Host "  BUILD COMPLETE! Artifacts ready in dist/ folder" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Set-Location $ProjectRoot
