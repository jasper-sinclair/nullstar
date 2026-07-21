@echo off
set "NULLSTAR_TRAIN_DIR=C:\DEV\NULLSTAR-TRAINING\TRAIN"
if not exist "%NULLSTAR_TRAIN_DIR%\nnue_gpu_env\Scripts\python.exe" set "NULLSTAR_TRAIN_DIR=C:\DEV\NULLSTAR-TRAIN\TRAINING"
cd /d "%NULLSTAR_TRAIN_DIR%"
if errorlevel 1 (
  echo ERROR: Training directory not found: %NULLSTAR_TRAIN_DIR%
  exit /b 1
)
set "VIRTUAL_ENV=%CD%\nnue_gpu_env"
set "NULLSTAR_PYTHON=%VIRTUAL_ENV%\Scripts\python.exe"
if not exist "%NULLSTAR_PYTHON%" (
  echo ERROR: GPU Python environment not found: %NULLSTAR_PYTHON%
  exit /b 1
)
set "PYTHONHOME="
set "PYTHONPATH="
set "PATH=%VIRTUAL_ENV%\Scripts;%PATH%"
exit /b 0
