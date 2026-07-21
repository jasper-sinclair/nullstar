[CmdletBinding()]
param(
  [ValidateSet(
    "all",
    "nonpgo",
    "pgo",
    "native",
    "avx2",
    "pgo-native",
    "pgo-avx2",
    "clean"
  )]
  [string]$Mode = "all",
  [int]$Jobs = 0,
  [string]$MsysRoot = "C:\msys64"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$sourceDirectory = Join-Path $repoRoot "src"
$binaryDirectory = Join-Path $repoRoot "binaries"
$buildInfoPath = Join-Path $repoRoot "BUILD_INFO.json"
$mingwBin = Join-Path $MsysRoot "mingw64\bin"
$msysBin = Join-Path $MsysRoot "usr\bin"
$make = Join-Path $mingwBin "mingw32-make.exe"

if (-not (Test-Path -LiteralPath $make -PathType Leaf)) {
  throw "MSYS2 MinGW make was not found: $make"
}
if (-not (Test-Path -LiteralPath $buildInfoPath -PathType Leaf)) {
  throw "Build metadata is missing: $buildInfoPath"
}
if ($Jobs -le 0) {
  $Jobs = [Environment]::ProcessorCount
}

$target = switch ($Mode) {
  "all" { "binaries" }
  default { $Mode }
}

$expectedBinaries = switch ($Mode) {
  "all" {
    @(
      "nullstar_mingw_native_nonpgo.exe",
      "nullstar_mingw_avx2_nonpgo.exe",
      "nullstar_mingw_native_pgo.exe",
      "nullstar_mingw_avx2_pgo.exe"
    )
  }
  "nonpgo" {
    @("nullstar_mingw_native_nonpgo.exe", "nullstar_mingw_avx2_nonpgo.exe")
  }
  "pgo" {
    @("nullstar_mingw_native_pgo.exe", "nullstar_mingw_avx2_pgo.exe")
  }
  "native" { @("nullstar_mingw_native_nonpgo.exe") }
  "avx2" { @("nullstar_mingw_avx2_nonpgo.exe") }
  "pgo-native" { @("nullstar_mingw_native_pgo.exe") }
  "pgo-avx2" { @("nullstar_mingw_avx2_pgo.exe") }
  "clean" { @() }
}

$originalPath = $env:PATH
try {
  $env:PATH = "$mingwBin;$msysBin;$env:PATH"
  Push-Location $sourceDirectory
  try {
    & $make "-j$Jobs" $target
    if ($LASTEXITCODE -ne 0) {
      throw "MinGW build failed with exit code $LASTEXITCODE."
    }
  } finally {
    Pop-Location
  }
} finally {
  $env:PATH = $originalPath
}

if ($Mode -eq "clean") {
  Write-Host "MinGW build products and profile data removed."
  exit 0
}

$buildInfo = Get-Content -LiteralPath $buildInfoPath -Raw | ConvertFrom-Json
$expectedIdentity = "id name $($buildInfo.uci_name)"
$results = @()

foreach ($name in $expectedBinaries) {
  $path = Join-Path $binaryDirectory $name
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
    throw "Expected binary was not produced: $path"
  }

  $uciOutput = @("uci", "quit") | & $path 2>&1
  $idLine = $uciOutput | Where-Object { $_ -like "id name *" } | Select-Object -First 1
  if ($idLine -ne $expectedIdentity) {
    throw "$name reports '$idLine'; expected '$expectedIdentity'."
  }

  $item = Get-Item -LiteralPath $path
  $results += [pscustomobject]@{
    Binary = $name
    Bytes = $item.Length
    SHA256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
    UCI = $buildInfo.uci_name
  }
}

Write-Host ""
Write-Host "MinGW $Mode build completed from $repoRoot"
$results | Format-Table -AutoSize
