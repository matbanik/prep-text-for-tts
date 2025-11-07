#!/bin/bash
# TTS Text Preprocessor - Launcher Script (Linux/macOS)
# Checks dependencies and launches the application

echo "=========================================="
echo "  TTS Text Preprocessor GUI"
echo "  Dependency Checker & Launcher"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Python package is installed
package_installed() {
    python3 -c "import $1" 2>/dev/null
    return $?
}

# Check Python installation
echo -e "${YELLOW}[1/6] Checking Python installation...${NC}"
if ! command_exists python3; then
    echo -e "${RED}ERROR: Python 3 is not installed!${NC}"
    echo -e "${RED}Please install Python 3.8+ from https://www.python.org/${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}  ✓ Found: $PYTHON_VERSION${NC}"

# Check pip
echo ""
echo -e "${YELLOW}[2/6] Checking pip installation...${NC}"
if ! command_exists pip3 && ! command_exists pip; then
    echo -e "${RED}ERROR: pip is not installed!${NC}"
    echo -e "${RED}Please install pip or reinstall Python with pip enabled${NC}"
    exit 1
fi

PIP_CMD="pip3"
if ! command_exists pip3; then
    PIP_CMD="pip"
fi

PIP_VERSION=$($PIP_CMD --version)
echo -e "${GREEN}  ✓ Found: $PIP_VERSION${NC}"

# Check and install required packages
echo ""
echo -e "${YELLOW}[3/6] Checking required packages...${NC}"

REQUIRED_PACKAGES=("openai" "ftfy" "spacy")
MISSING_PACKAGES=()

for pkg in "${REQUIRED_PACKAGES[@]}"; do
    echo -n "  Checking $pkg..."
    if package_installed "$pkg"; then
        echo -e " ${GREEN}✓ Installed${NC}"
    else
        echo -e " ${RED}✗ Missing${NC}"
        MISSING_PACKAGES+=("$pkg")
    fi
done

# Install missing packages
if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}[4/6] Installing missing packages...${NC}"

    for pkg in "${MISSING_PACKAGES[@]}"; do
        echo -e "${CYAN}  Installing $pkg...${NC}"
        $PIP_CMD install "$pkg"

        if [ $? -ne 0 ]; then
            echo -e "${RED}  ERROR: Failed to install $pkg${NC}"
            exit 1
        fi
    done

    echo -e "${GREEN}  ✓ All packages installed successfully${NC}"
else
    echo ""
    echo -e "${GREEN}[4/6] All required packages are already installed ✓${NC}"
fi

# Check spaCy model
echo ""
echo -e "${YELLOW}[5/6] Checking spaCy language model...${NC}"

if ! python3 -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null; then
    echo -e "${CYAN}  spaCy model 'en_core_web_sm' not found. Installing...${NC}"
    python3 -m spacy download en_core_web_sm

    if [ $? -ne 0 ]; then
        echo -e "${RED}  ERROR: Failed to download spaCy model${NC}"
        exit 1
    fi

    echo -e "${GREEN}  ✓ spaCy model installed successfully${NC}"
else
    echo -e "${GREEN}  ✓ spaCy model 'en_core_web_sm' is installed${NC}"
fi

# Launch the GUI
echo ""
echo -e "${YELLOW}[6/6] Launching TTS Text Preprocessor GUI...${NC}"
echo ""
echo "=========================================="
echo "  Starting application..."
echo "=========================================="
echo ""

# Check if GUI file exists
if [ ! -f "tts_preprocessor_gui.py" ]; then
    echo -e "${RED}ERROR: tts_preprocessor_gui.py not found in current directory!${NC}"
    echo -e "${RED}Please run this script from the repository root directory.${NC}"
    exit 1
fi

# Launch the GUI
python3 tts_preprocessor_gui.py

# Check exit code
if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}Application exited with error code: $?${NC}"
    echo ""
fi
