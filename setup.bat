@echo off
setlocal EnableExtensions EnableDelayedExpansion

title MLB TestPlan MCP - Setup

REM ────────────────────────────────────────────────────────────────────────────
REM  Determine install path  (wherever this .bat lives, e.g. Downloads\mlb-...)
REM ────────────────────────────────────────────────────────────────────────────
set "BASE=%~dp0"
if "%BASE:~-1%"=="\" set "BASE=%BASE:~0,-1%"

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
REM  Ask for PAT tokens
REM ────────────────────────────────────────────────────────────────────────────
echo  How to get a PAT:  Jira / Confluence  -^>  Profile  -^>  Personal Access Tokens  -^>  Create
echo.

set JIRA_PAT=
set CONFLUENCE_PAT=

:ask_jira
set /p JIRA_PAT="  Enter Jira PAT: "
if "!JIRA_PAT!"=="" (
    echo  PAT cannot be empty. Try again.
    goto :ask_jira
)

:ask_confluence
set /p CONFLUENCE_PAT="  Enter Confluence PAT: "
if "!CONFLUENCE_PAT!"=="" (
    echo  PAT cannot be empty. Try again.
    goto :ask_confluence
)

echo.
echo  Saving credentials...

REM ────────────────────────────────────────────────────────────────────────────
REM  Write .env files
REM ────────────────────────────────────────────────────────────────────────────

REM  jira-mcp\.env
(
    echo JIRA_PAT=!JIRA_PAT!
    echo JIRA_BASE_URL=https://api.skyway.porsche.com/jira
    echo HTTP_PROXY=http://http-proxy.porsche.org:3133
    echo HTTPS_PROXY=http://http-proxy.porsche.org:3133
    echo MCP_Port=8000
) > "%BASE%\jira-mcp\.env"
echo  [OK] jira-mcp\.env written

REM  confluence-mcp\.env
(
    echo CONFLUENCE_PAT=!CONFLUENCE_PAT!
    echo CONFLUENCE_BASE_URL=https://api.skyway.porsche.com/confluence
    echo HTTP_PROXY=http://http-proxy.porsche.org:3133
    echo HTTPS_PROXY=http://http-proxy.porsche.org:3133
    echo MCP_Port=8001
) > "%BASE%\confluence-mcp\.env"
echo  [OK] confluence-mcp\.env written

REM  root .env
(
    echo XRAY_BASE_URL=http://localhost:8000
    echo LOCAL_API_URL=http://localhost:8001
    echo CONFLUENCE_PAGE_ID=2378907792
) > "%BASE%\.env"
echo  [OK] root .env written

REM  Save today as PAT creation date
powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-dd'" > "%BASE%\.pat_date"
echo  [OK] PAT creation date saved
echo.

REM ────────────────────────────────────────────────────────────────────────────
REM  Install Python dependencies
REM ────────────────────────────────────────────────────────────────────────────

echo  ==========================================
echo   Step 1/3 : Root server (server.py)
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
    echo  ERROR: pip install failed for root requirements.txt
    pause
    exit /b 1
)
echo  Installing Playwright (needed for PDF export)...
playwright install chromium
call venv\Scripts\deactivate.bat 2>nul

echo.
echo  ==========================================
echo   Step 2/3 : Jira MCP proxy
echo  ==========================================
cd /d "%BASE%\jira-mcp"
if exist venv (
    echo  Removing existing virtual environment...
    rmdir /s /q venv
)
%PYTHON_CMD% -m venv venv
if %errorlevel% neq 0 (
    echo  ERROR: Failed to create virtual environment for jira-mcp.
    pause
    exit /b 1
)
call venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo  ERROR: pip install failed for jira-mcp requirements.txt
    pause
    exit /b 1
)
call venv\Scripts\deactivate.bat 2>nul

echo.
echo  ==========================================
echo   Step 3/3 : Confluence MCP proxy
echo  ==========================================
cd /d "%BASE%\confluence-mcp"
if exist venv (
    echo  Removing existing virtual environment...
    rmdir /s /q venv
)
%PYTHON_CMD% -m venv venv
if %errorlevel% neq 0 (
    echo  ERROR: Failed to create virtual environment for confluence-mcp.
    pause
    exit /b 1
)
call venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo  ERROR: pip install failed for confluence-mcp requirements.txt
    pause
    exit /b 1
)
call venv\Scripts\deactivate.bat 2>nul

echo.
echo  ==========================================
echo   Setup complete!
echo  ==========================================
echo.
echo   Next step: Double-click  launch.bat  to start all servers.
echo.
pause
exit /b 0
