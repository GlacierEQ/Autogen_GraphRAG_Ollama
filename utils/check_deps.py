import importlib.util
import subprocess
import sys
import os

def check_module(module_name):
    """Check if a Python module is installed"""
    spec = importlib.util.find_spec(module_name)
    if spec is not None:
        print(f"✅ {module_name} is installed")
        return True
    else:
        print(f"❌ {module_name} is not installed")
        return False

def check_command(command):
    """Check if a command is available in PATH"""
    try:
        subprocess.run([command, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        print(f"✅ {command} is installed")
        return True
    except FileNotFoundError:
        print(f"❌ {command} is not installed or not in PATH")
        return False

def check_ollama_models():
    """Check if required Ollama models are available"""
    required_models = ["llama3", "mistral", "nomic-embed-text"]
    try:
        result = subprocess.run(["ollama", "list"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        available_models = result.stdout.lower()
        
        for model in required_models:
            if model.lower() in available_models:
                print(f"✅ Ollama model {model} is available")
            else:
                print(f"❌ Ollama model {model} is not available. Pull it with 'ollama pull {model}'")
    except FileNotFoundError:
        print("❌ Ollama is not installed or not in PATH")

def check_graphrag_modifications():
    """Check if GraphRAG embedding files have been modified"""
    try:
        # Try to find the package path
        import graphrag
        pkg_path = os.path.dirname(graphrag.__file__)
        
        embedding_path = os.path.join(pkg_path, "query", "llm", "oai", "embedding.py")
        embeddings_llm_path = os.path.join(pkg_path, "llm", "openai", "openai_embeddings_llm.py")
        
        if os.path.exists(embedding_path) and os.path.exists(embeddings_llm_path):
            print(f"GraphRAG package found at: {pkg_path}")
            print(f"You may need to replace these files with the ones in the utils directory:")
            print(f"1. {embedding_path}")
            print(f"2. {embeddings_llm_path}")
        else:
            print("❌ Could not locate GraphRAG embedding files")
    except ImportError:
        print("❌ GraphRAG package is not installed")

def main():
    print("Checking dependencies for GraphRAG + AutoGen + Ollama + Chainlit application...\n")
    
    # Check Python modules
    modules = ["graphrag", "autogen", "chainlit", "litellm", "yaml", "torch"]
    all_modules_installed = all(check_module(module) for module in modules)
    
    # Check command-line tools
    commands = ["ollama"]
    all_commands_available = all(check_command(command) for command in commands)
    
    # Check Ollama models
    print("\nChecking Ollama models:")
    check_ollama_models()
    
    # Check GraphRAG modifications
    print("\nChecking GraphRAG package:")
    check_graphrag_modifications()
    
    # Overall status
    print("\nOverall status:")
    if all_modules_installed and all_commands_available:
        print("✅ All required dependencies are installed")
        print("\nYou can proceed with running the application:")
        print("1. Run 'python init_graphrag.py' to initialize the environment")
        print("2. Run 'python -m graphrag.index --root .' to index the documents")
        print("3. Start LiteLLM proxy with 'litellm --model ollama_chat/llama3'")
        print("4. Run the application with 'chainlit run appUI.py'")
        print("\nOr use the start.bat (Windows) or start.sh (Linux/Mac) script to start everything")
    else:
        print("❌ Some dependencies are missing. Please install them before running the application.")

if __name__ == "__main__":
    main()
