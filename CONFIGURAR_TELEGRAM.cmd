@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Segue primeiro docs\INSTALACAO.md para preparar Python.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" scripts\setup_telegram.py
pause
