param([long]$runId)
if (-not $runId) { Write-Host 'Usage: download_logs.ps1 <runId>'; exit 1 }
$logsUrl = "https://api.github.com/repos/ZephyrTut/SupplyChain-Reconciler-Plus/actions/runs/$runId/logs"
Write-Host "Downloading $logsUrl"
Invoke-WebRequest -Uri $logsUrl -OutFile "logs_$runId.zip" -UseBasicParsing
Write-Host "Extracting logs_$runId.zip to logs_$runId"
Expand-Archive -Path "logs_$runId.zip" -DestinationPath "logs_$runId" -Force
Get-ChildItem -Recurse "logs_$runId" | Select-Object -First 200 | Format-Table FullName,Length -AutoSize
