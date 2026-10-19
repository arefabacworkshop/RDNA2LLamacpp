@echo off
setlocal
title RDNA2LLamacpp 1-Click Builder & Updater

cd /d "%~dp0"
echo ========================================================
echo RDNA2LLamacpp - 1-Click Build & Update
echo ========================================================
echo.

python build_rdna2.py %*
if errorlevel 1 (
    echo.
    echo ========================================================
    echo [ERROR] Build failed! Check the output above.
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo [OK] Completed successfully!
    echo ========================================================
)

echo.
pause
