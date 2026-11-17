@echo off
setlocal
py -3.11 -m venv .venv
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
if errorlevel 1 exit /b 1
echo.
echo Entorno creado correctamente.
pause
