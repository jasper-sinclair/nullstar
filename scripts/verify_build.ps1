[CmdletBinding()]
param(
  [string[]]$Engine,
  [ValidateRange(1, 7)]
  [int]$PerftDepth = 5,
  [UInt64]$ExpectedPerftNodes = 4865609,
  [ValidateRange(1, 20)]
  [int]$BenchDepth = 10
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$binaryRoot = Join-Path $repoRoot "binaries"
$buildInfoPath = Join-Path $repoRoot "BUILD_INFO.json"

if (-not (Test-Path -LiteralPath $buildInfoPath -PathType Leaf)) {
  throw "Build metadata is missing: $buildInfoPath"
}

$buildInfo = Get-Content -LiteralPath $buildInfoPath -Raw | ConvertFrom-Json
$expectedIdentity = "id name $($buildInfo.uci_name)"

if ($null -eq $Engine -or $Engine.Count -eq 0) {
  $Engine = @(
    Get-ChildItem -LiteralPath $binaryRoot -File -Filter "*.exe" |
      Sort-Object Name |
      Select-Object -ExpandProperty FullName
  )
}
if ($Engine.Count -eq 0) {
  throw "No engine binaries were selected."
}

$results = @()
$expectedBenchNodes = $null
foreach ($candidate in $Engine) {
  $path = (Resolve-Path -LiteralPath $candidate).Path
  $commands = @(
    "uci",
    "isready",
    "position startpos",
    "perft $PerftDepth",
    "bench $BenchDepth",
    "quit"
  )
  $output = $commands | & $path 2>&1
  if ($LASTEXITCODE -ne 0) {
    throw "$path exited with code $LASTEXITCODE."
  }

  $identity = $output |
    Where-Object { $_ -like "id name *" } |
    Select-Object -First 1
  if ($identity -ne $expectedIdentity) {
    throw "$path reports '$identity'; expected '$expectedIdentity'."
  }
  if ($output -notcontains "readyok") {
    throw "$path did not report readyok."
  }

  $perftLine = $output |
    Where-Object { $_ -match "^node (\d+)$" } |
    Select-Object -First 1
  if (-not $perftLine) {
    throw "$path did not produce a perft result."
  }
  $perftNodes = [UInt64]([regex]::Match($perftLine, "\d+").Value)
  if ($perftNodes -ne $ExpectedPerftNodes) {
    throw "$path produced $perftNodes perft nodes; expected $ExpectedPerftNodes."
  }

  $benchLine = $output |
    Where-Object { $_ -match "^Nodes (\d+)$" } |
    Select-Object -Last 1
  if (-not $benchLine) {
    throw "$path did not produce a benchmark result."
  }
  $benchNodes = [UInt64]([regex]::Match($benchLine, "\d+").Value)
  if ($null -eq $expectedBenchNodes) {
    $expectedBenchNodes = $benchNodes
  } elseif ($benchNodes -ne $expectedBenchNodes) {
    throw "$path produced $benchNodes benchmark nodes; expected $expectedBenchNodes."
  }

  $item = Get-Item -LiteralPath $path
  $results += [pscustomobject]@{
    Binary = $item.Name
    Bytes = $item.Length
    Perft = $perftNodes
    Bench = $benchNodes
    SHA256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
  }
}

Write-Host ""
Write-Host "Verified $($results.Count) Nullstar $($buildInfo.build) binaries."
$results | Format-Table -AutoSize
