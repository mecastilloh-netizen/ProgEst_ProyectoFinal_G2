@echo off
rem Inicia AulaGest con el entorno virtual local ya preparado.
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py
) else (
    python main.py
)
pause
