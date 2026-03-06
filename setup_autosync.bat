@echo off
REM Brain Auto-Sync Task Scheduler Script
REM Run this as Administrator to set up automatic sync every 5 minutes

cd /d "e:\Vibe Code\Brain"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    pause
    exit /b 1
)

REM Create the scheduled task (runs every 5 minutes)
echo Creating Windows Task Scheduler task...
schtasks /create /tn "BrainAutoSync" /tr "python e:\Vibe Code\Brain\brain_autosync.py --once" /sc minute /mo 5 /f

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   Task created successfully!
    echo ========================================
    echo.
    echo Brain will auto-sync every 5 minutes
    echo.
    echo To view task:     schtasks /run /tn "BrainAutoSync"
    echo To check status: schtasks /query /tn "BrainAutoSync"
    echo To delete task:   schtasks /delete /tn "BrainAutoSync" /f
    echo.
) else (
    echo.
    echo ERROR: Could not create task
    echo Try running as Administrator
)

pause
