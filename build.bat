@echo off
pyinstaller --onefile --name automated_setup --hidden-import winshell --hidden-import win32com.client --add-data "app/dist/speech_recognition_app.exe;app/dist" --add-data "extension;extension" automated_setup.py
echo Build completed!
pause 