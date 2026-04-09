#!/bin/bash

# MEMORA ONE-COMMAND STARTUP SCRIPT
# For macOS and Linux
# Usage: ./memora_start.sh [options]
# Or just: ./memora_start.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
MEMORY_PATH="${MEMORA_PATH:-./memora_data}"
PORT="${MEMORA_PORT:-11435}"
AUTO_SETUP=true
SHOW_HELP=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            SHOW_HELP=true
            shift
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -m|--memory-path)
            MEMORY_PATH="$2"
            shift 2
            ;;
        --no-auto-setup)
            AUTO_SETUP=false
            shift
            ;;
        *)
            echo "Unknown option: $1"
            SHOW_HELP=true
            shift
            ;;
    esac
done

if [ "$SHOW_HELP" = true ]; then
    cat << 'EOF'
🧠 MEMORA - One-Command Startup

Usage: ./memora_start.sh [OPTIONS]

Options:
  -h, --help              Show this help message
  -p, --port PORT         Use custom port (default: 11435)
  -m, --memory-path PATH  Use custom memory path (default: ./memora_data)
  --no-auto-setup         Don't automatically configure OLLAMA_HOST

Examples:
  ./memora_start.sh                    # Use defaults
  ./memora_start.sh --port 11436       # Use different port
  ./memora_start.sh -m ~/my_memories   # Custom memory location

Environment Variables:
  MEMORA_PATH             Set default memory path
  MEMORA_PORT             Set default port

Requirements:
  - Python 3.11+
  - Poetry (or pip install memora)
  - Ollama running on localhost:11434

First Time Setup:
  1. Install Memora: pip install memora (or poetry install)
  2. Run this script: ./memora_start.sh
  3. In another terminal, use Ollama normally: ollama run llama2
  4. Your memories will be captured automatically!

For help: See COMPLETE_DEMO_GUIDE.md
EOF
    exit 0
fi

echo -e "${BLUE}🚀 MEMORA ONE-COMMAND STARTUP${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# Check if memora command exists
if ! command -v memora &> /dev/null; then
    echo -e "${RED}❌ Memora not found!${NC}"
    echo -e "${YELLOW}Install it with:${NC}"
    echo "  pip install memora"
    echo "  or"
    echo "  poetry install"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION"

# Check if Poetry is being used
if [ -f "pyproject.toml" ]; then
    echo -e "${GREEN}✓${NC} Poetry project detected"
    USE_POETRY=true
else
    USE_POETRY=false
fi

# Check Ollama
if ! nc -z localhost 11434 &> /dev/null; then
    echo -e "${YELLOW}⚠${NC} Ollama not detected on port 11434"
    echo -e "${YELLOW}  Is Ollama running? Start it with: ollama serve${NC}"
    echo -e "${YELLOW}  Continuing anyway...${NC}\n"
else
    echo -e "${GREEN}✓${NC} Ollama detected on port 11434"
fi

# Check port availability
if nc -z localhost "$PORT" &> /dev/null; then
    echo -e "${RED}❌ Port $PORT is already in use!${NC}"
    echo -e "${YELLOW}Options:${NC}"
    echo "  1. Kill the process: lsof -ti:$PORT | xargs kill -9"
    echo "  2. Use a different port: ./memora_start.sh --port 11436"
    exit 1
fi

echo -e "${GREEN}✓${NC} Port $PORT available"

# Create memory directory
mkdir -p "$MEMORY_PATH"
echo -e "${GREEN}✓${NC} Memory path: $MEMORY_PATH"

# Run initialization
echo -e "\n${BLUE}📍 Initializing Memora...${NC}"
if [ "$USE_POETRY" = true ]; then
    poetry run memora init --path "$MEMORY_PATH" 2>/dev/null || true
else
    memora init --path "$MEMORY_PATH" 2>/dev/null || true
fi

# Check spaCy model
echo -e "${BLUE}📖 Checking language model...${NC}"
if python3 -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} spaCy model available"
else
    echo -e "${YELLOW}📥 Downloading spaCy model (one-time, ~12MB)...${NC}"
    python3 -m spacy download en_core_web_sm --quiet || true
fi

# Configure OLLAMA_HOST
if [ "$AUTO_SETUP" = true ]; then
    echo -e "\n${BLUE}🔧 Configuring OLLAMA_HOST...${NC}"
    export OLLAMA_HOST="http://localhost:$PORT"
    echo -e "${GREEN}✓${NC} OLLAMA_HOST=http://localhost:$PORT"
    echo -e "${YELLOW}  (Set for this session. To persist:${NC}"
    echo -e "${YELLOW}   Add to ~/.bashrc or ~/.zshrc: export OLLAMA_HOST=http://localhost:$PORT)${NC}"
fi

# Final info
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ Setup Complete!${NC}\n"

echo -e "${BLUE}📌 NEXT STEPS:${NC}"
echo "  1. Memora is starting on port $PORT..."
echo "  2. In another terminal, use Ollama: ollama run llama2"
echo "  3. Your conversations will be captured automatically!"
echo ""
echo -e "${BLUE}💡 TRY THESE COMMANDS:${NC}"
echo "  memora search \"your topic\"  # Find memories"
echo "  memora when \"today\"          # Time-based search"
echo "  memora stats                  # View statistics"
echo "  memora chat                   # Interactive chat with memory"
echo "  memora branch list            # View all branches"
echo ""
echo -e "${BLUE}📖 LEARN MORE:${NC}"
echo "  See COMPLETE_DEMO_GUIDE.md for full feature list"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Start Memora
echo -e "${GREEN}🌐 Starting Memora proxy...${NC}\n"
if [ "$USE_POETRY" = true ]; then
    poetry run memora start --memory-path "$MEMORY_PATH" --port "$PORT"
else
    memora start --memory-path "$MEMORY_PATH" --port "$PORT"
fi
