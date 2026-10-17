@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python run.py
echo.
echo Fortune On-Chain Radar stopped. Read the error above, then check TROUBLESHOOTING.md.
pause
