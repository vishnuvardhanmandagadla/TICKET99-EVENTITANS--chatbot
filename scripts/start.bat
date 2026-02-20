@echo off
echo ============================================
echo   Dual-Brand AI Chatbot - Starting
echo ============================================
echo.

:: Check if Ollama is running
echo Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [WARN] Ollama is not running. Starting in fallback mode.
    echo        Start Ollama separately for AI-powered responses.
) else (
    echo [OK] Ollama is running.
)

:: Activate venv and start server
cd /d "%~dp0\..\backend"
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo [WARN] Virtual environment not found. Run scripts\setup.bat first.
    echo        Attempting to start with system Python...
)

echo.
echo Starting server on http://localhost:8000
echo Demo page: http://localhost:8000/demo
echo.

python main.py
pause
