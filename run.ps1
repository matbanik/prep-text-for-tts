# TTS Text Preprocessor - Launcher Script
# Checks dependencies and launches the application

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  TTS Text Preprocessor GUI" -ForegroundColor Cyan
Write-Host "  Dependency Checker & Launcher" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if command exists
function Test-Command {
    param($Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# Function to check if Python package is installed
function Test-PythonPackage {
    param($Package)
    $result = python -c "import $Package" 2>&1
    return $LASTEXITCODE -eq 0
}

# Check Python installation
Write-Host "[1/6] Checking Python installation..." -ForegroundColor Yellow
if (-not (Test-Command python)) {
    Write-Host "ERROR: Python is not installed or not in PATH!" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://www.python.org/" -ForegroundColor Red
    exit 1
}

$pythonVersion = python --version
Write-Host "  Found: $pythonVersion" -ForegroundColor Green

# Check pip
Write-Host "[2/6] Checking pip installation..." -ForegroundColor Yellow
if (-not (Test-Command pip)) {
    Write-Host "ERROR: pip is not installed!" -ForegroundColor Red
    Write-Host "Please install pip or reinstall Python with pip enabled" -ForegroundColor Red
    exit 1
}

$pipVersion = pip --version
Write-Host "  Found: $pipVersion" -ForegroundColor Green

# Check and install required packages
Write-Host ""
Write-Host "[3/6] Checking required packages..." -ForegroundColor Yellow

$requiredPackages = @(
    @{Name="openai"; ImportName="openai"},
    @{Name="ftfy"; ImportName="ftfy"},
    @{Name="spacy"; ImportName="spacy"}
)

$missingPackages = @()

foreach ($pkg in $requiredPackages) {
    Write-Host "  Checking $($pkg.Name)..." -NoNewline
    if (Test-PythonPackage $pkg.ImportName) {
        Write-Host " Installed" -ForegroundColor Green
    } else {
        Write-Host " ✗ Missing" -ForegroundColor Red
        $missingPackages += $pkg.Name
    }
}

# Install missing packages
if ($missingPackages.Count -gt 0) {
    Write-Host ""
    Write-Host "[4/6] Installing missing packages..." -ForegroundColor Yellow

    foreach ($pkg in $missingPackages) {
        Write-Host "  Installing $pkg..." -ForegroundColor Cyan
        pip install $pkg

        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ERROR: Failed to install $pkg" -ForegroundColor Red
            Write-Host ""
            exit 1
        }
    }

    Write-Host "  All packages installed successfully" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[4/6] All required packages are already installed " -ForegroundColor Green
}

# Check spaCy model
Write-Host ""
Write-Host "[5/6] Checking spaCy language model..." -ForegroundColor Yellow

$spacyModelCheck = python -c "import spacy; spacy.load('en_core_web_sm')" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  spaCy model 'en_core_web_sm' not found. Installing..." -ForegroundColor Cyan
    python -m spacy download en_core_web_sm

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Failed to download spaCy model" -ForegroundColor Red
        Write-Host ""
        exit 1
    }

    Write-Host "  spaCy model installed successfully" -ForegroundColor Green
} else {
    Write-Host "  spaCy model 'en_core_web_sm' is installed" -ForegroundColor Green
}

# Launch the GUI
Write-Host ""
Write-Host "[6/6] Launching TTS Text Preprocessor GUI..." -ForegroundColor Yellow
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Starting application..." -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if GUI file exists
if (-not (Test-Path "tts_preprocessor_gui.py")) {
    Write-Host "ERROR: tts_preprocessor_gui.py not found in current directory!" -ForegroundColor Red
    Write-Host "Please run this script from the repository root directory." -ForegroundColor Red
    Write-Host ""
    exit 1
}

# Launch the GUI
python tts_preprocessor_gui.py

# If GUI exits with error
if ($LASTEXITCODE -ne 0) {
    Write-Host $LASTEXITCODE
}
