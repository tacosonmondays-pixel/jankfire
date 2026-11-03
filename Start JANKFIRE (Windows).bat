@echo off
title JANKFIRE server
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 (
  echo.
  echo  JANKFIRE needs Node.js to run the server.
  echo  Opening the download page. Install the LTS version, then double-click this file again.
  echo.
  start "" https://nodejs.org/en/download
  pause
  exit /b
)
if not exist node_modules (
  echo First run: installing, this takes a minute...
  call npm install --no-audit --no-fund
)
set JF_OPEN=1
node server.js
pause
