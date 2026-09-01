@echo off
REM Dubbelklik dit bestand om het bakkerijsysteem te starten op Windows.
cd /d "%~dp0bakkerijsysteem"

echo.
echo   Bakkerijsysteem
echo   ---------------
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo   Python staat niet op deze computer.
  echo   Haal het op bij python.org, vink bij het installeren "Add Python to PATH" aan,
  echo   en dubbelklik dit bestand opnieuw.
  echo.
  pause
  exit /b 1
)

if not exist data\grondstoffen.json (
  echo   Eerste keer: de voorbeeldgegevens klaarzetten...
  python seed.py
  echo.
  echo   Marktnoteringen ophalen...
  python markt.py
  echo.
)

python start.py
echo.
pause
