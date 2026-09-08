@echo off
setlocal
python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --clean --onefile --windowed --name LudoGame main.py
echo.
echo Build complete: dist\LudoGame.exe
pause
