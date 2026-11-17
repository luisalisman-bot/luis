@echo off
setlocal
chcp 65001 >nul
title PeakCut
cd /d "%~dp0"
if not exist "runtime\python.exe" (
  echo Extrae el ZIP completo antes de abrir PeakCut.
  echo Clic derecho en el ZIP y luego Extraer todo.
  pause
  exit /b 1
)
"runtime\python.exe" -I -X utf8 "%~dp0iniciar.py"
if errorlevel 1 pause
endlocal
