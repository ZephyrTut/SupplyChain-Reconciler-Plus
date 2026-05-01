param(
    [string]$Version = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$appName = "SupplyChain-Reconciler-Plus"
$platform = "windows-x64"
$specFile = Join-Path $PWD "SupplyChain-Reconciler-Plus.spec"

function Get-AppVersionFromSettings {
    $settingsPath = Join-Path $PWD "config\settings.py"
    if (-not (Test-Path $settingsPath)) {
        return "0.0.0"
    }

    $content = Get-Content $settingsPath -Raw
    $match = [regex]::Match($content, 'APP_VERSION\s*=\s*"([0-9.]+)"')
    if ($match.Success) {
        return $match.Groups[1].Value
    }
    return "0.0.0"
}

if ([string]::IsNullOrWhiteSpace($Version)) {
    $Version = "v" + (Get-AppVersionFromSettings)
}
elseif ($Version -notmatch "^v") {
    $Version = "v$Version"
}

Write-Host "Building version: $Version"

if (-not (Test-Path $specFile)) {
    throw "Spec file not found: $specFile"
}

$upx = Get-Command upx -ErrorAction SilentlyContinue
if ($null -ne $upx) {
    $upxDir = Split-Path -Parent $upx.Source
    Write-Host "Using UPX: $upxDir"
    pyinstaller --noconfirm --clean --upx-dir "$upxDir" $specFile
}
else {
    Write-Host "UPX not found, building without UPX"
    pyinstaller --noconfirm --clean $specFile
}

$distDir = Join-Path $PWD "dist"
$rawExe = Join-Path $distDir "$appName.exe"

if (-not (Test-Path $rawExe)) {
    throw "Executable not found: $rawExe"
}

$exeName = "$appName-$Version-$platform.exe"
$packageName = "$appName-$Version-$platform.7z"
$hashName = "$appName-$Version-$platform.sha256"

$exeOut = Join-Path $distDir $exeName
$packageOut = Join-Path $distDir $packageName
$hashOut = Join-Path $distDir $hashName

Copy-Item $rawExe $exeOut -Force

$exeSize = (Get-Item $exeOut).Length
if ($exeSize -lt 1MB) {
    throw "EXE size too small ($exeSize bytes), build may be invalid"
}

$sevenZip = Get-Command 7z -ErrorAction SilentlyContinue
if ($null -ne $sevenZip) {
    & $sevenZip.Source a -t7z -mx=9 -mmt=on $packageOut $exeOut | Out-Host
}
else {
    $packageName = "$appName-$Version-$platform.zip"
    $packageOut = Join-Path $distDir $packageName
    Compress-Archive -Path $exeOut -DestinationPath $packageOut -Force
}

$packageHash = (Get-FileHash $packageOut -Algorithm SHA256).Hash.ToLower()
@("$packageHash *$packageName") | Set-Content -Path $hashOut -Encoding ascii

Write-Host "Built exe: $exeOut"
Write-Host "Packaged: $packageOut"
Write-Host "Hash file: $hashOut"