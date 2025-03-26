# ...existing code...

# Build index
$buildIndex = Read-Host "Do you want to build the GraphRAG index now? This may take a few minutes (y/n)"
if ($buildIndex -eq "y") {
    Write-Output "Building GraphRAG index..."
    
    try {
        &$pythonCmd -m graphrag.index --root .
        Write-Success "GraphRAG index built successfully"
    } catch {
        Write-Error "Failed to build GraphRAG index: $_"
    }
} else {
    Write-Output "Skipping index building. You can build it later with: python -m graphrag.index --root ."
}

# Create launcher scripts
Write-Header "Creating Launcher Scripts"

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

echo.
echo Waiting for LiteLLM server to start...
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
Write-Success "Created launcher script: $launchScriptPath"

# Final message
Write-Header "Installation Complete"
Write-Output "The GraphRAG + AutoGen + Ollama environment has been successfully set up!"
Write-Output ""
Write-Output "To start the application:"
Write-Output "1. Open Command Prompt in this directory"
Write-Output "2. Run: launch.bat"
Write-Output ""
Write-Output "This will start both the LiteLLM proxy server and the Chainlit UI."
Write-Output "You can then access the application at: http://localhost:8000"
Write-Output ""
Write-Output "Enjoy using GraphRAG + AutoGen + Ollama!"

# Restore original console colors
(Get-Host).UI.RawUI.ForegroundColor = $originalForeground
(Get-Host).UI.RawUI.BackgroundColor = $originalBackground
