$ErrorActionPreference = "Stop"

$frontendRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$nextPath = Join-Path $frontendRoot ".next"
$allowCleanWhileRunning = $env:ALLOW_NEXT_CLEAN_WHILE_RUNNING -eq "true"

function Test-OwnedNextListener {
  param([int]$Port)

  $listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
  foreach ($listener in $listeners) {
    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $($listener.OwningProcess)" -ErrorAction SilentlyContinue
    if ($null -eq $process) {
      continue
    }

    $commandLine = [string]$process.CommandLine
    if ($commandLine.Contains($frontendRoot) -and $commandLine.Contains("next")) {
      return $true
    }
  }

  return $false
}

if (-not (Test-Path -LiteralPath $nextPath)) {
  Write-Host "[clean-next] .next does not exist; nothing to clean."
  return
}

$devPort = if ($env:PORT) { [int]$env:PORT } else { 3000 }
if (-not $allowCleanWhileRunning -and (Test-OwnedNextListener $devPort)) {
  throw "[clean-next] Refusing to clean .next while a Wudian Next server is listening on port $devPort. Stop the server first, or set ALLOW_NEXT_CLEAN_WHILE_RUNNING=true for a deliberate clean."
}

$resolvedNext = (Resolve-Path -LiteralPath $nextPath).Path
$frontendPrefix = $frontendRoot.TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar

if (-not $resolvedNext.StartsWith($frontendPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
  throw "[clean-next] Refusing to remove path outside frontend: $resolvedNext"
}

Remove-Item -LiteralPath $resolvedNext -Recurse -Force
Write-Host "[clean-next] removed $resolvedNext"
