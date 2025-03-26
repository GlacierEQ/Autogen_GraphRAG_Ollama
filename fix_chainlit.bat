@echo off
echo ===================================================
echo Fixing Chainlit Installation Issues
echo ===================================================
echo.

REM Activate virtual environment if it exists, otherwise use system Python
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found, using system Python...
)

REM Install Chainlit with specific dependencies
echo Installing Chainlit and dependencies...
pip uninstall -y chainlit
pip install chainlit==2.1.1 --ignore-installed

REM Verify installation
echo.
echo Testing Chainlit installation...
chainlit --version

echo.
echo ===================================================
echo If you saw a version number above, the fix was successful.
echo If you still see errors, try running:
echo.
echo pip install chainlit --force-reinstall
echo ===================================================
echo.
pause
