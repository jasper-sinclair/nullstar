[CmdletBinding()]
param(
  [string]$Build,
  [string]$NetworkFile,
  [string]$NetworkId,
  [Parameter(Mandatory = $true)]
  [ValidateNotNullOrEmpty()]
  [string]$Summary,
  [ValidateSet("network", "source", "documentation", "tooling")]
  [string]$ChangeType,
  [string]$TrainingRun = "stm-base",
  [double]$ValidationLoss,
  [long]$ExpectedNetworkBytes = 394754,
  [string]$EmbedTool
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$buildInfoPath = Join-Path $repoRoot "BUILD_INFO.json"
$historyPath = Join-Path $repoRoot "docs\DEVELOPMENT_BUILDS.json"
$historyMarkdownPath = Join-Path $repoRoot "docs\DEVELOPMENT_BUILDS.md"
$uciHeaderPath = Join-Path $repoRoot "src\uci.h"
$netCppPath = Join-Path $repoRoot "src\net.cpp"

function Write-Utf8NoBomAtomic {
  param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][string]$Content
  )

  $temporaryPath = "$Path.prepare.tmp"
  $encoding = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($temporaryPath, $Content, $encoding)
  Move-Item -LiteralPath $temporaryPath -Destination $Path -Force
}

function Get-EmbedToolPath {
  param([string]$RequestedPath)

  $candidates = @()
  if (-not [string]::IsNullOrWhiteSpace($RequestedPath)) {
    $candidates += $RequestedPath
  }
  if (-not [string]::IsNullOrWhiteSpace($env:NULLSTAR_EMBED_FILE)) {
    $candidates += $env:NULLSTAR_EMBED_FILE
  }
  $repoToolPath = Join-Path $repoRoot "build\tools\embed_file.exe"
  $embedSourcePath = Join-Path $repoRoot "tools\embed_file.cpp"
  $candidates += $repoToolPath

  foreach ($candidate in $candidates) {
    if (Test-Path -LiteralPath $candidate -PathType Leaf) {
      if ($candidate -ne $repoToolPath -or
          (Get-Item -LiteralPath $candidate).LastWriteTimeUtc -ge
          (Get-Item -LiteralPath $embedSourcePath).LastWriteTimeUtc) {
        return (Resolve-Path -LiteralPath $candidate).Path
      }
    }
  }

  $compilerCandidates = @(
    "C:\msys64\mingw64\bin\g++.exe",
    "C:\msys64\ucrt64\bin\g++.exe"
  )
  $compilerPath = $compilerCandidates |
    Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } |
    Select-Object -First 1

  if ($null -eq $compilerPath) {
    throw "embed_file.exe is missing and MinGW g++ was not found. Build tools/embed_file.cpp or pass -EmbedTool."
  }

  $toolDirectory = Split-Path -Parent $repoToolPath
  New-Item -ItemType Directory -Path $toolDirectory -Force | Out-Null
  $originalPath = $env:PATH
  try {
    $env:PATH = (Split-Path -Parent $compilerPath) + ";" + $env:PATH
    & $compilerPath `
      -std=c++20 `
      -O2 `
      -Wall `
      -Wextra `
      -Wpedantic `
      -static `
      $embedSourcePath `
      -o $repoToolPath
    if ($LASTEXITCODE -ne 0) {
      throw "Failed to build embed_file.exe with exit code $LASTEXITCODE."
    }
  } finally {
    $env:PATH = $originalPath
  }

  return (Resolve-Path -LiteralPath $repoToolPath).Path
}

