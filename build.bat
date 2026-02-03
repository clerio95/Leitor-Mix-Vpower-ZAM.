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
