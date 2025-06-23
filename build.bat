@echo off
echo Cleaning previous build...
rmdir /s /q build
rmdir /s /q dist

echo Building application...
python -m PyInstaller --noconfirm --onefile --windowed ^
    --add-data "config.json;." ^
    --add-data "icons;icons" ^
    --add-data "Logo_Vpower.png;." ^
    --icon "icons/iconV.ico" ^
    --name "Mix V-Power" ^
    bonus_calculator.py

echo Build complete!
pause 