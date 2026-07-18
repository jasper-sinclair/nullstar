@echo off
setlocal

echo This removes local checkpoints, epoch networks, and training.log from:
echo %CD%
choice /C YN /N /M "Continue? [Y/N] "
if errorlevel 2 exit /b 0

del /q network_best_epoch_*.bin 2>nul
del /q *.pt 2>nul
del /q training.log 2>nul

echo Training artifacts removed.
