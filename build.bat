@echo off
REM Instala dependências
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Gera o executável atualizado
python -m PyInstaller --noconfirm --onefile --windowed --icon=icons/iconV.ico --name "Mix V-Power" bonus_calculator.py

REM Mensagem final
ECHO.
ECHO Executável gerado em dist\Mix V-Power.exe
PAUSE 