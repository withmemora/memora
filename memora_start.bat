@echo off
REM MEMORA ONE-COMMAND STARTUP SCRIPT FOR WINDOWS
REM Usage: memora_start.bat [options]
REM Or just: memora_start.bat

setlocal enabledelayedexpansion

REM Colors (Windows 10+)
set GREEN=[92m
set RED=[91m
set YELLOW=[93m
set BLUE=[94m
set RESET=[0m

REM Default values
set MEMORY_PATH=%MEMORA_PATH%
if "!MEMORY_PATH!"=="" set MEMORY_PATH=memora_data
set PORT=%MEMORA_PORT%
if "!PORT!"=="" set PORT=11435
set AUTO_SETUP=true
set SHOW_HELP=false

REM Parse arguments
:parse_args
if "%1"=="" goto args_done
if "%1"=="-h" goto show_help
if "%1"=="--help" goto show_help
if "%1"=="-p" (
    set PORT=%2
    shift
    shift
    goto parse_args
)
if "%1"=="--port" (
    set PORT=%2
    shift
    shift
    goto parse_args
)
if "%1"=="-m" (
    set MEMORY_PATH=%2
    shift
    shift
    goto parse_args
)
if "%1"=="--memory-path" (
    set MEMORY_PATH=%2
    shift
    shift
    goto parse_args
)
if "%1"=="--no-auto-setup" (
    set AUTO_SETUP=false
    shift
    goto parse_args
)
shift
goto parse_args

:show_help
cls
echo.
echo     🧠 MEMORA - One-Command Startup for Windows
echo.
echo     Usage: memora_start.bat [OPTIONS]
echo.
echo     Options:
echo       -h, --help              Show this help message
echo       -p, --port PORT         Use custom port (default: 11435)
echo       -m, --memory-path PATH  Use custom memory path (default: memora_data)
echo       --no-auto-setup         Don't automatically configure OLLAMA_HOST
echo.
echo     Examples:
echo       memora_start.bat                    # Use defaults
echo       memora_start.bat --port 11436       # Use different port
echo       memora_start.bat -m C:\my_memories  # Custom memory location
echo.
echo     Requirements:
echo       - Python 3.11+
echo       - Memora installed (pip install memora)
echo       - Ollama running on localhost:11434
echo.
echo     First Time Setup:
echo       1. Install Memora: pip install memora
echo       2. Run this script: memora_start.bat
echo       3. In another PowerShell, use Ollama: ollama run llama2
echo       4. Your memories will be captured automatically!
echo.
echo     For help: See COMPLETE_DEMO_GUIDE.md
echo.
exit /b 0

:args_done
cls
echo.
echo     !BLUE!🚀 MEMORA ONE-COMMAND STARTUP!RESET!
echo     !BLUE!━━━━━━━━━━━━━━━━━━━━━━━━━━━━━!RESET!
echo.

REM Check if memora command exists
where memora >nul 2>nul
if errorlevel 1 (
    echo     !RED!❌ Memora not found!!RESET!
    echo     !YELLOW!Install it with:!RESET!
    echo       pip install memora
    echo.
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo     !GREEN!✓!RESET! Python !PYTHON_VERSION!

REM Check if Poetry is being used
if exist "pyproject.toml" (
    echo     !GREEN!✓!RESET! Poetry project detected
    set USE_POETRY=true
) else (
    set USE_POETRY=false
)

REM Check Ollama
netstat -ano 2>nul | findstr ":11434 " >nul
if errorlevel 1 (
    echo     !YELLOW!⚠!RESET! Ollama not detected on port 11434
    echo     !YELLOW!  Is Ollama running? Start it with: ollama serve!RESET!
    echo     !YELLOW!  Continuing anyway...!RESET!
    echo.
) else (
    echo     !GREEN!✓!RESET! Ollama detected on port 11434
)

REM Check port availability
netstat -ano 2>nul | findstr ":%PORT% " >nul
if not errorlevel 1 (
    echo     !RED!❌ Port %PORT% is already in use!!RESET!
    echo     !YELLOW!Options:!RESET!
    echo       1. Use a different port: memora_start.bat --port 11436
    echo       2. Find what's using it: netstat -ano | findstr :%PORT%
    echo.
    pause
    exit /b 1
)

echo     !GREEN!✓!RESET! Port %PORT% available

REM Create memory directory
if not exist "!MEMORY_PATH!" mkdir "!MEMORY_PATH!"
echo     !GREEN!✓!RESET! Memory path: !MEMORY_PATH!

REM Run initialization
echo.
echo     !BLUE!📍 Initializing Memora...!RESET!
if "!USE_POETRY!"=="true" (
    poetry run memora init --path "!MEMORY_PATH!" 2>nul
) else (
    memora init --path "!MEMORY_PATH!" 2>nul
)

REM Check spaCy model
echo     !BLUE!📖 Checking language model...!RESET!
python -c "import spacy; spacy.load('en_core_web_sm')" >nul 2>&1
if errorlevel 1 (
    echo     !YELLOW!📥 Downloading spaCy model (one-time, ~12MB)...!RESET!
    python -m spacy download en_core_web_sm
) else (
    echo     !GREEN!✓!RESET! spaCy model available
)

REM Configure OLLAMA_HOST
if "!AUTO_SETUP!"=="true" (
    echo.
    echo     !BLUE!🔧 Configuring OLLAMA_HOST...!RESET!
    setx OLLAMA_HOST http://localhost:%PORT% >nul 2>&1
    echo     !GREEN!✓!RESET! OLLAMA_HOST=http://localhost:%PORT%
    echo     !YELLOW!  (Set system-wide for future sessions)!RESET!
)

REM Final info
echo.
echo     !BLUE!━━━━━━━━━━━━━━━━━━━━━━━━━━━━━!RESET!
echo     !GREEN!✓ Setup Complete!!RESET!
echo.
echo     !BLUE!📌 NEXT STEPS:!RESET!
echo       1. Memora is starting on port %PORT%...
echo       2. In another PowerShell, use Ollama: ollama run llama2
echo       3. Your conversations will be captured automatically!
echo.
echo     !BLUE!💡 TRY THESE COMMANDS:!RESET!
echo       memora search "your topic"  # Find memories
echo       memora when "today"         # Time-based search
echo       memora stats                # View statistics
echo       memora chat                 # Interactive chat with memory
echo       memora branch list          # View all branches
echo.
echo     !BLUE!📖 LEARN MORE:!RESET!
echo       See COMPLETE_DEMO_GUIDE.md for full feature list
echo.
echo     !BLUE!━━━━━━━━━━━━━━━━━━━━━━━━━━━━━!RESET!
echo.

REM Start Memora
echo     !GREEN!🌐 Starting Memora proxy...!RESET!
echo.
if "!USE_POETRY!"=="true" (
    poetry run memora start --memory-path "!MEMORY_PATH!" --port %PORT%
) else (
    memora start --memory-path "!MEMORY_PATH!" --port %PORT%
)

endlocal
pause
