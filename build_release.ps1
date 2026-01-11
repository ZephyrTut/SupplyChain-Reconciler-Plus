param(
    [string]$Version = "v1.4.3"
)

# Build and package SupplyChain-Reconciler-Plus on Windows
# Usage: .\build_release.ps1 -Version v1.4.3

$ErrorActionPreference = 'Stop'
$root = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
Set-Location -Path $root
Write-Host "Working directory: $root"

# 1. Create venv if missing
$venvPath = Join-Path $root ".venv\Scripts\python.exe"
if (-Not (Test-Path $venvPath)) {
    Write-Host "Creating virtualenv .venv..."
    python -m venv .venv
}

# 2. Activate
Write-Host "Activating virtualenv..."
. .\venv\Scripts\Activate.ps1

# 3. Upgrade pip and install deps
Write-Host "Installing dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# 4. Build with PyInstaller
Write-Host "Running PyInstaller..."
pyinstaller --noconfirm --onefile --windowed --name SupplyChain-Reconciler-Plus main.py

# 5. Package zip
$exe = Join-Path $root "dist\SupplyChain-Reconciler-Plus.exe"
$zip = Join-Path $root "dist\reconciler-$Version-windows.zip"
if (Test-Path $exe) {
    if (Test-Path $zip) { Remove-Item $zip -Force }
    Write-Host "Zipping $exe -> $zip"
    Compress-Archive -Path $exe -DestinationPath $zip
    Write-Host "Package created: $zip"
} else {
    Write-Error "Build failed: executable not found: $exe"
    exit 1
}

# 6. Create git tag if missing and push
$tagExists = git tag -l $Version
if (-Not $tagExists) {
    Write-Host "Creating git tag $Version..."
    git tag -a $Version -m "Release $Version"
    git push origin $Version
} else {
    Write-Host "Tag $Version already exists. Skipping tag creation."
}

Write-Host "Done."