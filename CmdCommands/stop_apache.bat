@echo off
fltmc >nul 2>&1
if errorlevel 1 (
	powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%ComSpec%' -ArgumentList '/c \"%~f0\" %*' -Verb RunAs"
	exit /b
)

set "SERVICE_DIR=%~1"
if "%SERVICE_DIR%"=="" set "SERVICE_DIR=%SERVICE_POSITION%"

taskkill /F /IM httpd.exe

