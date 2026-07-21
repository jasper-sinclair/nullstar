param(
  [ValidateRange(8, 20)]
  [int]$Depth = 13
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Split-Path -Parent $PSScriptRoot
$project = Join-Path $root 'src\nullstar.vcxproj'
$binaryDir = Join-Path $root 'binaries'
$engine = Join-Path $binaryDir 'nullstar_msvc_pgo.exe'
$buildInfoPath = Join-Path $root 'BUILD_INFO.json'
$vswhere = 'C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe'

New-Item -ItemType Directory -Force -Path $binaryDir | Out-Null

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

  $result = $trainingOutput |
    Where-Object { $_ -match '^Nodes (\d+)$' } |
    Select-Object -Last 1
  if (-not $result) {
    throw 'Training run did not produce a benchmark result.'
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

  $smoke = @("bench $Depth", 'quit') | & $engine 2>&1
  $smokeResult = $smoke |
    Where-Object { $_ -match '^Nodes (\d+)$' } |
    Select-Object -Last 1
  if ($LASTEXITCODE -ne 0 -or -not $smokeResult -or $smokeResult -ne $result) {
    throw "Optimized MSVC benchmark does not match PGO training: '$smokeResult' versus '$result'."
  }

  $buildInfo = Get-Content -LiteralPath $buildInfoPath -Raw | ConvertFrom-Json
  $expectedIdentity = "id name $($buildInfo.uci_name)"
  $uciOutput = @('uci', 'quit') | & $engine 2>&1
  $idLine = $uciOutput |
    Where-Object { $_ -like 'id name *' } |
    Select-Object -First 1
  if ($LASTEXITCODE -ne 0 -or $idLine -ne $expectedIdentity) {
    throw "MSVC PGO executable reports '$idLine'; expected '$expectedIdentity'."
  }

  Write-Host "MSVC PGO build complete: $engine"
  Write-Host "Training result: $result"
  Write-Host "SHA-256: $((Get-FileHash -LiteralPath $engine -Algorithm SHA256).Hash)"
}
finally {
  Pop-Location
}
