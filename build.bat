@echo off
echo Cleaning previous build...
rmdir /s /q build
rmdir /s /q dist

echo Building application...
python -m PyInstaller --noconfirm --onefile --windowed ^
    --add-data "config.json;." ^
    --add-data "icons;icons" ^
    --icon "icons/cog.ico" ^
    --name "Calculadora de Bonificação" ^
    bonus_calculator.py

echo Build complete!
pause 