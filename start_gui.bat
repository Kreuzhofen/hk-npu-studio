@echo off
setlocal
set "REPOSITORY_ROOT=%~dp0"
set "ENTRYPOINT=%REPOSITORY_ROOT%gui_v2.py"

if not exist "%ENTRYPOINT%" (
    echo ERROR: Phoenix entry point not found: "%ENTRYPOINT%"
    exit /b 1
)

where py >nul 2>&1
if not errorlevel 1 (
    py -3 "%ENTRYPOINT%"
    exit /b %ERRORLEVEL%
)

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found on PATH. Install Python 3.11 ARM64 or add it to PATH.
    exit /b 1
)

python "%ENTRYPOINT%"
exit /b %ERRORLEVEL%
