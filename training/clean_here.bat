@echo off
setlocal EnableExtensions
set "cleanup_failed=0"

cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Unable to enter the training directory.
  pause
  exit /b 1
)

echo.
echo Nullstar training artifact cleaner
echo Directory: %CD%
echo.
echo   L  Remove legacy Set 006 model and checkpoint artifacts
echo   F  Reset the current full STM training state
echo   S  Remove the isolated 1M smoke-test artifacts
echo   D  Remove full STM shuffled and sparse derived data
echo   Q  Quit without changing anything
echo.

choice /C LFSDQ /N /M "Select L, F, S, D, or Q: "
if errorlevel 5 goto :quit
if errorlevel 4 goto :derived
if errorlevel 3 goto :smoke
if errorlevel 2 goto :full
goto :legacy

:legacy
echo.
echo The following legacy names will be removed when present:
echo   best_model.pt
echo   checkpoint.pt
echo   checkpoint_mid_epoch.pt
echo   network.bin
echo   network_epoch_*.bin
echo   network_best_epoch_*.bin
echo   training.log
call :confirm || goto :quit

call :remove "best_model.pt"
call :remove "best_model.pt.tmp"
call :remove "checkpoint.pt"
call :remove "checkpoint.pt.tmp"
call :remove "checkpoint_mid_epoch.pt"
call :remove "checkpoint_mid_epoch.pt.tmp"
call :remove "network.bin"
call :remove "network.bin.tmp"
call :remove "network_epoch_*.bin"
call :remove "network_epoch_*.bin.tmp"
call :remove "network_best_epoch_*.bin"
call :remove "network_best_epoch_*.bin.tmp"
call :remove "training.log"
goto :complete

:full
echo.
echo This resets the current full STM model, checkpoints, networks, and log.
echo Prepared shuffled and sparse data will be preserved.
call :confirm || goto :quit

call :remove "best_model_stm_base.pt"
call :remove "best_model_stm_base.pt.tmp"
call :remove "checkpoint_stm_base.pt"
call :remove "checkpoint_stm_base.pt.tmp"
call :remove "checkpoint_mid_epoch_stm_base.pt"
call :remove "checkpoint_mid_epoch_stm_base.pt.tmp"
call :remove "network_stm_base.bin"
call :remove "network_stm_base.bin.tmp"
call :remove "network_stm_base_epoch_*.bin"
call :remove "network_stm_base_epoch_*.bin.tmp"
call :remove "training_stm_base.log"
goto :complete

:smoke
echo.
echo This removes only artifacts beneath the smoke directory.
call :confirm || goto :quit

call :remove "smoke\best_model_stm_smoke_1m.pt"
call :remove "smoke\best_model_stm_smoke_1m.pt.tmp"
call :remove "smoke\checkpoint_stm_smoke_1m.pt"
call :remove "smoke\checkpoint_stm_smoke_1m.pt.tmp"
call :remove "smoke\checkpoint_mid_epoch_stm_smoke_1m.pt"
call :remove "smoke\checkpoint_mid_epoch_stm_smoke_1m.pt.tmp"
call :remove "smoke\network_stm_smoke_1m.bin"
call :remove "smoke\network_stm_smoke_1m.bin.tmp"
call :remove "smoke\network_stm_smoke_1m_epoch_*.bin"
call :remove "smoke\network_stm_smoke_1m_epoch_*.bin.tmp"
call :remove "smoke\training_sparse_stm_smoke_1m.bin"
call :remove "smoke\training_stm_smoke_1m.log"
goto :complete

:derived
echo.
echo WARNING: This removes the expensive full STM preprocessing outputs:
echo   training_shuffled_stm.txt
echo   training_sparse_stm.bin
echo They will have to be rebuilt before the next full training run.
call :confirm || goto :quit

call :remove "training_shuffled_stm.txt"
call :remove "training_sparse_stm.bin"
goto :complete

:confirm
choice /C YN /N /M "Continue? [Y/N] "
if errorlevel 2 exit /b 1
exit /b 0

:remove
if exist "%~1" (
  echo Removing %~1
  del /Q "%~1"
  if exist "%~1" (
    echo ERROR: Failed to remove %~1
    set "cleanup_failed=1"
    exit /b 1
  )
)
exit /b 0

:complete
echo.
if "%cleanup_failed%"=="1" (
  echo Cleanup finished with one or more errors.
  echo Review the messages above; files that could not be removed remain intact.
  pause
  exit /b 1
)
echo Selected training artifacts removed.
echo Corpora, manifests, configurations, and unselected experiments remain.
pause
exit /b 0

:quit
echo.
echo No additional files were removed.
exit /b 0
