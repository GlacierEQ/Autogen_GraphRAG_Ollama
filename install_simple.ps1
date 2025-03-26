# Simple installation script that avoids PowerShell function issues

Write-Host "`n===== Setting Up GraphRAG Environment =====" -ForegroundColor Cyan

# Find Python executable
$pythonCmd = "python"

# Set up virtual environment
Write-Host "`n===== Setting Up Virtual Environment =====" -ForegroundColor Cyan
$venvPath = "venv"
if (-Not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    try {
        & python -m venv $venvPath
        Write-Host "Virtual environment created successfully" -ForegroundColor Green
    }
    catch {
        Write-Host "Error creating virtual environment: $_" -ForegroundColor Red
    }
} else {
    Write-Host "Virtual environment already exists. Skipping creation." -ForegroundColor Yellow
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
if (Test-Path "$venvPath\Scripts\Activate.ps1") {
    & "$venvPath\Scripts\Activate.ps1"
} else {
    Write-Host "Could not find activation script. Manual activation may be required." -ForegroundColor Yellow
}

# Install required Python packages
Write-Host "`n===== Installing Required Python Packages =====" -ForegroundColor Cyan
$requirementsFile = "requirements.txt"
if (Test-Path $requirementsFile) {
    Write-Host "Installing packages from $requirementsFile..." -ForegroundColor Yellow
    try {
        & python -m pip install -r $requirementsFile
        Write-Host "Required packages installed successfully" -ForegroundColor Green
    } catch {
        Write-Host "Failed to install required packages: $_" -ForegroundColor Red
    }
} else {
    Write-Host "Requirements file not found: $requirementsFile" -ForegroundColor Red
}

# Build index
Write-Host "`n===== GraphRAG Index Building =====" -ForegroundColor Cyan
$buildIndex = Read-Host "Do you want to build the GraphRAG index now? This may take a few minutes (y/n)"
if ($buildIndex -eq "y") {
    Write-Host "Building GraphRAG index..." -ForegroundColor Yellow
    
    try {
        & python -m graphrag.index --root .
        Write-Host "GraphRAG index built successfully" -ForegroundColor Green
    } catch {
        Write-Host "Failed to build GraphRAG index: $_" -ForegroundColor Red
    }
} else {
    Write-Host "Skipping index building. You can build it later with: python -m graphrag.index --root ." -ForegroundColor Yellow
}

# Create launcher scripts
Write-Host "`n===== Creating Launcher Scripts =====" -ForegroundColor Cyan

$launchScript = @"
@echo off
echo ===================================================
echo GraphRAG + AutoGen + Ollama Application Launcher
echo ===================================================
echo.

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment not found, using system Python...
)

REM Start LiteLLM proxy server
echo.
echo Starting LiteLLM proxy server...
start "LiteLLM Proxy" cmd /c "title LiteLLM Proxy && python -m litellm --model ollama_chat/llama3 --port 8000"

REM Start Flask server
echo.
echo Starting Flask server...
start "Flask Server" cmd /c "title Flask Server && python appUI_pro.py"

echo.
echo Waiting for servers to start...
timeout /t 5 /nobreak > nul

REM Start Chainlit application
echo.
echo Starting Chainlit application...
start "Chainlit Application" cmd /c "title Chainlit Application && python -m chainlit run appUI_pro.py"

echo.
echo ===================================================
echo Open your browser to access the application
echo Your browser should automatically open to http://localhost:8000
echo.
echo Close this window to shut down all servers when done.
echo ===================================================
echo.
pause
"@

$launchScriptPath = "launch.bat"
$launchScript | Out-File -FilePath $launchScriptPath -Encoding ascii
Write-Host "Created launcher script: $launchScriptPath" -ForegroundColor Green

# Final message
Write-Host "`n===== Installation Complete =====" -ForegroundColor Cyan
Write-Host "The GraphRAG + AutoGen + Ollama environment has been successfully set up!" -ForegroundColor Green
Write-Host ""
Write-Host "To start the application:" -ForegroundColor White
Write-Host "1. Open Command Prompt in this directory" -ForegroundColor White
Write-Host "2. Run: launch.bat" -ForegroundColor White
Write-Host ""
Write-Host "This will start both the LiteLLM proxy server and the Chainlit UI." -ForegroundColor White
Write-Host "You can then access the application at: http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "Enjoy using GraphRAG + AutoGen + Ollama!" -ForegroundColor Green
