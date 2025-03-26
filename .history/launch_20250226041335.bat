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

REM Check if directories and files exist
if not exist "output" (
    echo GraphRAG index not found. Initializing...
    python init_graphrag.py
    
    echo Building GraphRAG index...
    python -m graphrag.index --root .
    
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo Error initializing GraphRAG. Please check the error message above.
        pause
        exit /b 1
    )
)

REM Check if Ollama is running
echo Checking if Ollama is running...
curl -s http://localhost:11434/api/version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Ollama service does not appear to be running.
    echo Please start Ollama and make sure the required models are pulled:
    echo   - llama3
    echo   - mistral
    echo   - nomic-embed-text
    echo.
    set /p continue="Continue anyway? (y/n): "
    if /I "%continue%" NEQ "y" exit /b 1
)

REM Start LiteLLM proxy server
echo.
echo Starting LiteLLM proxy server...
start "LiteLLM Proxy" cmd /c "title LiteLLM Proxy && python -m litellm --model ollama_chat/llama3 --port 8000"

echo.
echo Waiting for LiteLLM server to start...
timeout /t 5 /nobreak > nul

REM Check if LiteLLM proxy is running
curl -s http://localhost:8000/health >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: LiteLLM proxy does not appear to be running.
    echo This might be due to missing dependencies or configuration issues.
    echo You can try running:
    echo   pip install 'litellm[proxy]' --upgrade
    echo.
    set /p continue="Continue anyway? (y/n): "
    if /I "%continue%" NEQ "y" exit /b 1
)

REM Start Chainlit application with professional UI
echo.
echo Starting Chainlit application with professional UI...
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
