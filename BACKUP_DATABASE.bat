@echo off
cd /d "%~dp0"
if not exist backups mkdir backups
powershell -NoProfile -Command "$d=Get-Date -Format yyyyMMdd_HHmmss; if(Test-Path 'data\fortune_radar.db'){Copy-Item -LiteralPath 'data\fortune_radar.db' -Destination ('backups\fortune_radar_'+$d+'.db'); Write-Host 'Backup succeeded.'}else{Write-Host 'Database not found. Start the bot once first.'; exit 1}"
pause
