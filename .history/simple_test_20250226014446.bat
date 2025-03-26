@echo off
echo ===================================================
echo GraphRAG + AutoGen Simple Test Script
echo ===================================================
echo.

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo No virtual environment found. Using system Python...
)

echo.
echo Checking Python installation...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH.
    pause
    exit /b 1
)

echo.
echo Checking Ollama installation...
ollama --version
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Ollama is not installed or not in PATH.
    echo Please install Ollama from https://ollama.com/download/windows
    pause
    exit /b 1
)

echo.
echo Testing dependencies...
echo.
echo 1. Testing GraphRAG...
python -c "import graphrag; print(f'GraphRAG version: {graphrag.__version__}')"

echo.
echo 2. Testing AutoGen...
python -c "import autogen; print(f'AutoGen version: {autogen.__version__}')"

echo.
echo 3. Testing Chainlit...
python -c "import chainlit; print(f'Chainlit version: {chainlit.__version__}')"

echo.
echo 4. Testing LiteLLM...
python -c "import litellm; print(f'LiteLLM version: {litellm.__version__}')"

echo.
echo ===================================================
echo If all tests passed, your environment is correctly set up.
echo If any errors occurred, please fix those dependencies.
echo.
echo Next steps:
echo 1. Run "python init_graphrag.py" to initialize GraphRAG
echo 2. Run ".\run_windows.bat" to start the application
echo ===================================================
pause
