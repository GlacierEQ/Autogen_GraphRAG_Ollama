@echo off
echo ===================================================
echo Installing All Dependencies for GraphRAG + AutoGen
echo ===================================================
echo.

REM Create virtual environment
echo Creating Python virtual environment...
python -m venv venv
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to create virtual environment.
    echo Make sure Python 3.10+ is installed and in your PATH.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies one by one to better identify issues
echo.
echo Installing core dependencies...
pip install ollama
pip install tiktoken
pip install torch
pip install pyyaml

echo.
echo Installing GraphRAG...
pip install graphrag

echo.
echo Installing AutoGen...
pip install pyautogen[retrievechat]

echo.
echo Installing Chainlit...
pip install chainlit==2.1.1

echo.
echo Installing LiteLLM with proxy support...
pip install litellm[proxy]
pip install apscheduler==3.10.4
pip install gunicorn==22.0.0
pip install cryptography==43.0.0

echo.
echo Installing additional utilities...
pip install marker-pdf
pip install requests

echo.
echo ===================================================
echo Installation complete!
echo.
echo To test your installation, run:
echo   .\simple_test.bat
echo.
echo To activate this environment in the future, run:
echo   venv\Scripts\activate.bat
echo ===================================================
pause
