@echo off
setlocal
set SCRIPT_DIR=%~dp0
if "%~1"=="" (
    py "%SCRIPT_DIR%scripts\open_in_sheets.py" "%SCRIPT_DIR%Chicago_Commercial_Market_Sample.xlsx"
) else (
    py "%SCRIPT_DIR%scripts\open_in_sheets.py" "%~1"
)
