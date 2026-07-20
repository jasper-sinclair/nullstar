@echo off
setlocal

call "%~dp0cpu.bat"
if errorlevel 1 goto :environment_error

echo.
echo Nullstar 1M-position CPU smoke training
echo Working directory: %CD%
echo Configuration: %CD%\configs\smoke-1m.json
echo.

if not exist "..\DATA\MASTER\training_stm.txt" goto :data_error
if not exist "..\DATA\MASTER\training_stm.txt.manifest.json" goto :data_error
if not exist "configs\smoke-1m.json" goto :config_error
if not exist "smoke" mkdir "smoke"

python -c "import torch; print('PyTorch:', torch.__version__); print('Training device: CPU')"
if errorlevel 1 goto :environment_error

if exist "smoke\checkpoint_stm_smoke_1m.pt" (
  echo.
  echo A smoke-test checkpoint already exists.
  choice /C YN /N /M "Resume that checkpoint? [Y/N] "
  if errorlevel 2 exit /b 0
)

python run_pipeline.py configs\smoke-1m.json
set "result=%errorlevel%"

echo.
if not "%result%"=="0" goto :pipeline_error
if not exist "smoke\network_stm_smoke_1m.bin" goto :network_error

for %%I in ("smoke\network_stm_smoke_1m.bin") do set "network_size=%%~zI"
echo Smoke network: %CD%\smoke\network_stm_smoke_1m.bin
echo Network size: %network_size% bytes
if not "%network_size%"=="394754" goto :network_size_error

echo Smoke training pipeline completed successfully.
pause
exit /b 0

:pipeline_error
echo Smoke training pipeline failed with exit code %result%.
pause
exit /b %result%

:network_error
echo ERROR: The smoke network was not exported.
pause
exit /b 1

:network_size_error
echo ERROR: Expected a 394754-byte 768x256 network.
pause
exit /b 1

:data_error
echo ERROR: The STM master corpus or its manifest is missing.
pause
exit /b 1

:config_error
echo ERROR: configs\smoke-1m.json is missing.
pause
exit /b 1

:environment_error
echo ERROR: The CPU Python environment could not be activated or imported.
pause
exit /b 1
