@echo off
title MLB Testplan Server [port 8080]
cd /d "C:\Users\UOUMPC3\Desktop\mlb-testplan-mcp"
call venv\Scripts\activate.bat
python server.py
echo.
echo  Server stopped. Press any key to close.
pause >nul
