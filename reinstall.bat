@echo off
echo ===================================================
echo GraphRAG + AutoGen + Ollama Reinstaller
echo ===================================================
echo.
echo This will reinstall all dependencies and reset the environment.
echo WARNING: This will delete your virtual environment but preserve your documents.
echo.
set /p confirm="Are you sure you want to continue? (y/n): "
if /I "%confirm%" NEQ "y" goto :EOF

echo.
echo Deactivating virtual environment if active...
call deactivate 2>nul

echo.
echo Removing old virtual environment...
if exist venv (
    rmdir /S /Q venv
    echo Old virtual environment removed.
) else (
    echo No existing virtual environment found.
)

echo.
echo Creating new virtual environment...
python -m venv venv
if %ERRORLEVEL% NEQ 0 (
    echo Failed to create virtual environment.
    echo Make sure Python 3.10+ is installed and in your PATH.
    goto :EOF
)

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Installing dependencies...
pip install -r requirements_updated.txt

echo.
echo Installing additional packages...
pip install apscheduler==3.10.4
pip install gunicorn==22.0.0
pip install uvicorn==0.29.0
pip install cryptography==43.0.0
pip install pynacl==1.5.0

echo.
echo ===================================================
echo Reinstallation completed!
echo.
echo To start the application:
echo 1. Make sure Ollama is running
echo 2. Run: launch.bat
echo ===================================================

pause
