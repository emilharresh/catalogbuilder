@echo off
title Build Standalone Executable
echo ============================================================
echo   Building Finapack Catalog Builder Standalone Executable
echo ============================================================
echo.
pyinstaller --clean FinapackCatalogBuilder.spec
if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Build complete! Executable is located in dist\FinapackCatalogBuilder\
) else (
    echo.
    echo [ERROR] Build failed. Ensure PyInstaller is installed: pip install pyinstaller
)
pause
