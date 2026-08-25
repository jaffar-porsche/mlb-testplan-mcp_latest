@echo off
setlocal EnableExtensions EnableDelayedExpansion

title MLB TestPlan MCP - Start All (8080 / 8000 / 8001)

REM ────────────────────────────────────────────────────────────────────────────
REM  Location-independent: BASE = folder this .bat lives in, wherever the repo
REM  was cloned/extracted on this machine.
REM ────────────────────────────────────────────────────────────────────────────
set "BASE=%~dp0"
if "%BASE:~-1%"=="\" set "BASE=%BASE:~0,-1%"

set "MAIN_DIR=%BASE%"
set "JIRA_DIR=%BASE%\jira-mcp"
set "CONFLUENCE_DIR=%BASE%\confluence-mcp"

cls
echo.
echo  ==========================================
echo   MLB TestPlan MCP  ^|  START ALL SERVERS
echo   %BASE%
echo  ==========================================
echo.

REM ────────────────────────────────────────────────────────────────────────────
REM  Corporate proxy (needed for pip install / package downloads)
REM ────────────────────────────────────────────────────────────────────────────
set "HTTP_PROXY=http://http-proxy.porsche.org:3128"
set "HTTPS_PROXY=http://http-proxy.porsche.org:3133"

REM ────────────────────────────────────────────────────────────────────────────
REM  Detect a working Python launcher
REM ────────────────────────────────────────────────────────────────────────────
set PYTHON_CMD=
py --version >nul 2>&1
if %errorlevel%==0 (set "PYTHON_CMD=py") else (
    python --version >nul 2>&1
    if %errorlevel%==0 (set "PYTHON_CMD=python") else (
        python3 --version >nul 2>&1
        if %errorlevel%==0 (set "PYTHON_CMD=python3")
    )
)
if "%PYTHON_CMD%"=="" (
    echo  ERROR: Python not found. Install Python 3.11+ and ensure it is on PATH.
    pause
    exit /b 1
)
echo  Using Python: %PYTHON_CMD%
echo.

REM ────────────────────────────────────────────────────────────────────────────
REM  Stopping existing MCP servers...
REM ────────────────────────────────────────────────────────────────────────────
echo  ==========================================
echo   Stopping existing MCP servers...
echo  ==========================================
call :KillPort 8080
call :KillPort 8000
call :KillPort 8001
echo.
echo  Waiting for ports to clear...
timeout /t 2 /nobreak >nul
echo.

REM ────────────────────────────────────────────────────────────────────────────
REM  Ensure each service's venv exists and dependencies are installed.
REM  Skips the (slow) install step on subsequent runs via a marker file, so
REM  starting the servers is fast every time after the first run.
REM ────────────────────────────────────────────────────────────────────────────
call :EnsureVenv "%MAIN_DIR%"
if errorlevel 1 exit /b 1

call :EnsureVenv "%JIRA_DIR%"
if errorlevel 1 exit /b 1

call :EnsureVenv "%CONFLUENCE_DIR%"
if errorlevel 1 exit /b 1

REM ────────────────────────────────────────────────────────────────────────────
REM  Start all three servers as TABS in a single Windows Terminal window
REM  (falls back to 3 separate cmd windows if `wt` is not installed).
REM ────────────────────────────────────────────────────────────────────────────
echo  ==========================================
echo   Starting servers...
echo  ==========================================

