# MEMORA ONE-COMMAND STARTUP SCRIPT FOR WINDOWS (PowerShell)
# Usage: .\memora_start.ps1 [options]
# Or just: .\memora_start.ps1
#
# If you get "execution policy" error, run:
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

param(
    [string]$MemoryPath = $env:MEMORA_PATH ?? "memora_data",
    [int]$Port = $env:MEMORA_PORT ?? 11435,
    [switch]$NoAutoSetup,
    [switch]$Help
)

# Colors
$Green = "`e[92m"
$Red = "`e[91m"
$Yellow = "`e[93m"
$Blue = "`e[94m"
$Reset = "`e[0m"

function Show-Help {
    Clear-Host
    Write-Host @"
    
    🧠 MEMORA - One-Command Startup for Windows (PowerShell)
    
    Usage: .\memora_start.ps1 [OPTIONS]
    
    Options:
      -Help                    Show this help message
      -Port <PORT>             Use custom port (default: 11435)
      -MemoryPath <PATH>       Use custom memory path (default: memora_data)
      -NoAutoSetup             Don't automatically configure OLLAMA_HOST
    
    Examples:
      .\memora_start.ps1                           # Use defaults
      .\memora_start.ps1 -Port 11436               # Use different port
      .\memora_start.ps1 -MemoryPath C:\my_memories  # Custom location
    
    Requirements:
      - Python 3.11+
      - Memora installed (pip install memora)
      - Ollama running on localhost:11434
    
    First Time Setup:
      1. Install Memora: pip install memora
      2. Run this script: .\memora_start.ps1
      3. In another PowerShell, use Ollama: ollama run llama2
      4. Your memories will be captured automatically!
    
    For help: See COMPLETE_DEMO_GUIDE.md
    
"@
    exit 0
}

if ($Help) {
    Show-Help
}

Clear-Host
Write-Host "${Blue}🚀 MEMORA ONE-COMMAND STARTUP${Reset}"
Write-Host "${Blue}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${Reset}`n"

# Check if memora command exists
$MemoraCommand = Get-Command memora -ErrorAction SilentlyContinue
if (-not $MemoraCommand) {
    Write-Host "${Red}❌ Memora not found!${Reset}"
    Write-Host "${Yellow}Install it with:${Reset}"
    Write-Host "  pip install memora"
    exit 1
}

# Check Python version
$PythonVersion = (python --version 2>&1 | Select-Object -First 1) -replace "Python "
Write-Host "${Green}✓${Reset} Python $PythonVersion"

# Check if Poetry is being used
if (Test-Path "pyproject.toml") {
    Write-Host "${Green}✓${Reset} Poetry project detected"
    $UsePoetry = $true
} else {
    $UsePoetry = $false
}

# Check Ollama
try {
    $OllamaCheck = [Net.Sockets.TcpClient]::new()
    $OllamaCheck.Connect("localhost", 11434)
    if ($OllamaCheck.Connected) {
        Write-Host "${Green}✓${Reset} Ollama detected on port 11434"
        $OllamaCheck.Close()
    }
} catch {
    Write-Host "${Yellow}⚠${Reset} Ollama not detected on port 11434"
    Write-Host "${Yellow}  Is Ollama running? Start it with: ollama serve${Reset}"
    Write-Host "${Yellow}  Continuing anyway...${Reset}`n"
}

# Check port availability
try {
    $PortCheck = [Net.Sockets.TcpClient]::new()
    $PortCheck.Connect("localhost", $Port)
    if ($PortCheck.Connected) {
        Write-Host "${Red}❌ Port $Port is already in use!${Reset}"
        Write-Host "${Yellow}Options:${Reset}"
        Write-Host "  1. Use a different port: .\memora_start.ps1 -Port 11436"
        Write-Host "  2. Find what's using it: netstat -ano | findstr :$Port"
        $PortCheck.Close()
        exit 1
    }
} catch {
    # Port is available
}

Write-Host "${Green}✓${Reset} Port $Port available"

# Create memory directory
if (-not (Test-Path $MemoryPath)) {
    New-Item -ItemType Directory -Path $MemoryPath -Force | Out-Null
}
Write-Host "${Green}✓${Reset} Memory path: $MemoryPath"

# Run initialization
Write-Host "`n${Blue}📍 Initializing Memora...${Reset}"
if ($UsePoetry) {
    poetry run memora init --path "$MemoryPath" 2>$null
} else {
    memora init --path "$MemoryPath" 2>$null
}

# Check spaCy model
Write-Host "${Blue}📖 Checking language model...${Reset}"
$SpacyCheck = python -c "import spacy; spacy.load('en_core_web_sm')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "${Green}✓${Reset} spaCy model available"
} else {
    Write-Host "${Yellow}📥 Downloading spaCy model (one-time, ~12MB)...${Reset}"
    python -m spacy download en_core_web_sm
}

# Configure OLLAMA_HOST
if (-not $NoAutoSetup) {
    Write-Host "`n${Blue}🔧 Configuring OLLAMA_HOST...${Reset}"
    [Environment]::SetEnvironmentVariable("OLLAMA_HOST", "http://localhost:$Port", "User")
    Write-Host "${Green}✓${Reset} OLLAMA_HOST=http://localhost:$Port"
    Write-Host "${Yellow}  (Set system-wide for future sessions)${Reset}"
}

# Final info
Write-Host "`n${Blue}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${Reset}"
Write-Host "${Green}✓ Setup Complete!${Reset}`n"

Write-Host "${Blue}📌 NEXT STEPS:${Reset}"
Write-Host "  1. Memora is starting on port $Port..."
Write-Host "  2. In another PowerShell, use Ollama: ollama run llama2"
Write-Host "  3. Your conversations will be captured automatically!"
Write-Host ""
Write-Host "${Blue}💡 TRY THESE COMMANDS:${Reset}"
Write-Host '  memora search "your topic"  # Find memories'
Write-Host '  memora when "today"         # Time-based search'
Write-Host "  memora stats                # View statistics"
Write-Host "  memora chat                 # Interactive chat with memory"
Write-Host "  memora branch list          # View all branches"
Write-Host ""
Write-Host "${Blue}📖 LEARN MORE:${Reset}"
Write-Host "  See COMPLETE_DEMO_GUIDE.md for full feature list"
Write-Host ""
Write-Host "${Blue}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${Reset}`n"

# Start Memora
Write-Host "${Green}🌐 Starting Memora proxy...${Reset}`n"
if ($UsePoetry) {
    poetry run memora start --memory-path "$MemoryPath" --port $Port
} else {
    memora start --memory-path "$MemoryPath" --port $Port
}
