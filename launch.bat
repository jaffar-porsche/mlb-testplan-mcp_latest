@echo off
setlocal EnableExtensions EnableDelayedExpansion

title MLB TestPlan MCP - Launcher

REM ────────────────────────────────────────────────────────────────────────────
REM  Determine base path (wherever this .bat lives)
REM ────────────────────────────────────────────────────────────────────────────
set "BASE=%~dp0"
if "%BASE:~-1%"=="\" set "BASE=%BASE:~0,-1%"

cls
echo.
echo  ==========================================
echo   MLB TestPlan MCP  ^|  LAUNCHER
echo   %BASE%
echo  ==========================================
echo.

REM ────────────────────────────────────────────────────────────────────────────
REM  First-time check: if venv doesn't exist, setup has not been run
REM ────────────────────────────────────────────────────────────────────────────
if not exist "%BASE%\venv\Scripts\python.exe" (
    echo  Setup not found. Running setup first...
    echo.
    call "%BASE%\setup.bat"
    if !errorlevel! neq 0 (
        echo  Setup failed. Cannot launch servers.
        pause
        exit /b 1
    )
    REM Re-read BASE in case setup changed directory
    cd /d "%BASE%"
)

REM ────────────────────────────────────────────────────────────────────────────
REM  PAT expiry check (warn and prompt at day 29+)
REM ────────────────────────────────────────────────────────────────────────────
if not exist "%BASE%\.pat_date" goto :pat_expired

set "PAT_DATE="
for /f "usebackq delims=" %%D in ("%BASE%\.pat_date") do (
    if "!PAT_DATE!"=="" set "PAT_DATE=%%D"
)
REM Strip any trailing whitespace/CR
set "PAT_DATE=!PAT_DATE: =!"

echo  Checking PAT expiry (setup date: !PAT_DATE!)...

powershell -NoProfile -Command ^
    "try { $d=[datetime]::ParseExact('!PAT_DATE!','yyyy-MM-dd',$null); $days=([datetime]::Today-$d).Days; if($days -ge 29){exit 1}else{Write-Host (' PAT age: '+$days+' day(s) - OK'); exit 0} } catch { exit 1 }"

if !errorlevel!==0 goto :pat_ok

:pat_expired
echo.
echo  ==========================================
echo   PAT TOKEN RENEWAL REQUIRED
echo   Your PAT is 29+ days old and may have
echo   expired. Please enter new tokens below.
echo  ==========================================
echo.
echo  How to get a new PAT:
echo    Jira / Confluence -^> Profile -^> Personal Access Tokens -^> Create
echo.

set NEW_JIRA_PAT=
set NEW_CONFLUENCE_PAT=

:renew_jira
set /p NEW_JIRA_PAT="  New Jira PAT: "
if "!NEW_JIRA_PAT!"=="" (
    echo  PAT cannot be empty.
    goto :renew_jira
)

:renew_confluence
set /p NEW_CONFLUENCE_PAT="  New Confluence PAT: "
if "!NEW_CONFLUENCE_PAT!"=="" (
    echo  PAT cannot be empty.
    goto :renew_confluence
)

REM  Update jira-mcp\.env
(
    echo JIRA_PAT=!NEW_JIRA_PAT!
    echo JIRA_BASE_URL=https://api.skyway.porsche.com/jira
    echo HTTP_PROXY=http://http-proxy.porsche.org:3133
    echo HTTPS_PROXY=http://http-proxy.porsche.org:3133
    echo MCP_Port=8000
) > "%BASE%\jira-mcp\.env"

REM  Update confluence-mcp\.env
(
    echo CONFLUENCE_PAT=!NEW_CONFLUENCE_PAT!
    echo CONFLUENCE_BASE_URL=https://api.skyway.porsche.com/confluence
    echo HTTP_PROXY=http://http-proxy.porsche.org:3133
    echo HTTPS_PROXY=http://http-proxy.porsche.org:3133
    echo MCP_Port=8001
) > "%BASE%\confluence-mcp\.env"

REM  Reset PAT date to today
powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-dd'" > "%BASE%\.pat_date"
echo.
echo  [OK] PAT tokens updated. New expiry window starts today.

