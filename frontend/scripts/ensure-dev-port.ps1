$ErrorActionPreference = "Stop"

$expectedRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$port = if ($env:PORT) { [int]$env:PORT } else { 3000 }

$listeners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
$blocking = @()

foreach ($listener in $listeners) {
  $process = Get-CimInstance Win32_Process -Filter "ProcessId = $($listener.OwningProcess)" -ErrorAction SilentlyContinue
  if ($null -eq $process) {
    continue
  }

  $commandLine = [string]$process.CommandLine
  if (-not $commandLine.Contains($expectedRoot)) {
    $blocking += [pscustomobject]@{
      ProcessId = $process.ProcessId
      CommandLine = $commandLine
    }
  }
}

if ($blocking.Count -gt 0) {
  Write-Error "Port $port is occupied by a different project. Stop that process before starting Wudian.`n$($blocking | Format-List | Out-String)"
}

npx next dev -p $port
