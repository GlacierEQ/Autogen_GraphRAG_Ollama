@echo off
echo Creating Python virtual environment...

REM Create virtual environment
python -m venv venv

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip

REM Install dependencies
echo Installing required packages...
pip install ollama
pip install pyautogen[retrievechat]
pip install tiktoken
pip install chainlit
pip install graphrag
pip install marker-pdf
pip install torch
pip install litellm[proxy]

echo Dependencies installed!
echo To activate this environment in the future, run: venv\Scripts\activate.bat
