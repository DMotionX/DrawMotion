@echo off
title DrawMotion Forensic Diagnostic Console
set QT_DEBUG_PLUGINS=1
echo ========================================================
echo   DrawMotion Forensic Diagnostic Launcher
echo ========================================================
echo Select diagnostic mode to run:
echo   [1] Normal Execution (All components active)
echo   [2] Disable Animation Only (DM_NO_ANIM=1)
echo   [3] Disable Tab 0 Only (DM_NO_TAB0=1)
echo   [4] Safe Mode - Both Flags (DM_NO_ANIM=1 + DM_NO_TAB0=1)
echo ========================================================
set /p mode="Enter choice [1-4] (default 1): "

if "%mode%"=="2" (
    set DM_NO_ANIM=1
    set DM_NO_TAB0=0
    echo [RUNNING] Mode 2: Animation Disabled
) else if "%mode%"=="3" (
    set DM_NO_ANIM=0
    set DM_NO_TAB0=1
    echo [RUNNING] Mode 3: Tab 0 Creation Disabled
) else if "%mode%"=="4" (
    set DM_NO_ANIM=1
    set DM_NO_TAB0=1
    echo [RUNNING] Mode 4: Safe Mode (Both Disabled)
) else (
    set DM_NO_ANIM=0
    set DM_NO_TAB0=0
    echo [RUNNING] Mode 1: Normal Execution
)

echo.
"%~dp0DrawMotion.exe"
echo.
echo ========================================================
echo DrawMotion exited with exit code: %ERRORLEVEL%
echo Diagnostic logs are automatically recorded at:
echo %%LOCALAPPDATA%%\DrawMotion\Logs\startup_lifecycle.log
echo %%LOCALAPPDATA%%\DrawMotion\Logs\qt_messages.log
echo %%LOCALAPPDATA%%\DrawMotion\Logs\crash_faulthandler.log
echo ========================================================
if exist "%LOCALAPPDATA%\DrawMotion\Logs\startup_lifecycle.log" (
    echo.
    echo --- Last Startup Lifecycle Events ---
    powershell -NoProfile -Command "Get-Content '%LOCALAPPDATA%\DrawMotion\Logs\startup_lifecycle.log' -Tail 15"
    echo.
)
pause