function Get-HistoryMarkdown {
  param([object[]]$Builds)

  $lines = New-Object System.Collections.Generic.List[string]
  $lines.Add("# Nullstar development builds")
  $lines.Add("")
  $lines.Add("This ledger separates the sequential development build from the NNUE")
  $lines.Add("training epoch. The machine-readable source is DEVELOPMENT_BUILDS.json;")
  $lines.Add("BUILD_INFO.json records the currently prepared source tree.")
  $lines.Add("")
  $lines.Add("| Build | Change | Network | Epoch | Network SHA-256 | Playing-equivalent | Test | Summary |")
  $lines.Add("| --- | --- | --- | ---: | --- | --- | --- | --- |")

  foreach ($entry in $Builds) {
    $epoch = if ($null -eq $entry.network.epoch) { "-" } else { [string]$entry.network.epoch }
    $shortHash = ([string]$entry.network.sha256).Substring(0, 12) + "..."
    $equivalent = if ([string]::IsNullOrWhiteSpace([string]$entry.playing_equivalent_to)) {
      "-"
    } else {
      [string]$entry.playing_equivalent_to
    }
    $tests = New-Object System.Collections.Generic.List[string]
    if ($null -ne $entry.test) {
      $tests.Add("$($entry.test.rating) Elo; $($entry.test.games) games; $($entry.test.score_percent)%")
    }
    $strongPoolProperty = $entry.PSObject.Properties["strong_pool_test"]
    if ($null -ne $strongPoolProperty -and $null -ne $strongPoolProperty.Value) {
      $strongPoolTest = $strongPoolProperty.Value
      $tests.Add("strong pool: $($strongPoolTest.rating) Elo; $($strongPoolTest.games) games; $($strongPoolTest.score_percent)%")
    }
    $test = if ($tests.Count) { [string]::Join("; ", $tests) } else { "-" }
    $summaryText = ([string]$entry.summary).Replace("|", "\|")
    $lines.Add("| $($entry.build) | $($entry.change_type) | $($entry.network.id) | $epoch | $shortHash | $equivalent | $test | $summaryText |")
  }

  $lines.Add("")
  $lines.Add("## Preparing the next build")
  $lines.Add("")
  $lines.Add("From the repository root, run:")
  $lines.Add("")
  $lines.Add('```powershell')
  $lines.Add('.\scripts\prepare_dev_build.ps1 `')
  $lines.Add('  -NetworkFile "C:\path\to\network_stm_base_epoch_20.bin" `')
  $lines.Add('  -Summary "Epoch 20 STM candidate" `')
  $lines.Add('  -ValidationLoss 0.415064')
  $lines.Add('```')
  $lines.Add("")
  $lines.Add("The script chooses the next consecutive build number, validates and embeds")
  $lines.Add("the network, updates the UCI version, and records exact SHA-256 hashes. Omit")
  $lines.Add("-NetworkFile for a source, documentation, or tooling-only build; the current")
  $lines.Add("network identity will be retained.")
  $lines.Add("")
  $lines.Add("After compiling and verifying the binaries, copy the repository to the")
  $lines.Add("suggested numbered snapshot directory printed by the script.")
  $lines.Add("")

  return [string]::Join([Environment]::NewLine, $lines)
}

if (-not (Test-Path -LiteralPath $buildInfoPath -PathType Leaf)) {
  throw "Missing current build metadata: $buildInfoPath"
}
if (-not (Test-Path -LiteralPath $historyPath -PathType Leaf)) {
  throw "Missing development build history: $historyPath"
}

$currentInfo = Get-Content -LiteralPath $buildInfoPath -Raw | ConvertFrom-Json
$history = Get-Content -LiteralPath $historyPath -Raw | ConvertFrom-Json
$currentBuildNumber = 0
if (-not [int]::TryParse([string]$currentInfo.build, [ref]$currentBuildNumber)) {
  throw "Invalid current build number in BUILD_INFO.json: $($currentInfo.build)"
}

$expectedBuildNumber = $currentBuildNumber + 1
if ([string]::IsNullOrWhiteSpace($Build)) {
  $Build = $expectedBuildNumber.ToString("000")
} elseif ($Build -notmatch '^\d{3}$') {
  throw "Build must contain exactly three digits."
} elseif ([int]$Build -ne $expectedBuildNumber) {
  throw "Build $Build is not consecutive; expected $($expectedBuildNumber.ToString('000'))."
}

$existingBuild = @($history.builds) | Where-Object { $_.build -eq $Build }
if ($null -ne $existingBuild -and @($existingBuild).Count -gt 0) {
  throw "Build $Build already exists in DEVELOPMENT_BUILDS.json."
}

$hasNewNetwork = -not [string]::IsNullOrWhiteSpace($NetworkFile)
if ([string]::IsNullOrWhiteSpace($ChangeType)) {
  $ChangeType = if ($hasNewNetwork) { "network" } else { "source" }
}