where wt >nul 2>&1
if %errorlevel%==0 (
    echo  Opening Windows Terminal with 3 tabs [8080 / 8000 / 8001]...
    wt -w 0 new-tab --title "MLB Testplan [8080]" cmd /k "cd /d "%MAIN_DIR%" && call venv\Scripts\activate.bat && python server.py" ; new-tab --title "Jira MCP [8000]" cmd /k "cd /d "%JIRA_DIR%" && call venv\Scripts\activate.bat && uvicorn mcp_server:app --host 0.0.0.0 --port 8000" ; new-tab --title "Confluence MCP [8001]" cmd /k "cd /d "%CONFLUENCE_DIR%" && call venv\Scripts\activate.bat && uvicorn mcp_server:app --host 0.0.0.0 --port 8001"
) else (
    echo  Windows Terminal ^(wt^) not found - falling back to separate windows.
    echo  Starting MLB Testplan server ^(port 8080^)...
    start "MLB Testplan [8080]" cmd /k "cd /d "%MAIN_DIR%" && call venv\Scripts\activate.bat && python server.py"

    echo  Starting Jira MCP server ^(port 8000^)...
    start "Jira MCP [8000]" cmd /k "cd /d "%JIRA_DIR%" && call venv\Scripts\activate.bat && uvicorn mcp_server:app --host 0.0.0.0 --port 8000"

    echo  Starting Confluence MCP server ^(port 8001^)...
    start "Confluence MCP [8001]" cmd /k "cd /d "%CONFLUENCE_DIR%" && call venv\Scripts\activate.bat && uvicorn mcp_server:app --host 0.0.0.0 --port 8001"
)

echo.
echo  ==========================================
echo   All 3 servers starting:
echo     - MLB Testplan   : http://127.0.0.1:8080
echo     - Jira MCP       : http://127.0.0.1:8000
echo     - Confluence MCP : http://127.0.0.1:8001
echo   Close the tab/window to stop the corresponding server.
echo  ==========================================
echo.
pause
exit /b 0


REM ════════════════════════════════════════════════════════════════════════════
:EnsureVenv  <service_dir>
REM  Creates venv (if missing) and installs requirements.txt only once, using
REM  a marker file (venv\.installed) so re-runs skip the slow install step.
REM ════════════════════════════════════════════════════════════════════════════
set "SVC_DIR=%~1"

if not exist "%SVC_DIR%\requirements.txt" (
    echo  Skipping "%SVC_DIR%" - no requirements.txt found.
    exit /b 0
)

if exist "%SVC_DIR%\venv\Scripts\python.exe" if exist "%SVC_DIR%\venv\.installed" if exist "%SVC_DIR%\venv\.requirements.snapshot" (
    fc /b "%SVC_DIR%\requirements.txt" "%SVC_DIR%\venv\.requirements.snapshot" >nul 2>&1
    if not errorlevel 1 (
        echo  [%SVC_DIR%] Dependencies already installed and requirements.txt unchanged - skipping.
        exit /b 0
    )
)

echo  [%SVC_DIR%] Setting up virtual environment...
pushd "%SVC_DIR%"

if not exist venv\Scripts\python.exe (
    %PYTHON_CMD% -m venv venv
    if errorlevel 1 (
        echo  ERROR: Failed to create virtual environment in "%SVC_DIR%".
        popd
        exit /b 1
    )
)

call venv\Scripts\activate.bat
echo  [%SVC_DIR%] Installing requirements.txt (using corporate proxy)...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt
if errorlevel 1 (
    echo  ERROR: pip install failed in "%SVC_DIR%".
    call venv\Scripts\deactivate.bat 2>nul
    popd
    exit /b 1
)
call venv\Scripts\deactivate.bat 2>nul

REM  Snapshot requirements.txt + mark as installed so future runs skip this step
REM  unless requirements.txt changes.
copy /y requirements.txt venv\.requirements.snapshot >nul
type nul > venv\.installed

popd
exit /b 0


REM ════════════════════════════════════════════════════════════════════════════
:KillPort  <port>
REM  Kill all processes LISTENING on the given port (supports EN + DE Windows)
REM ════════════════════════════════════════════════════════════════════════════
echo  Checking port %1...

for /L %%I in (1,1,3) do (
    for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":%1 " ^| findstr "LISTENING"') do (
        if not "%%P"=="0" (
            echo  Killing PID %%P on port %1...
            taskkill /F /T /PID %%P >nul 2>&1
        )
    )
    REM  German Windows: ABHÖREN instead of LISTENING
    for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":%1 " ^| findstr "ABH"') do (
        if not "%%P"=="0" (
            echo  Killing PID %%P on port %1...
            taskkill /F /T /PID %%P >nul 2>&1
        )
    )
    timeout /t 1 /nobreak >nul
)

echo  Port %1 cleared.
exit /b 0
