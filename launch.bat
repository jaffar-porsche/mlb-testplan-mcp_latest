@echo off
setlocal EnableExtensions EnableDelayedExpansion

title MLB TestPlan MCP - Launcher

REM ────────────────────────────────────────────────────────────────────────────
REM  Determine base path (wherever this .bat lives)
REM ────────────────────────────────────────────────────────────────────────────
set "BASE=%~dp0"
if "%BASE:~-1%"=="\" set "BASE=%BASE:~0,-1%"

REM ────────────────────────────────────────────────────────────────────────────
REM  Log everything this script prints to launch_log.txt (while still showing
REM  it live in the console) so launch failures can be diagnosed afterwards.
REM ────────────────────────────────────────────────────────────────────────────
if not "%~1"=="__LOGGED__" (
    powershell -NoProfile -Command "& { & '%~f0' __LOGGED__ 2>&1 | Tee-Object -FilePath '%BASE%\launch_log.txt' }"
    exit /b %errorlevel%
)

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
        echo  Setup failed. Cannot launch server.
        pause
        exit /b 1
    )
    REM Re-read BASE in case setup changed directory
    cd /d "%BASE%"
)

REM ────────────────────────────────────────────────────────────────────────────
REM  Kill any existing server on port 8080
REM ────────────────────────────────────────────────────────────────────────────
echo  ==========================================
echo  Stopping existing server (if any)...
echo  ==========================================

call :KillPort 8080

echo.
echo  Waiting for port to clear...
timeout /t 2 /nobreak >nul

REM ────────────────────────────────────────────────────────────────────────────
REM  Write per-server helper bat (avoids nested-quote issues with spaces in path)
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

REM ────────────────────────────────────────────────────────────────────────────
REM  Start server
REM ────────────────────────────────────────────────────────────────────────────
echo  ==========================================
echo  Starting server...
echo  ==========================================
echo.

echo  Starting MLB Testplan (port 8080)...
start "MLB Testplan [8080]" cmd /k "%BASE%\_run_mlb.bat"
timeout /t 2 /nobreak >nul

REM ────────────────────────────────────────────────────────────────────────────
REM  Open Dashboard
REM  (Jira/Confluence MCP servers are started manually via the Electron app.)
REM ────────────────────────────────────────────────────────────────────────────
echo.
echo  Opening dashboard...
start "" "%BASE%\dashboard.html"

echo.
echo  ==========================================
echo   Server started.  Dashboard opened.
echo  ==========================================
echo   Port: 8080 (MLB Testplan)
echo   Make sure Jira/Confluence are running in the Electron app.
echo   Close the server window to stop it.
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
