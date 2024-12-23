@echo off
pyinstaller --onefile --name uninstall --hidden-import winshell uninstall.py
echo Build completed!
pause 