@echo off
REM 🚀 Windows Setup Script - APC Gym Log System
REM Double-click this file to set up the project automatically

echo.
echo ========================================
echo 🚀 APC Gym Log System - Windows Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please download Python from: https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed or not in PATH
    echo Please download Node.js from: https://nodejs.org
    pause
    exit /b 1
)

echo ✅ Python and Node.js are available
echo.

REM Run the Python setup script
echo 🚀 Running automated setup...
python quick-setup.py

echo.
echo ========================================
echo Setup script completed!
echo ========================================
echo.
echo If setup was successful, you can now run:
echo   python start-dev.py
echo.
echo Then open your browser to: http://localhost:5173
echo.
pause
