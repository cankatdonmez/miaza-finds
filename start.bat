@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
title miaza finds - Testserver

rem ---------------------------------------------------------------
rem  miaza finds lokal auf diesem Windows-Rechner starten (wie miaza counts).
rem  Doppelklick genuegt. Fenster schliessen = Server beenden.
rem  Code liegt im Drive-Ordner; Python-Umgebung und Daten ausserhalb (D-008):
rem  %USERPROFILE%\miaza-local\finds
rem ---------------------------------------------------------------

set "LOKAL=%USERPROFILE%\miaza-local\finds"
set "VENV=%LOKAL%\.venv"
set "PORT=8090"
set "PYTHONDONTWRITEBYTECODE=1"

set "PY="
py -3 --version >nul 2>nul && set "PY=py -3"
if not defined PY python --version >nul 2>nul && set "PY=python"
if not defined PY (
  echo.
  echo  Python wurde nicht gefunden.
  echo  Bitte Python 3.12 oder neuer von https://www.python.org/downloads/ installieren
  echo  und beim Installieren "Add python.exe to PATH" anhaken.
  echo.
  pause
  exit /b 1
)

if not exist "%VENV%\Scripts\python.exe" (
  echo  Erste Einrichtung: Python-Umgebung wird angelegt ...
  if not exist "%LOKAL%" mkdir "%LOKAL%"
  %PY% -m venv "%VENV%" || goto :fehler
)

rem Pakete nur installieren, wenn sich requirements.txt geaendert hat.
fc /b requirements.txt "%VENV%\installiert.txt" >nul 2>nul
if errorlevel 1 (
  echo  Pakete werden installiert, das dauert beim ersten Mal 1-2 Minuten ...
  "%VENV%\Scripts\python.exe" -m pip install --disable-pip-version-check -q --upgrade pip || goto :fehler
  "%VENV%\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt || goto :fehler
  copy /y requirements.txt "%VENV%\installiert.txt" >nul
)

rem Laeuft noch ein alter finds-Server auf Port 8090? Dann beenden,
rem sonst zeigt der Browser weiter die alte Version an.
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /r /c:":%PORT% .*LISTENING"') do call :alt_beenden %%p
if defined BELEGT goto :belegt

set "MF_DB_PATH=%LOKAL%\data\finds.db"
set "MF_MEDIA_DIR=%LOKAL%\media"
set "MF_BACKUP_DIR=%LOKAL%\backups"

rem Nur dieser Rechner (127.0.0.1). Fuer Tests mit dem Telefon im Buero
rem start.bat netz  aufrufen; dann fragt die Windows-Firewall einmal nach.
set "HOST=127.0.0.1"
if /i "%~1"=="netz" set "HOST=0.0.0.0"

set "URL=http://localhost:%PORT%"
set "BROWSER="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "BROWSER=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not defined BROWSER if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "BROWSER=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not defined BROWSER if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set "BROWSER=%LocalAppData%\Google\Chrome\Application\chrome.exe"
if not defined BROWSER if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" set "BROWSER=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"

echo.
echo  miaza finds laeuft auf %URL%
echo  Datenbank:             %MF_DB_PATH%
echo  Zum Beenden dieses Fenster schliessen oder Strg+C druecken.
echo.

rem Browser nach 3 Sekunden oeffnen (dann laeuft der Server schon).
if defined BROWSER (
  start "" /min powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep 3; Start-Process -FilePath '%BROWSER%' -ArgumentList '--app=%URL%','--window-size=1200,860'"
) else (
  start "" /min powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep 3; Start-Process '%URL%'"
)

:server
"%VENV%\Scripts\python.exe" -m uvicorn --factory app.main:create_app --host %HOST% --port %PORT%
rem Exit-Code 3 = Neustart erbeten (spaeter: nach "Wiederherstellen" im Systembereich)
if errorlevel 3 if not errorlevel 4 (
  echo.
  echo  Neustart ...
  echo.
  goto :server
)
goto :eof

:alt_beenden
rem Gleiche PID kann zweimal kommen (IPv4/IPv6); bereits beendet = nichts zu tun.
tasklist /FI "PID eq %1" 2>nul | find "%1" >nul || goto :eof
tasklist /FI "PID eq %1" 2>nul | find /i "python" >nul
if errorlevel 1 (
  set "BELEGT=%1"
  goto :eof
)
echo  Ein aelterer finds-Server lief noch, PID %1. Er wird beendet ...
taskkill /F /PID %1 >nul 2>nul
timeout /t 2 /nobreak >nul
goto :eof

:belegt
echo.
echo  Port %PORT% ist von einem anderen Programm belegt, PID %BELEGT%.
echo  Bitte dieses Programm beenden und start.bat erneut aufrufen.
pause
exit /b 1

:fehler
echo.
echo  Etwas ist schiefgegangen. Die Meldung oben zeigt den Grund.
pause
exit /b 1
