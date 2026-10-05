@echo off
setlocal
cd /d "%~dp0"

set "PYEXE="

REM 1) Standard Python launcher / PATH
for %%P in (py.exe python.exe python3.exe) do (
  where %%P >nul 2>nul
  if not errorlevel 1 (
    for /f "delims=" %%I in ('where %%P 2^>nul') do (
      if not defined PYEXE set "PYEXE=%%I"
    )
  )
)

REM 2) Microsoft Store Python 3.12 package
if not defined PYEXE (
  for /d %%D in ("%LOCALAPPDATA%\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_*") do (
    if exist "%%D\python.exe" set "PYEXE=%%D\python.exe"
  )
)

REM 3) WindowsApps alias
if not defined PYEXE (
  if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\python3.12.exe" set "PYEXE=%LOCALAPPDATA%\Microsoft\WindowsApps\python3.12.exe"
)
if not defined PYEXE (
  if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" set "PYEXE=%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe"
)

REM 4) Common local install locations
if not defined PYEXE (
  for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python312*" "%ProgramFiles%\Python312*") do (
    if exist "%%D\python.exe" set "PYEXE=%%D\python.exe"
  )
)

if not defined PYEXE (
  echo.
  echo [TRIPICK] Python 3.12 was not found automatically.
  echo Open Python 3.12 once from Windows Search, close it, and try again.
  echo.
  pause
  exit /b 1
)

echo [TRIPICK] Python found:
echo "%PYEXE%"
echo.

"%PYEXE%" -c "import sys; print('[TRIPICK] Python', sys.version)"
if errorlevel 1 (
  echo Python was found but could not be started.
  pause
  exit /b 1
)

echo.
echo [TRIPICK] Installing required packages...
"%PYEXE%" -m ensurepip --upgrade >nul 2>nul
"%PYEXE%" -m pip install --upgrade pip
"%PYEXE%" -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo Package installation failed.
  pause
  exit /b 1
)

echo.
echo [TRIPICK] Starting app...
"%PYEXE%" -m streamlit run app.py
pause
