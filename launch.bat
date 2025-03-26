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
