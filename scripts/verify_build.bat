@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0verify_build.ps1" %*
