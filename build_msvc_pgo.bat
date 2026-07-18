@echo off
setlocal

powershell.exe -NoProfile -ExecutionPolicy Bypass ^
  -File "%~dp0build_msvc_pgo.ps1"

set "BUILD_RESULT=%ERRORLEVEL%"

echo.
if not "%BUILD_RESULT%"=="0" (
    echo MSVC PGO build failed with exit code %BUILD_RESULT%.
) else (
    echo MSVC PGO build completed successfully.
)

pause
exit /b %BUILD_RESULT%
