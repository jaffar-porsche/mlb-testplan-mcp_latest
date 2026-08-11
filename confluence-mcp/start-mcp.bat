@echo off
setlocal enabledelayedexpansion

echo Starting Confluence MCP Server...

cd %CONFLUENCE_MCP_SERVER_HOME%

REM Simple Python detection
set PYTHON_CMD=

REM Try py first (most reliable on Windows)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Found Python via py launcher
    py --version
    set PYTHON_CMD=py
    goto :create_venv
)

REM Try python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Found Python via python command
    python --version
    set PYTHON_CMD=python
    goto :create_venv
)

REM Try python3
python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Found Python via python3 command
    python3 --version
    set PYTHON_CMD=python3
    goto :create_venv
)

echo Python not found!
echo Please install Python and ensure it's in your PATH
pause
exit /b 1

:create_venv
REM Check existing virtual environment
if exist venv (
    echo Checking existing virtual environment...
    if exist venv\Scripts\python.exe (
        REM Get current Python version used to create this script
        for /f "tokens=2 delims= " %%v in ('%PYTHON_CMD% --version 2^>^&1') do (
            set CURRENT_PYTHON_VERSION=%%v
        )
        
        REM Get venv Python version
        for /f "tokens=2 delims= " %%v in ('venv\Scripts\python.exe --version 2^>^&1') do (
            set VENV_PYTHON_VERSION=%%v
        )
        
        REM Compare versions - if they match, keep the venv
        if "!CURRENT_PYTHON_VERSION!"=="!VENV_PYTHON_VERSION!" (
            echo Existing virtual environment uses Python !VENV_PYTHON_VERSION! (compatible)
            goto :activate_venv
        ) else (
            echo Removing old virtual environment (Python versions differ)
            rmdir /s /q venv
        )
    ) else (
        echo Removing corrupted virtual environment
        rmdir /s /q venv
    )
)

REM Create new venv
echo Creating virtual environment with %PYTHON_CMD%
%PYTHON_CMD% -m venv venv
if %errorlevel% neq 0 (
    echo Failed to create virtual environment
    echo Make sure Python has venv support installed
    pause
    exit /b 1
)

:activate_venv
REM Activate venv
echo Activating virtual environment
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies
python -m pip install --upgrade pip
if exist requirements.txt (
    echo Installing from requirements.txt...
    pip install -r requirements.txt
) else (
    echo requirements.txt not found, installing default packages...
    pip install fastapi-mcp fastapi httpx uvicorn atlassian-python-api python-dotenv pydantic
)
if %errorlevel% neq 0 (
    echo Failed to install dependencies
    pause
    exit /b 1
)

REM Check for .env file
set MCP_PORT=8001
set MCP_PORT_FOUND=0
if exist .env (
    for /f "tokens=1,2 delims== " %%a in ('findstr /R "^MCP_Port[ ]*=" .env') do (
        set MCP_PORT=%%b
        set MCP_PORT_FOUND=1
    )
) 
if %MCP_PORT_FOUND%==0 if exist .env.example (
    for /f "tokens=1,2 delims== " %%a in ('findstr /R "^MCP_Port[ ]*=" .env.example') do (
        set MCP_PORT=%%b
        set MCP_PORT_FOUND=1
    )
    echo **********************************************************
    echo Warning: .env file has not been found !
    echo Please copy .env.example to .env and add your CONFLUENCE_PAT
    echo **********************************************************
    exit /b 1
)
REM Remove spaces and quotes from MCP_PORT
set MCP_PORT=%MCP_PORT: =%
set MCP_PORT=%MCP_PORT:"=%
REM Validate MCP_PORT is numeric, else fallback to default
for /f "delims=0123456789" %%c in ("%MCP_PORT%") do set MCP_PORT=8001

echo Setup complete!
echo Starting server on http://localhost:%MCP_PORT%/mcp/
echo API docs available at http://localhost:%MCP_PORT%/docs
echo Press Ctrl+C to stop

REM Start server
uvicorn mcp_server:app --host 0.0.0.0 --port %MCP_PORT% --reload
