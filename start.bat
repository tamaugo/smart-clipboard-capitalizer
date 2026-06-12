@echo off
taskkill /f /im pythonw.exe >nul 2>&1
start /b pythonw src/clipboard_capitalizer/app.py
exit
