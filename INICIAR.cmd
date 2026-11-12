@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Instala Python 3.12 ou superior em python.org e segue docs\INSTALACAO.md.
  pause
  exit /b 1
)
echo MEMECOIN RADAR PRO - teste local de mercado, sem dinheiro e sem Telegram
".venv\Scripts\python.exe" -m radar.app --dry-run
echo.
echo Proximo passo: abrir docs\INSTALACAO.md
pause
