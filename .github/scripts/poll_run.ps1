$runId=20897764662
$url="https://api.github.com/repos/ZephyrTut/SupplyChain-Reconciler-Plus/actions/runs/$runId"
while ($true) {
  try {
    $r = Invoke-RestMethod -Uri $url -Headers @{Accept='application/vnd.github+json'} -ErrorAction Stop
  } catch {
    Write-Host "API error: $($_.Exception.Message)"
    Start-Sleep -Seconds 5
    continue
  }
  $s = $r.status
  $c = $r.conclusion
  Write-Host "status=$s conclusion=$c"
  if ($s -ne 'in_progress' -and $s -ne 'queued') {
    $r | ConvertTo-Json -Depth 6
    break
  }
  Start-Sleep -Seconds 8
}
