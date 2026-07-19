param(
  [ValidateRange(8, 20)]
  [int]$Depth = 13
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = $PSScriptRoot
$project = Join-Path $root 'src\nullstar.vcxproj'
$engine = Join-Path $root 'nullstar_msvc_pgo.exe'
$vswhere = 'C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe'

if (-not (Test-Path -LiteralPath $vswhere)) {
  throw 'Visual Studio Installer (vswhere.exe) was not found.'
}

$vsPath = & $vswhere -latest -property installationPath
if (-not $vsPath) {
  throw 'No Visual Studio installation was found.'
}

$msbuild = Join-Path $vsPath 'MSBuild\Current\Bin\MSBuild.exe'
$toolRoot = Get-ChildItem (Join-Path $vsPath 'VC\Tools\MSVC') -Directory |
  Sort-Object Name -Descending |
  Select-Object -First 1
$pgortDir = Join-Path $toolRoot.FullName 'bin\Hostx64\x64'

Push-Location $root
try {
  & $msbuild $project /t:Rebuild /m /p:Configuration=Release /p:Platform=x64 `
    /p:TargetName=nullstar_msvc_pgo `
    /p:WholeProgramOptimization=PGInstrument /v:minimal
  if ($LASTEXITCODE -ne 0) {
    throw 'MSVC PGO instrumentation build failed.'
  }

  $savedPath = $env:PATH
  try {
    $env:PATH = $pgortDir + ';' + $savedPath
    $trainingOutput = @("bench $Depth", 'quit') | & $engine 2>&1
    if ($LASTEXITCODE -ne 0) {
      throw 'Instrumented Nullstar training run failed.'
    }
  }
  finally {
    $env:PATH = $savedPath
  }

  $expectedNodes = if ($Depth -eq 13) { 2985205 } else { $null }
  $result = $trainingOutput |
    Where-Object { $_ -match '^Nodes (\d+)$' } |
    Select-Object -Last 1
  if (-not $result) {
    throw 'Training run did not produce a benchmark result.'
  }
  if ($null -ne $expectedNodes -and $result -ne "Nodes $expectedNodes") {
    throw "Training benchmark signature changed: $result"
  }

  # Preserve the generated profile while forcing an optimized relink.
  $resolvedEngine = (Resolve-Path -LiteralPath $engine).Path
  if ($resolvedEngine -ne $engine) {
    throw "Unexpected executable path: $resolvedEngine"
  }
  Remove-Item -LiteralPath $resolvedEngine

  & $msbuild $project /t:Build /m /p:Configuration=Release /p:Platform=x64 `
    /p:TargetName=nullstar_msvc_pgo `
    /p:WholeProgramOptimization=PGOptimize /v:minimal
  if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $engine)) {
    throw 'MSVC profile-optimized link failed.'
  }

  $smoke = @('bench 10', 'quit') | & $engine 2>&1
  if ($LASTEXITCODE -ne 0 -or -not ($smoke -match '^Nodes 890981$')) {
    throw 'Optimized MSVC executable failed its benchmark smoke test.'
  }

  Write-Host "MSVC PGO build complete: $engine"
  Write-Host "Training result: $result"
}
finally {
  Pop-Location
}
