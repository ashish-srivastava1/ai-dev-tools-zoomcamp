# Single command for the whole test suite (backend lint + unit, integration on
# Postgres, frontend lint + tests) - all inside Docker.
#   powershell -ExecutionPolicy Bypass -File .\scripts\test.ps1
$ErrorActionPreference = 'Continue'
Push-Location (Join-Path $PSScriptRoot '..')
try {
  docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from tests
  $status = $LASTEXITCODE
  docker compose -f docker-compose.test.yml down -v | Out-Null
} finally {
  Pop-Location
}
if ($status -eq 0) { Write-Host "All tests passed" -ForegroundColor Green }
else { Write-Host "Tests failed (exit $status)" -ForegroundColor Red }
exit $status
