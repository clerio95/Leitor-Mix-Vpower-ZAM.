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
pip install -r requirements.txt
ECHO.

REM Gera o executável
ECHO Gerando executável...
python -m PyInstaller --noconfirm --onefile --windowed --icon=icons/iconV.ico --name "Mix V-Power" bonus_calculator.py
ECHO.

REM Cria pasta de distribuição
ECHO Criando pacote de distribuição...
mkdir "dist\Mix V-Power"
move "dist\Mix V-Power.exe" "dist\Mix V-Power\"
copy "Logo_Vpower.png" "dist\Mix V-Power\"
copy "icons" "dist\Mix V-Power\icons\" /Y
xcopy "icons" "dist\Mix V-Power\icons\" /E /I /Y
copy "README.md" "dist\Mix V-Power\"
copy "Leia-me.txt" "dist\Mix V-Power\"
ECHO.

REM Cria arquivo ZIP
ECHO Criando arquivo ZIP...
powershell -command "Compress-Archive -Path 'dist\Mix V-Power' -DestinationPath 'dist\Mix-V-Power-Completo.zip' -Force"
ECHO.

REM Mensagem final
ECHO ========================================
ECHO Build concluído com sucesso!
ECHO.
ECHO Arquivos gerados:
ECHO - dist\Mix V-Power\Mix V-Power.exe
ECHO - dist\Mix-V-Power-Completo.zip
ECHO.
ECHO O arquivo ZIP contém tudo necessário
ECHO para executar o programa em outro PC.
ECHO ========================================
PAUSE 