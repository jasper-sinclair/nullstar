@echo off
if "%~1"=="" (
  echo Usage:
  echo   prepare_dev_build.bat -Summary "Description" [-NetworkFile "network.bin"]
  echo.
  echo See docs\DEVELOPMENT_BUILDS.md for the complete workflow.
  pause
  exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass ^
  -File "%~dp0prepare_dev_build.ps1" %*
set "result=%errorlevel%"
pause
exit /b %result%
