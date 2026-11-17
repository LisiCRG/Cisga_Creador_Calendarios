@echo off
if not exist .venv\Scripts\python.exe (
  echo No existe .venv. Ejecuta primero crear_entorno.bat
  pause
  exit /b 1
)
.venv\Scripts\python.exe main.py
