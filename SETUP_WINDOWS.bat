@echo off
cd /d "%~dp0"
py -3.12 -m venv .venv || goto :error
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt || goto :error
if not exist .env copy .env.example .env
if not exist config.json copy config.example.json config.json
if not exist data mkdir data
if not exist logs mkdir logs
echo.
echo Setup complete. Open WINDOWS_INSTALL.md and complete the .env steps.
pause
exit /b 0
:error
echo Setup failed. Open TROUBLESHOOTING.md. This window will remain open.
pause
exit /b 1
