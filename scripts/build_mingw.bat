@echo off
set "mode=%~1"
if not defined mode set "mode=all"

powershell.exe -NoProfile -ExecutionPolicy Bypass ^
  -File "%~dp0build_mingw.ps1" -Mode "%mode%"
set "result=%errorlevel%"
pause
exit /b %result%
