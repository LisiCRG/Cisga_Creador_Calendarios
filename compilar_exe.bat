@echo off
if not exist .venv\Scripts\python.exe (
  echo No existe .venv. Ejecuta primero crear_entorno.bat
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m pytest -q
if errorlevel 1 (
  echo Las pruebas han fallado. No se compila.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm GENERADOR_TURNOS.spec
if errorlevel 1 exit /b 1
echo.
echo EXE generado en dist\GENERADOR_TURNOS.exe
pause
