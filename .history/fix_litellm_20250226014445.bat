@echo off
echo ===================================================
echo Fixing LiteLLM Dependency Issues
echo ===================================================
echo.

REM Activate virtual environment if it exists, otherwise use system Python
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found, using system Python...
)

REM Install specific dependencies that might be missing
echo Installing missing dependencies for LiteLLM proxy...
pip install apscheduler==3.10.4
pip install gunicorn==22.0.0
pip install uvicorn==0.29.0
pip install "litellm[proxy]" --upgrade
pip install cryptography==43.0.0

echo.
echo Testing LiteLLM installation...
litellm --version

echo.
echo ===================================================
echo If you saw a version number above, the fix was successful.
echo If you still see errors, try running the commands manually:
echo.
echo pip install "litellm[proxy]" --force-reinstall
echo ===================================================
echo.
pause
