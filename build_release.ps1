param(
    [string]$Version = "v1.4.3"
)

# Build and package SupplyChain-Reconciler-Plus on Windows
# Usage: .\build_release.ps1 -Version v1.4.3

$ErrorActionPreference = 'Stop'
$root = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
Set-Location -Path $root
Write-Host "Working directory: $root"

# 1. Ensure python executable available
$pythonCmd = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonCmd) {
    $pythonCmd = (Get-Command py -ErrorAction SilentlyContinue).Source
}
if (-not $pythonCmd) {
    Write-Error "Python executable not found in PATH. Install Python 3.10+ and retry."
    exit 1
}

# 2. Create venv if missing
$venvDir = Join-Path $root ".venv"
$pythonExe = Join-Path $venvDir "Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Host "Creating virtualenv $venvDir..."
    & $pythonCmd -m venv $venvDir
}

# 3. Activate virtualenv (if available)
Write-Host "Activating virtualenv..."
$activate = Join-Path $venvDir "Scripts\Activate.ps1"
if (Test-Path $activate) {
    . $activate
} else {
    Write-Host "Warning: activate script not found, will use explicit python path: $pythonExe"
}

# 4. Upgrade pip and install deps using venv python
Write-Host "Upgrading pip..."
& $pythonExe -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to upgrade pip (exit $LASTEXITCODE). Check network/proxy and try manually."
    exit 1
}

Write-Host "Installing requirements..."
& $pythonExe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install requirements (exit $LASTEXITCODE). Common causes: network/proxy or custom index SSL issues."
    Write-Host "Suggested fixes:"
    Write-Host "  1) Ensure HTTP_PROXY/HTTPS_PROXY are set correctly (include hostname), or unset them if not used."
    Write-Host "  2) Try installing manually with a trusted host:"
    Write-Host "       & $pythonExe -m pip install --trusted-host mirrors.aliyun.com -i https://mirrors.aliyun.com/pypi/simple -r requirements.txt"
    Write-Host "  3) Or use the default PyPI index:"
    Write-Host "       & $pythonExe -m pip install --index-url https://pypi.org/simple -r requirements.txt"
    Write-Host "  4) If none work, install dependencies on a machine with internet access and re-run this script."
    exit 1
}

Write-Host "Installing pyinstaller..."
& $pythonExe -m pip install pyinstaller
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install pyinstaller (exit $LASTEXITCODE)."
    Write-Host "Try: & $pythonExe -m pip install pyinstaller --trusted-host mirrors.aliyun.com -i https://mirrors.aliyun.com/pypi/simple"
    exit 1
}

# 5. Verify PyInstaller is available
Write-Host "Checking PyInstaller..."
try {
    & $pythonExe -c "import PyInstaller; print(PyInstaller.__version__)"
} catch {
    Write-Error "PyInstaller not installed in venv. Install it with: & $pythonExe -m pip install pyinstaller"
    Write-Host "If you are behind a proxy, set HTTP_PROXY/HTTPS_PROXY or use:"
    Write-Host "  & $pythonExe -m pip install --trusted-host mirrors.aliyun.com -i https://mirrors.aliyun.com/pypi/simple pyinstaller"
    exit 1
}

# 6. Build with PyInstaller
Write-Host "Running PyInstaller..."
& $pythonExe -m PyInstaller --noconfirm --onefile --windowed --name SupplyChain-Reconciler-Plus main.py

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