:pat_ok
echo.

REM ────────────────────────────────────────────────────────────────────────────
REM  Kill any existing servers on ports 8080 / 8000 / 8001
REM ────────────────────────────────────────────────────────────────────────────
echo  ==========================================
echo  Stopping existing servers...
echo  ==========================================

call :KillPort 8080
call :KillPort 8000
call :KillPort 8001

echo.
echo  Waiting for ports to clear...
timeout /t 2 /nobreak >nul

REM ────────────────────────────────────────────────────────────────────────────
REM  Write per-server helper bats (avoids nested-quote issues with spaces in path)
REM ────────────────────────────────────────────────────────────────────────────
(
    echo @echo off
    echo title MLB Testplan Server [port 8080]
    echo cd /d "%BASE%"
    echo call venv\Scripts\activate.bat
    echo python server.py
    echo echo.
    echo echo  Server stopped. Press any key to close.
    echo pause ^>nul
) > "%BASE%\_run_mlb.bat"

(
    echo @echo off
    echo title Jira MCP Proxy [port 8000]
    echo cd /d "%BASE%\jira-mcp"
    echo call venv\Scripts\activate.bat
    echo uvicorn mcp_server:app --host 0.0.0.0 --port 8000 --reload
    echo echo.
    echo echo  Server stopped. Press any key to close.
    echo pause ^>nul
) > "%BASE%\_run_jira.bat"

(
    echo @echo off
    echo title Confluence MCP Proxy [port 8001]
    echo cd /d "%BASE%\confluence-mcp"
    echo call venv\Scripts\activate.bat
    echo uvicorn mcp_server:app --host 0.0.0.0 --port 8001 --reload
    echo echo.
    echo echo  Server stopped. Press any key to close.
    echo pause ^>nul
) > "%BASE%\_run_confluence.bat"

REM ────────────────────────────────────────────────────────────────────────────
REM  Start servers
REM ────────────────────────────────────────────────────────────────────────────
echo  ==========================================
echo  Starting servers...
echo  ==========================================
echo.

echo  [1/3] Starting MLB Testplan (port 8080)...
start "MLB Testplan [8080]" cmd /k "%BASE%\_run_mlb.bat"
timeout /t 2 /nobreak >nul

echo  [2/3] Starting Jira MCP proxy (port 8000)...
start "Jira MCP [8000]" cmd /k "%BASE%\_run_jira.bat"
timeout /t 2 /nobreak >nul

echo  [3/3] Starting Confluence MCP proxy (port 8001)...
start "Confluence MCP [8001]" cmd /k "%BASE%\_run_confluence.bat"
timeout /t 3 /nobreak >nul

REM ────────────────────────────────────────────────────────────────────────────
REM  Open Dashboard
REM ────────────────────────────────────────────────────────────────────────────
echo.
echo  Opening dashboard...
start "" "%BASE%\dashboard.html"

echo.
echo  ==========================================
echo   All servers started.  Dashboard opened.
echo  ==========================================
echo   Ports:  8080 (MLB)   8000 (Jira)   8001 (Confluence)
echo   Close each server window to stop that server.
echo  ==========================================
echo.
pause
exit /b 0


REM ════════════════════════════════════════════════════════════════════════════
:KillPort
REM  Kill all processes LISTENING on the given port (supports EN + DE Windows)
REM ════════════════════════════════════════════════════════════════════════════
echo.
echo  Checking port %1...

for /L %%I in (1,1,5) do (

    set "FOUND="

    for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":%1 " ^| findstr "LISTENING"') do (
        if not "%%P"=="0" (
            echo  Killing PID %%P on port %1...
            taskkill /F /T /PID %%P >nul 2>&1
            set "FOUND=1"
        )
    )

    REM  German Windows: ABHÖREN instead of LISTENING
    for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":%1 " ^| findstr "ABH"') do (
        if not "%%P"=="0" (
            echo  Killing PID %%P on port %1...
            taskkill /F /T /PID %%P >nul 2>&1
            set "FOUND=1"
        )
    )

    timeout /t 1 /nobreak >nul
)

echo  Port %1 cleared.
exit /b
