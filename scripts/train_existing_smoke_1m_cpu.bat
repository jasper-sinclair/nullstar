@echo off
setlocal

call "%~dp0cpu.bat"
if errorlevel 1 goto :environment_error

echo.
echo Nullstar trainer-only 1M-position CPU smoke test
echo Working directory: %CD%
echo Configuration: %CD%\configs\existing-sparse-smoke-1m.json
echo.

if not exist "training_sparse_stm.bin" goto :data_error
if not exist "configs\existing-sparse-smoke-1m.json" goto :config_error
if not exist "smoke" mkdir "smoke"

"%NULLSTAR_PYTHON%" -c "import sys, torch; print('Python:', sys.executable); print('PyTorch:', torch.__version__); print('Torch package:', torch.__file__); print('Training device: CPU')"
if errorlevel 1 goto :environment_error

"%NULLSTAR_PYTHON%" run_pipeline.py configs\existing-sparse-smoke-1m.json --start-at train.py
set "result=%errorlevel%"

echo.
echo Pipeline log: %CD%\smoke\training_stm_smoke_1m_pipeline.log
echo Training log: %CD%\smoke\training_stm_smoke_1m.log
if not "%result%"=="0" goto :pipeline_error
if not exist "smoke\network_stm_smoke_1m.bin" goto :network_error

for %%I in ("smoke\network_stm_smoke_1m.bin") do set "network_size=%%~zI"
echo Smoke network: %CD%\smoke\network_stm_smoke_1m.bin
echo Network size: %network_size% bytes
if not "%network_size%"=="394754" goto :network_size_error

echo Trainer-only smoke test completed successfully.
pause
exit /b 0

:pipeline_error
echo Trainer-only smoke test failed with exit code %result%.
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
echo ERROR: training_sparse_stm.bin is missing.
pause
exit /b 1

:config_error
echo ERROR: configs\existing-sparse-smoke-1m.json is missing.
pause
exit /b 1

:environment_error
echo ERROR: The CPU Python environment could not be activated or imported.
pause
exit /b 1
