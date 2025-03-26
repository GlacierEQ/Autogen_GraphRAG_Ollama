# Troubleshooting Guide for GraphRAG + AutoGen + Ollama

## PowerShell Script Execution Issues

### Problem: Scripts won't execute
If you see "... is not recognized as the name of a cmdlet, function, script file, or operable program"

**Solution:**
1. Make sure to use the dot-slash prefix: `.\install_simple.ps1` instead of `install_simple.ps1`
2. You might need to set the execution policy: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### Problem: "&" operator errors
If you see "The expression after '&' in a pipeline element produced an object that was not valid"

**Solution:**
1. Make sure Python is in your PATH
2. Use explicit paths: `& "C:\Path\To\Python\python.exe"` instead of `& python`

## Virtual Environment Issues

### Problem: Virtual environment not found
If the launch script shows "WARNING: Virtual environment not found"

**Solution:**
1. Run the installation script again: `.\install_simple.ps1`
2. Create the virtual environment manually:
   ```
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

## Python Package Installation Issues

### Problem: Missing packages
If you see "No module named X" errors

**Solution:**
1. Make sure your virtual environment is activated
2. Install the package directly: `pip install X`
3. Verify requirements.txt doesn't have invalid entries

## Document Processing Issues

### Problem: "Package not found" when processing Word documents
If you see "Package not found at 'sample_document.docx'"

**Solution:**
1. Ensure the file exists in the specified location
2. Install python-docx: `pip install python-docx`
3. Use full paths to files: `python document_processors/word_processor.py --input "C:\full\path\to\sample_document.docx" --output "C:\full\path\to\output_directory"`

## Running Commands in PowerShell

Using `&&` to chain commands doesn't work in PowerShell. Instead:

1. For simple command chaining, use `;`: `cd document_processors; python word_processor.py`
2. For more complex logic, use multiple lines or scripts

## Running the Application

If everything is set up but the application won't start:

1. Run each component separately:
   - Start LiteLLM: `python -m litellm --model ollama_chat/llama3 --port 8000`
   - Start your Flask app: `python appUI_pro.py`
   - Start Chainlit: `python -m chainlit run appUI_pro.py`
2. Ensure Ollama is installed and running locally

## Testing Document Processing

To test the Word document processor:
```
python document_processors/word_processor.py --input "path/to/your/document.docx" --output "output_directory"
```

Make sure the directories exist and Python has permission to write to them.
