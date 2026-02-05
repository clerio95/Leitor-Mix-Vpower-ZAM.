@echo off
ECHO ========================================
ECHO    Mix V-Power - Build Script
ECHO ========================================
ECHO.

REM Limpa builds anteriores
ECHO Limpando builds anteriores...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
ECHO.

REM Prepara ambiente virtual (Python 3.12+)
ECHO Preparando ambiente virtual...
set "VENV_DIR=.venv"
set "PY_CMD="

py -3.13 -c "import sys; sys.exit(0)" >nul 2>&1
if %errorlevel%==0 (
    set "PY_CMD=py -3.13"
) else (
    py -3.12 -c "import sys; sys.exit(0)" >nul 2>&1
    if %errorlevel%==0 (
        set "PY_CMD=py -3.12"
    )
)

if "%PY_CMD%"=="" (
    python -c "import sys; v=sys.version_info; sys.exit(0 if (v.major==3 and v.minor>=12) else 1)" >nul 2>&1
    if %errorlevel%==0 (
        set "PY_CMD=python"
    )
)

if "%PY_CMD%"=="" (
    ECHO Erro: Python 3.12 ou superior é necessário para o build.
    ECHO Instale o Python 3.12+ e tente novamente.
    PAUSE
    exit /b 1
)

%PY_CMD% -m venv "%VENV_DIR%"
if errorlevel 1 (
    ECHO Erro ao criar o ambiente virtual.
    PAUSE
    exit /b 1
)

call "%VENV_DIR%\Scripts\activate"
if errorlevel 1 (
    ECHO Erro ao ativar o ambiente virtual.
    PAUSE
    exit /b 1
)

REM Instala dependências
ECHO Instalando dependências...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    ECHO Erro ao instalar dependências.
    PAUSE
    exit /b 1
)
ECHO.

REM Gera o executável
ECHO Gerando executável...
python -m PyInstaller --noconfirm --onefile --windowed --icon=icons/iconV.ico --name "Mix V-Power" bonus_calculator.py
ECHO.

REM Cria pasta de distribuição
ECHO Criando pacote de distribuição...
if not exist "dist\Mix V-Power" mkdir "dist\Mix V-Power"
if exist "dist\Mix V-Power.exe" (
    move "dist\Mix V-Power.exe" "dist\Mix V-Power\"
) else (
    ECHO Erro: executável não encontrado em dist.
    PAUSE
    exit /b 1
)
copy "Logo_Vpower.png" "dist\Mix V-Power\"
xcopy "icons" "dist\Mix V-Power\icons\" /E /I /Y
copy "README.md" "dist\Mix V-Power\"
copy "Leia-me.txt" "dist\Mix V-Power\"
ECHO.

REM Mensagem final
ECHO ========================================
ECHO Build concluído com sucesso!
ECHO.
ECHO Arquivos gerados:
ECHO - dist\Mix V-Power\Mix V-Power.exe
ECHO.
ECHO A pasta de distribuição contém tudo necessário
ECHO para executar o programa em outro PC.
ECHO ========================================
PAUSE 
