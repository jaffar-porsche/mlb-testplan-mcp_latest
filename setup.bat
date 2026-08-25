@echo off
setlocal EnableExtensions EnableDelayedExpansion

title MLB TestPlan MCP - Setup

REM ────────────────────────────────────────────────────────────────────────────
REM  Determine install path  (wherever this .bat lives, e.g. extracted zip folder)
REM ────────────────────────────────────────────────────────────────────────────
set "BASE=%~dp0"
if "%BASE:~-1%"=="\" set "BASE=%BASE:~0,-1%"

REM ────────────────────────────────────────────────────────────────────────────
REM  Log everything this script prints to setup_log.txt (while still showing
REM  it live in the console) so setup failures can be diagnosed afterwards.
REM ────────────────────────────────────────────────────────────────────────────
if not "%~1"=="__LOGGED__" (
    powershell -NoProfile -Command "& { & '%~f0' __LOGGED__ 2>&1 | Tee-Object -FilePath '%BASE%\setup_log.txt' }"
    exit /b %errorlevel%
)

cls
echo.
echo  ==========================================
echo   MLB TestPlan MCP  ^|  SETUP
echo  ==========================================
echo   Install location: %BASE%
echo  ==========================================
echo.

REM ────────────────────────────────────────────────────────────────────────────
REM  Verify Python is available
REM ────────────────────────────────────────────────────────────────────────────
set PYTHON_CMD=

python --version >nul 2>&1
if %errorlevel%==0 set "PYTHON_CMD=python" & goto :python_ok

py --version >nul 2>&1
if %errorlevel%==0 set "PYTHON_CMD=py" & goto :python_ok

python3 --version >nul 2>&1
if %errorlevel%==0 set "PYTHON_CMD=python3" & goto :python_ok

echo  ERROR: Python not found.
echo  Please install Python 3.11 or newer and ensure it is in your PATH.
echo  Download: https://www.python.org/downloads/
pause
exit /b 1

:python_ok
echo  Python found:
%PYTHON_CMD% --version
echo.

REM ────────────────────────────────────────────────────────────────────────────
REM  Create venv and install requirements.txt from the root folder
REM  (Jira/Confluence MCP servers are started manually via the Electron app,
REM   so no separate setup is needed for those here.)
REM ────────────────────────────────────────────────────────────────────────────
echo  ==========================================
echo   Installing dependencies (requirements.txt)
echo  ==========================================
cd /d "%BASE%"

if exist venv (
    echo  Removing existing virtual environment...
    rmdir /s /q venv
)

%PYTHON_CMD% -m venv venv
if %errorlevel% neq 0 (
    echo  ERROR: Failed to create virtual environment.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo  ERROR: pip install failed for requirements.txt
    pause
    exit /b 1
)
call venv\Scripts\deactivate.bat 2>nul

echo.
echo  ==========================================
echo   Setup complete!
echo  ==========================================
echo.
echo   Next step: Double-click  launch.bat  to open the dashboard.
echo   (Start Jira/Confluence in the Electron app yourself, as usual.)
echo.
pause
exit /b 0
