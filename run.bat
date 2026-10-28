@echo off
title Finapack Catalog Builder
echo Starting Finapack Catalog Builder...
python run_desktop.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred while launching. Please ensure Python and requirements are installed:
    echo pip install -r requirements.txt
    pause
)
