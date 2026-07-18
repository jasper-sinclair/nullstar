@echo off
setlocal

if "%~1"=="" goto usage
if "%~2"=="" goto usage

python split_training_txt.py "%~1" "%~2"
set "RESULT=%ERRORLEVEL%"
pause
exit /b %RESULT%

:usage
echo Usage: %~nx0 INPUT_FILE LINES_PER_PART
echo Example: %~nx0 training.txt 10000000
pause
exit /b 2
