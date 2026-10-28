@echo off
setlocal
cd /d "%~dp0"

rem Prefer this project's virtual environment so dependencies stay isolated.
if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else (
    where py >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON=py"
    ) else (
        where python >nul 2>nul
        if not errorlevel 1 (
            set "PYTHON=python"
        ) else (
            echo Python 3.12 or newer was not found.
            echo Install Python, then follow docs\STARTUP_GUIDE_WINDOWS.md.
            pause
            exit /b 1
        )
    )
)

%PYTHON% -c "import streamlit, energy_routing" >nul 2>nul
if errorlevel 1 (
    echo Project dependencies or the project package are missing from the selected Python environment.
    echo Follow the one-time setup in docs\STARTUP_GUIDE_WINDOWS.md:
    echo   py -3.12 -m venv .venv
    echo   .venv\Scripts\python.exe -m pip install -r requirements.txt
    echo   .venv\Scripts\python.exe -m pip install -e .
    pause
    exit /b 1
)

echo Starting the WSN routing dashboard...
echo Keep this window open. Press Ctrl+C here to stop the dashboard.
%PYTHON% -m streamlit run src/energy_routing/dashboard.py
pause
endlocal
