@echo off
REM Handler invoked by the "mlbstart://" custom URL protocol.
REM Registered via register-start-protocol.reg. Launches the main server
REM (port 8080) in the background using the existing launch.bat.

set "BASE=%~dp0"
if "%BASE:~-1%"=="\" set "BASE=%BASE:~0,-1%"

start "MLB TestPlan MCP" /min cmd /c ""%BASE%\launch.bat""
exit /b 0