$stagedNetCppPath = $null
if ($hasNewNetwork) {
  $resolvedNetworkPath = (Resolve-Path -LiteralPath $NetworkFile).Path
  $networkItem = Get-Item -LiteralPath $resolvedNetworkPath
  if ($networkItem.Length -ne $ExpectedNetworkBytes) {
    throw "Unexpected network size $($networkItem.Length); expected $ExpectedNetworkBytes bytes."
  }

  if ([string]::IsNullOrWhiteSpace($NetworkId)) {
    $NetworkId = [System.IO.Path]::GetFileNameWithoutExtension($networkItem.Name)
    $NetworkId = ($NetworkId -replace '^network_', '') -replace '_', '-'
  }

  $networkEpoch = $null
  if ($networkItem.Name -match 'epoch[_-]?(\d+)') {
    $networkEpoch = [int]$Matches[1]
  }

  $networkHash = (Get-FileHash -LiteralPath $resolvedNetworkPath -Algorithm SHA256).Hash
  $networkRecord = [ordered]@{
    id = $NetworkId
    training_run = $TrainingRun
    source_file = $networkItem.Name
    epoch = $networkEpoch
    validation_loss = if ($PSBoundParameters.ContainsKey("ValidationLoss")) { $ValidationLoss } else { $null }
    bytes = $networkItem.Length
    sha256 = $networkHash
  }

  $embedToolPath = Get-EmbedToolPath -RequestedPath $EmbedTool
  $stagedNetCppPath = "$netCppPath.prepare.tmp"
  if (Test-Path -LiteralPath $stagedNetCppPath) {
    Remove-Item -LiteralPath $stagedNetCppPath -Force
  }

  & $embedToolPath $resolvedNetworkPath $stagedNetCppPath
  if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $stagedNetCppPath -PathType Leaf)) {
    throw "embed_file.exe failed with exit code $LASTEXITCODE."
  }
  $netCppSourcePath = $stagedNetCppPath
} else {
  $networkRecord = [ordered]@{
    id = $currentInfo.network.id
    training_run = $currentInfo.network.training_run
    source_file = $currentInfo.network.source_file
    epoch = $currentInfo.network.epoch
    validation_loss = $currentInfo.network.validation_loss
    bytes = $currentInfo.network.bytes
    sha256 = $currentInfo.network.sha256
  }
  $netCppSourcePath = $netCppPath
}

$netCppItem = Get-Item -LiteralPath $netCppSourcePath
$netCppRecord = [ordered]@{
  bytes = $netCppItem.Length
  sha256 = (Get-FileHash -LiteralPath $netCppSourcePath -Algorithm SHA256).Hash
}

$uciText = [System.IO.File]::ReadAllText($uciHeaderPath)
$versionPattern = 'constexpr auto engine_version = "[^"]+";'
$versionMatches = [regex]::Matches($uciText, $versionPattern)
if ($versionMatches.Count -ne 1) {
  throw "Expected exactly one engine_version declaration in src/uci.h."
}
$newUciText = ([regex]$versionPattern).Replace(
  $uciText,
  "constexpr auto engine_version = `"$Build`";",
  1
)

$playingEquivalent = $null
if (-not $hasNewNetwork -and $ChangeType -in @("documentation", "tooling")) {
  $playingEquivalent = [string]$currentInfo.build
}

$preparedAt = (Get-Date).ToString("o")
$publicReleaseBase = if ($null -ne $currentInfo.public_release_base) {
  [string]$currentInfo.public_release_base
} else {
  "003"
}

$entry = [ordered]@{
  build = $Build
  uci_name = "Nullstar $Build"
  reported_uci_version = $Build
  public_release_base = $publicReleaseBase
  parent_build = [string]$currentInfo.build
  change_type = $ChangeType
  playing_equivalent_to = $playingEquivalent
  summary = $Summary
  prepared_at = $preparedAt
  network = $networkRecord
  embedded_net_cpp = $netCppRecord
  test = $null
}

$buildInfo = [ordered]@{ schema_version = 1 }
foreach ($key in $entry.Keys) {
  $buildInfo[$key] = $entry[$key]
}

$newBuilds = @($history.builds) + @([pscustomobject]$entry)
$newHistory = [ordered]@{
  schema_version = 1
  builds = $newBuilds
}

$buildInfoJson = ($buildInfo | ConvertTo-Json -Depth 10) + [Environment]::NewLine
$historyJson = ($newHistory | ConvertTo-Json -Depth 10) + [Environment]::NewLine
$historyMarkdown = (Get-HistoryMarkdown -Builds $newBuilds) + [Environment]::NewLine

if ($hasNewNetwork) {
  Move-Item -LiteralPath $stagedNetCppPath -Destination $netCppPath -Force
}
Write-Utf8NoBomAtomic -Path $uciHeaderPath -Content $newUciText
Write-Utf8NoBomAtomic -Path $buildInfoPath -Content $buildInfoJson
Write-Utf8NoBomAtomic -Path $historyPath -Content $historyJson
Write-Utf8NoBomAtomic -Path $historyMarkdownPath -Content $historyMarkdown

$snapshotRoot = Join-Path (Split-Path -Parent $repoRoot) "nullstar dev\nullstar $Build"
Write-Host ""
Write-Host "Prepared Nullstar $Build"
Write-Host "Network: $($networkRecord.id)"
Write-Host "Network SHA-256: $($networkRecord.sha256)"
Write-Host "Embedded net.cpp SHA-256: $($netCppRecord.sha256)"
Write-Host "UCI identity: Nullstar $Build"
Write-Host "Suggested snapshot: $snapshotRoot"
