@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "APP_NAME=Mix V-Power"
set "MAIN_PY=bonus_calculator.py"
set "ICON=icons\iconV.ico"
set "LOGO=Logo_Vpower.png"
set "DIST_DIR=dist"
set "OUT_DIR=%DIST_DIR%\%APP_NAME%"
set "LOG=build_log.txt"

echo ===== INICIO %date% %time% ===== > "%LOG%"

call :step "Checando Python"
python -c "import sys; exit(0 if sys.version_info >= (3,12) else 1)" >>"%LOG%" 2>&1
if errorlevel 1 (
  echo ERRO: precisa Python 3.12+ >>"%LOG%"
  echo ERRO: precisa Python 3.12+
  type "%LOG%"
  pause
  exit /b 1
)

call :step "Limpando dist/build/spec"
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%" >>"%LOG%" 2>&1
if exist "build" rmdir /s /q "build" >>"%LOG%" 2>&1
del /q "*.spec" >>"%LOG%" 2>&1

call :step "Garantindo pip e PyInstaller"
python -m pip install --upgrade pip >>"%LOG%" 2>&1
if errorlevel 1 goto :fail

python -m pip show pyinstaller >>"%LOG%" 2>&1
if errorlevel 1 (
  python -m pip install pyinstaller >>"%LOG%" 2>&1
  if errorlevel 1 goto :fail
)

call :step "Instalando requirements"
if exist "requirements.txt" (
  python -m pip install -r requirements.txt >>"%LOG%" 2>&1
  if errorlevel 1 goto :fail
)

call :step "PyInstaller build (incluindo assets)"
REM --add-data usa formato: "origem;destino" no Windows
python -m PyInstaller --noconfirm --onefile --windowed ^
  --name "%APP_NAME%" ^
  --icon "%ICON%" ^
  --add-data "%LOGO%;." ^
  --add-data "icons;icons" ^
  "%MAIN_PY%" >>"%LOG%" 2>&1
if errorlevel 1 goto :fail

call :step "Empacotando pasta final"
mkdir "%OUT_DIR%" >>"%LOG%" 2>&1

if exist "%DIST_DIR%\%APP_NAME%.exe" (
  move /Y "%DIST_DIR%\%APP_NAME%.exe" "%OUT_DIR%\" >>"%LOG%" 2>&1
) else (
  echo ERRO: executavel nao encontrado em "%DIST_DIR%". >>"%LOG%"
  goto :fail
)

REM Copia arquivos extras (se existirem)
if exist "%LOGO%" copy /Y "%LOGO%" "%OUT_DIR%\" >>"%LOG%" 2>&1
if exist "README.md" copy /Y "README.md" "%OUT_DIR%\" >>"%LOG%" 2>&1
if exist "Leia-me.txt" copy /Y "Leia-me.txt" "%OUT_DIR%\" >>"%LOG%" 2>&1

REM Copia pasta icons sem depender de xcopy (usa PowerShell)
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "if (Test-Path 'icons') { Copy-Item -Path 'icons' -Destination '%OUT_DIR%\icons' -Recurse -Force }" >>"%LOG%" 2>&1

echo ===== SUCESSO %date% %time% ===== >> "%LOG%"
echo.
echo Build OK!
echo Saida: "%OUT_DIR%\%APP_NAME%.exe"
echo Log: "%LOG%"
pause
exit /b 0


:step
echo.
echo ===== %~1 =====
echo ===== %~1 ===== >> "%LOG%"
exit /b 0

:fail
echo.
echo ===== FALHA %date% %time% ===== >> "%LOG%"
echo FALHA! Veja o log: "%LOG%"
type "%LOG%"
pause
exit /b 1
