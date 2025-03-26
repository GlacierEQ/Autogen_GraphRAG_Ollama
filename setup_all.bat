@echo off
echo ===================================================
echo GraphRAG + AutoGen + Ollama Setup Helper
echo ===================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    goto :EOF
)

REM Create and setup virtual environment
echo Setting up Python virtual environment...
call setup_env.bat

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if Ollama is installed
ollama --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo NOTE: Ollama is not installed or not in PATH.
    echo Please install Ollama from: https://ollama.com/download/windows
    echo After installation, please run this script again.
    echo.
    echo See install_ollama.md for detailed instructions
    echo.
    pause
    goto :EOF
)

echo.
echo Checking Ollama models...
ollama list

echo.
echo Checking if required models are available...
set MODEL_MISSING=0

ollama list | findstr /C:"llama3" >nul
if %ERRORLEVEL% NEQ 0 (
    echo Pulling llama3 model...
    ollama pull llama3
    set MODEL_MISSING=1
)

ollama list | findstr /C:"mistral" >nul
if %ERRORLEVEL% NEQ 0 (
    echo Pulling mistral model...
    ollama pull mistral
    set MODEL_MISSING=1
)

ollama list | findstr /C:"nomic-embed-text" >nul
if %ERRORLEVEL% NEQ 0 (
    echo Pulling nomic-embed-text model...
    ollama pull nomic-embed-text
    set MODEL_MISSING=1
)

if %MODEL_MISSING% EQU 1 (
    echo.
    echo Models have been pulled. Continuing with setup...
)

echo.
echo Initializing GraphRAG environment...
python init_graphrag.py

echo.
echo Building knowledge graph...
python -m graphrag.index --root .

echo.
echo ===================================================
echo Setup completed successfully!
echo ===================================================
echo.
echo To start the application:
echo.
echo 1. Open a new Command Prompt and run:
echo    venv\Scripts\activate.bat
echo    litellm --model ollama_chat/llama3 --port 8000
echo.
echo 2. Open another Command Prompt and run:
echo    venv\Scripts\activate.bat
echo    chainlit run appUI.py
echo.
echo 3. Open your browser to: http://localhost:8000
echo.
echo ===================================================

pause
