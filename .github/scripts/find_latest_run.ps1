$resp = Invoke-RestMethod -Uri "https://api.github.com/repos/ZephyrTut/SupplyChain-Reconciler-Plus/actions/runs?per_page=50" -Headers @{Accept='application/vnd.github+json'}
$runs = $resp.workflow_runs | Where-Object { $_.head_branch -eq 'v1.4.3' } | Sort-Object created_at -Descending
if ($runs -and $runs.Count -gt 0) {
  $runs[0] | ConvertTo-Json -Depth 6
} else {
  Write-Host 'no run found'
  exit 1
}
