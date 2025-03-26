# Windows-Specific Troubleshooting Guide

This guide addresses common issues when running GraphRAG + AutoGen + Ollama on Windows systems.

## PowerShell Script Execution Issues

If you're seeing errors like: `The term 'setup_all.bat' is not recognized as the name of a cmdlet...`

### Solution 1: Use Command Prompt Instead

1. Open Command Prompt (not PowerShell)
2. Navigate to the project directory using `cd`
3. Run the batch scripts directly

### Solution 2: Run PowerShell Scripts with Explicit Path

In PowerShell, run batch files with `.\` prefix:
```powershell
.\setup_all.bat
```

## Module Not Found Errors

For errors like `No module named 'apscheduler'` or other missing dependencies:

### Solution:

Run the fix scripts:
```cmd
.\fix_litellm.bat
.\fix_chainlit.bat
```

## 'chainlit' or 'litellm' Command Not Found

If the commands aren't recognized even after installation:

### Solution 1: Verify Virtual Environment

1. Make sure you're using the virtual environment:
   ```cmd
   venv\Scripts\activate
   ```
2. Confirm the command exists:
   ```cmd
   where chainlit
   where litellm
   ```

### Solution 2: Add to PATH

1. Add the Scripts directory to your PATH:
   ```cmd
   set PATH=%PATH%;%USERPROFILE%\AppData\Roaming\Python\Python310\Scripts
   ```

## GraphRAG Index Errors

If you see errors with GraphRAG initialization:

### Solution:

1. Install GraphRAG and other dependencies:
   ```cmd
   pip install -U graphrag
   ```
2. Manually create the directory structure:
   ```cmd
   mkdir input
   mkdir input\markdown
   mkdir cache
   mkdir output
   mkdir coding
   ```
3. Copy the settings file:
   ```cmd
   copy utils\settings.yaml .
   ```

## Running Everything with One Command

To avoid multiple command prompts and activation issues, use:

```cmd
.\run_windows.bat
```

This script handles:
- Virtual environment activation
- Starting LiteLLM proxy server
- Starting Chainlit application

## Windows-Specific Environment Variables

If you're seeing strange path issues, you might need to set environment variables:

```cmd
set PYTHONPATH=%PYTHONPATH%;%CD%
set PATH=%PATH%;C:\Program Files\Ollama
```

## Python Version Issues

If you're seeing compatibility warnings:

1. Check your Python version:
   ```cmd
   python --version
   ```
2. This project works best with Python 3.10 or 3.11
3. Consider installing a different Python version if needed
