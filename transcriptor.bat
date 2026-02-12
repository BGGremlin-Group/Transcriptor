@echo off
setlocal
cd /d "%~dp0"

REM Prefer the Python Launcher (py) if available
where py >nul 2>nul
if %errorlevel%==0 (
  py transcriptor.py
  goto :done
)

REM Fallback to python
where python >nul 2>nul
if %errorlevel%==0 (
  python transcriptor.py
  goto :done
)

echo.
echo Python was not found.
echo Install Python from https://www.python.org/downloads/ and re-run.
echo.
pause

:done
echo.
pause
endlocal
