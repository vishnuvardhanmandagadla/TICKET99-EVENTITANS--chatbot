@echo off
echo ============================================
echo   Dual-Brand AI Chatbot - Setup
echo ============================================
echo.

:: Create virtual environment
echo [1/4] Creating virtual environment...
cd /d "%~dp0\..\backend"
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create venv. Ensure Python 3.10+ is installed.
    pause
    exit /b 1
)

:: Activate and install dependencies
echo [2/4] Installing Python dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

:: Pull Ollama model
echo [3/4] Pulling phi3:mini model via Ollama...
echo (Make sure Ollama is installed and running)
ollama pull phi3:mini
if errorlevel 1 (
    echo [WARN] Could not pull model. Make sure Ollama is installed.
    echo        The chatbot will still work in fallback mode without Ollama.
)

:: Build knowledge base
echo [4/4] Building ChromaDB knowledge base...
python -c "import vector_store; vector_store.initialize()"
if errorlevel 1 (
    echo [ERROR] Failed to build knowledge base.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Setup complete!
echo   Run scripts\start.bat to start the server
echo ============================================
pause
