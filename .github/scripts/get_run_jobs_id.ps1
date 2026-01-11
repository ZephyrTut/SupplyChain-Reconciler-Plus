param([long]$runId)
if (-not $runId) { Write-Host 'Usage: get_run_jobs_id.ps1 <runId>'; exit 1 }
$jobs = Invoke-RestMethod -Uri "https://api.github.com/repos/ZephyrTut/SupplyChain-Reconciler-Plus/actions/runs/$runId/jobs" -Headers @{Accept='application/vnd.github+json'}
foreach ($job in $jobs.jobs) {
  Write-Host "Job: $($job.name) id:$($job.id) status:$($job.status) conclusion:$($job.conclusion)"
  if ($job.steps) {
    foreach ($step in $job.steps) {
      Write-Host "  Step: $($step.number) - $($step.name) status:$($step.status) conclusion:$($step.conclusion)"
    }
  }
}
