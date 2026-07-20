@echo off
setlocal

call "%~dp0cpu.bat"
if errorlevel 1 goto :environment_error

echo.
echo Nullstar training from existing full STM sparse data
echo Working directory: %CD%
echo Configuration: %CD%\config.json
echo.

if not exist "training_sparse_stm.bin" goto :data_error

"%NULLSTAR_PYTHON%" -c "import sys, torch; print('Python:', sys.executable); print('PyTorch:', torch.__version__); print('Torch package:', torch.__file__); print('Training device: CPU')"
if errorlevel 1 goto :environment_error

if exist "checkpoint_stm_base.pt" (
  goto :resume_prompt
)
if exist "checkpoint_mid_epoch_stm_base.pt" (
  goto :resume_prompt
)
goto :start_training

:resume_prompt
  echo.
  echo A full-training checkpoint already exists.
  choice /C YN /N /M "Resume that checkpoint? [Y/N] "
  if errorlevel 2 exit /b 0

:start_training

"%NULLSTAR_PYTHON%" run_pipeline.py --start-at train.py
set "result=%errorlevel%"

echo.
echo Pipeline log: %CD%\training_stm_base_pipeline.log
echo Training log: %CD%\training_stm_base.log
if "%result%"=="0" (
  echo Full training completed successfully.
) else (
  echo Full training failed with exit code %result%.
)
pause
exit /b %result%

:data_error
echo ERROR: training_sparse_stm.bin is missing.
pause
exit /b 1

:environment_error
echo ERROR: The CPU Python environment could not be activated or imported.
pause
exit /b 1
