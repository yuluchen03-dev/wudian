$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$frontendRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$failures = New-Object System.Collections.Generic.List[string]

function Add-Failure {
  param([string]$Message)
  $script:failures.Add($Message) | Out-Null
}

function Read-TextFile {
  param([string]$RelativePath)
  $path = Join-Path $repoRoot $RelativePath
  if (-not (Test-Path -LiteralPath $path)) {
    Add-Failure "Missing file: $RelativePath"
    return ""
  }
  return Get-Content -LiteralPath $path -Raw -Encoding UTF8
}

function Join-CodePoints {
  param([int[]]$CodePoints)
  return -join ($CodePoints | ForEach-Object { [char]$_ })
}

function Assert-Contains {
  param(
    [string]$RelativePath,
    [string]$Needle,
    [string]$Label
  )
  $text = Read-TextFile $RelativePath
  if (-not $text.Contains($Needle)) {
    Add-Failure "$RelativePath missing: $Label"
  }
}

function Assert-AnyContains {
  param(
    [string[]]$RelativePaths,
    [string]$Needle,
    [string]$Label
  )
  foreach ($relativePath in $RelativePaths) {
    $path = Join-Path $repoRoot $relativePath
    if ((Test-Path -LiteralPath $path) -and (Get-Content -LiteralPath $path -Raw -Encoding UTF8).Contains($Needle)) {
      return
    }
  }
  Add-Failure "Delivery docs missing: $Label"
}

function Assert-EnvLine {
  param(
    [string]$Key,
    [string]$ExpectedValue
  )
  $envPath = Join-Path $frontendRoot ".env.local"
  if (-not (Test-Path -LiteralPath $envPath)) {
    Add-Failure "frontend/.env.local missing required public runtime keys."
    return
  }

  $expectedLine = "$Key=$ExpectedValue"
  $lines = Get-Content -LiteralPath $envPath -Encoding UTF8
  if ($lines -contains $expectedLine) {
    return
  }

  $hasKey = [bool]($lines | Where-Object { $_ -match "^\s*$([regex]::Escape($Key))\s*=" })
  if ($hasKey) {
    Add-Failure "frontend/.env.local has $Key but not the required public demo value. Current value suppressed."
  } else {
    Add-Failure "frontend/.env.local missing $Key."
  }
}

function Get-JsonFile {
  param([string]$RelativePath)
  $text = Read-TextFile $RelativePath
  if ([string]::IsNullOrWhiteSpace($text)) {
    return $null
  }
  try {
    return $text | ConvertFrom-Json
  } catch {
    Add-Failure "$RelativePath is not valid JSON: $($_.Exception.Message)"
    return $null
  }
}

function Assert-Script {
  param(
    [object]$PackageJson,
    [string]$RelativePath,
    [string]$ScriptName
  )
  if ($null -eq $PackageJson -or $null -eq $PackageJson.scripts -or -not ($PackageJson.scripts.PSObject.Properties.Name -contains $ScriptName)) {
    Add-Failure "$RelativePath missing npm script: $ScriptName"
  }
}

function Test-OwnedByWorkspace {
  param([object]$Process)
  $commandLine = [string]$Process.CommandLine
  $executablePath = [string]$Process.ExecutablePath
  return $commandLine.Contains($repoRoot) -or $executablePath.Contains($repoRoot)
}

function Check-Port {
  param([int]$Port)
  $listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
  if (-not $listeners) {
    Write-Host "[stage-check] port ${Port}: no listener"
    return
  }

  $owners = $listeners | Select-Object -ExpandProperty OwningProcess -Unique
  foreach ($owner in $owners) {
    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $owner" -ErrorAction SilentlyContinue
    if ($null -eq $process) {
      Write-Warning "port $Port listener PID $owner cannot be inspected."
      continue
    }

    $owned = Test-OwnedByWorkspace $process
    Write-Host "[stage-check] port ${Port}: PID $owner $($process.Name), workspace=$owned"

    if (($Port -eq 3000 -or $Port -eq 8000) -and -not $owned) {
      Write-Warning "port $Port is listening outside this workspace; confirm it is the intended Wudian process."
    }

    if ($Port -eq 8001 -and -not $owned) {
      $riskLabel = Join-CodePoints @(38750, 24735, 20856, 21518, 31471, 39118, 38505)
      Write-Warning "8001 ${riskLabel}: listener is outside this workspace; keep the demo API on port 8000 unless explicitly explained."
    }
  }
}

$frontendPkg = Get-JsonFile "frontend/package.json"
$rootPkg = Get-JsonFile "package.json"

Assert-Script $frontendPkg "frontend/package.json" "stage-check"
Assert-Script $frontendPkg "frontend/package.json" "clean"
Assert-Script $frontendPkg "frontend/package.json" "dev:clean"
Assert-Script $frontendPkg "frontend/package.json" "build:clean"
Assert-Script $frontendPkg "frontend/package.json" "start:clean"
Assert-Script $rootPkg "package.json" "frontend:stage-check"

Assert-EnvLine "NEXT_PUBLIC_API_URL" "http://localhost:8000/api"
Assert-EnvLine "NEXT_PUBLIC_USE_MOCK" "false"

$pitchFile = Get-ChildItem -LiteralPath $repoRoot -File |
  Where-Object { $_.Name -like "Pitch*3*.md" } |
  Select-Object -First 1
$pitchRelativePath = if ($pitchFile) { $pitchFile.Name } else { "Pitch_3min.md" }

$route = "/demo -> /sage-chat -> /about -> /roundtable"
Assert-Contains $pitchRelativePath $route "single demo route"
Assert-Contains "HACKATHON_OPTIMIZATIONS.md" $route "single demo route"

$deliveryDocs = @(
  $pitchRelativePath,
  "HACKATHON_OPTIMIZATIONS.md",
  "docs/hackathon/final-delivery-checklist.md"
)

$mockDisclosure = Join-CodePoints @(28436, 31034, 31283, 23450, 23618)
$retrievalPhrase = Join-CodePoints @(20808, 26816, 32034, 12289, 20877, 29983, 25104, 12289, 21487, 36861, 28335, 12289, 26816, 32034, 19981, 21040, 19981, 30828, 32534)
$evidencePage = Join-CodePoints @(21487, 20449, 38142, 36335, 35777, 25454, 39029)
$preEvent30 = Join-CodePoints @(36187, 21069, 32, 51, 48, 32, 20998, 38047)
$preStage5 = Join-CodePoints @(19978, 21488, 21069, 32, 53, 32, 20998, 38047)
$pptStatus = "PPT " + (Join-CodePoints @(26356, 26032, 29366, 24577))

Assert-AnyContains $deliveryDocs $mockDisclosure "mock usage must be disclosed"
Assert-AnyContains $deliveryDocs $retrievalPhrase "anti-hallucination wording"
Assert-AnyContains $deliveryDocs "Trae" "Trae contribution statement"
Assert-AnyContains $deliveryDocs $evidencePage "trusted evidence page material"
Assert-AnyContains $deliveryDocs $preEvent30 "30-minute pre-event checklist"
Assert-AnyContains $deliveryDocs $preStage5 "5-minute stage checklist"
Assert-AnyContains $deliveryDocs $pptStatus "PPT delivery status"

Check-Port 3000
Check-Port 8000
Check-Port 8001

if ($failures.Count -gt 0) {
  Write-Error ("Stage check failed with {0} issue(s):`n- {1}" -f $failures.Count, ($failures -join "`n- "))
}

Write-Host "[stage-check] delivery readiness checks passed."
