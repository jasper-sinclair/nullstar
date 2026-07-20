@echo off
cd /d C:\DEV\NULLSTAR-TRAIN\TRAINING
set "VIRTUAL_ENV=%CD%\nnue_cpu_env"
set "NULLSTAR_PYTHON=%VIRTUAL_ENV%\Scripts\python.exe"
if not exist "%NULLSTAR_PYTHON%" (
  echo ERROR: CPU Python environment not found: %NULLSTAR_PYTHON%
  exit /b 1
)
set "PYTHONHOME="
set "PYTHONPATH="
set "PATH=%VIRTUAL_ENV%\Scripts;%PATH%"
exit /b 0
