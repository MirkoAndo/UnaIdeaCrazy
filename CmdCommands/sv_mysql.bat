@echo off
set "SERVICE_DIR=%~1"
if "%SERVICE_DIR%"=="" set "SERVICE_DIR=%SERVICE_POSITION%"

if "%SERVICE_DIR%"=="" (
    echo [ERROR] Nessuna posizione del file/servizio fornita.
    exit /b 1
)

start "" "%SERVICE_DIR%\bin\mysqld.exe" --defaults-file="%SERVICE_DIR%\my.ini"

