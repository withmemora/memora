@echo off
REM MEMORA VIDEO RECORDING - COMPLETE SETUP SCRIPT (Windows)
REM Run this BEFORE recording to ensure clean slate

echo.
echo === MEMORA VIDEO RECORDING SETUP ===
echo.

REM Step 1: Clean all old data
echo [Step 1] Cleaning old data...
if exist memora_data (
    rmdir /s /q memora_data
    echo Deleted memora_data
)
if exist test_demo (
    rmdir /s /q test_demo
    echo Deleted test_demo
)
echo [OK] Old data cleaned
echo.

REM Step 2: Verify directory structure
echo [Step 2] Verifying project structure...
if exist pyproject.toml (
    echo [OK] pyproject.toml found
) else (
    echo [ERROR] pyproject.toml not found!
    pause
    exit /b 1
)

if exist src\memora (
    echo [OK] src\memora directory found
) else (
    echo [ERROR] src\memora directory not found!
    pause
    exit /b 1
)
echo.

REM Step 3: Verify poetry installation
echo [Step 3] Checking Poetry...
where poetry > nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Poetry is installed
    poetry --version
) else (
    echo [ERROR] Poetry not installed!
    echo Install with: pip install poetry
    pause
    exit /b 1
)
echo.

REM Step 4: Check project
echo [Step 4] Checking project...
poetry check > nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Project dependencies are valid
) else (
    echo [WARNING] Run 'poetry install' to ensure dependencies
)
echo.

REM Step 5: Final confirmation
echo.
echo === SETUP COMPLETE ===
echo.
echo NEXT STEPS FOR RECORDING:
echo.
echo Terminal 1 (Ollama Server):
echo   ^> ollama serve
echo.
echo Terminal 2 (Memora Proxy):
echo   ^> cd "Z:\Open Source\FOSS HACK 26\Memora"
echo   ^> poetry run memora proxy start
echo.
echo Terminal 3 (Demo - follow FOSS_HACK_DEMO.md):
echo   ^> cd "Z:\Open Source\FOSS HACK 26\Memora"
echo   ^> poetry run memora init
echo   ^> poetry run memora chat --model llama3.2:1b
echo.
echo All data is clean and ready for recording!
echo.
pause
