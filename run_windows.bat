@echo off
echo ===================================================
echo GraphRAG + AutoGen + Ollama Application Launcher
echo ===================================================
echo.

REM Activate virtual environment if it exists, otherwise use system Python
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment not found, using system Python...
    echo This may cause issues if dependencies aren't installed globally.
    echo Run setup_env.bat to create a virtual environment.
    pause
)

REM Check for required directories
if not exist "output" (
    echo GraphRAG index not found. Initializing environment...
    python init_graphrag.py
    
    echo Indexing documents...
    python -m graphrag.index --root .
    
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo Error creating GraphRAG index. Please check the error message above.
        pause
        exit /b 1
    )
)

REM Start LiteLLM proxy server
echo.
echo Starting LiteLLM proxy server on port 8000...
start "LiteLLM Proxy" cmd /c "title LiteLLM Proxy && python -m litellm --model ollama_chat/llama3 --port 8000"

echo.
echo Waiting for LiteLLM server to start (5 seconds)...
timeout /t 5 /nobreak > nul

REM Start Chainlit application
echo.
echo Starting Chainlit application...
start "Chainlit Application" cmd /c "title Chainlit Application && python -m chainlit run appUI.py"

echo.
echo ===================================================
echo Your browser should open soon to access the application.
echo If it doesn't, open http://localhost:8000 manually.
echo.
echo Close this window to shut down both servers when done.
echo ===================================================
echo.

REM Wait for user to press Ctrl+C
echo Press Ctrl+C to shut down all servers and exit.
pause > nul
