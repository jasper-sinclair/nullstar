@echo off
setlocal

call "%~dp0cpu.bat"
if errorlevel 1 goto :environment_error

echo.
echo Nullstar full STM training
echo Working directory: %CD%
echo Configuration: %CD%\config.json
echo.

if not exist "..\DATA\MASTER\training_stm.txt" goto :data_error
if not exist "..\DATA\MASTER\training_stm.txt.manifest.json" goto :data_error

python -c "import torch; print('PyTorch:', torch.__version__); print('Training device: CPU')"
if errorlevel 1 goto :environment_error

if exist "checkpoint_stm_base.pt" (
  echo.
  echo A full-training checkpoint already exists.
  choice /C YN /N /M "Resume that checkpoint? [Y/N] "
  if errorlevel 2 exit /b 0
)

python run_pipeline.py
set "result=%errorlevel%"

echo.
echo Pipeline log: %CD%\training_stm_base_pipeline.log
if "%result%"=="0" (
  echo Full training pipeline completed successfully.
) else (
  echo Full training pipeline failed with exit code %result%.
)
pause
exit /b %result%

:data_error
echo ERROR: The STM master corpus or its manifest is missing.
pause
exit /b 1

:environment_error
echo ERROR: The CPU Python environment could not be activated or imported.
pause
exit /b 1
