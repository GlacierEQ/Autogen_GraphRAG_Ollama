@echo off
echo Installing required Python packages...
pip install -r requirements_updated.txt

echo Checking for Ollama installation...
where ollama >nul 2>nul
if %errorlevel% neq 0 (
    echo Ollama is not installed. Please install it from https://ollama.com.
)

echo Checking for GraphRAG installation...
where graphrag >nul 2>nul
if %errorlevel% neq 0 (
    echo GraphRAG is not installed. Please install it as per the documentation.
)

echo Installation complete. Please ensure all dependencies are correctly installed.
pause
