@echo off
echo ============================================
echo   Rebuilding ChromaDB Knowledge Base
echo ============================================
echo.

cd /d "%~dp0\..\backend"

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

echo Rebuilding collections...
python -c "import vector_store; vector_store.initialize(); print('Done!')"

echo.
echo Knowledge base rebuilt successfully.
pause
