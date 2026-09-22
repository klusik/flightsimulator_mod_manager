@echo off
setlocal EnableExtensions

cd /d "%~dp0"

set "APP_VERSION=%~1"
if not defined APP_VERSION set "APP_VERSION=0.1.0"
set "INNO_SCRIPT=packaging\installer.iss"
set "ISCC_PATH="
set "ISCC_MAJOR="

echo Building application executable...
call build.bat
if errorlevel 1 (
    echo ERROR: Application build failed; installer was not created.
    exit /b 1
)

if not exist "%INNO_SCRIPT%" (
    echo ERROR: Installer definition not found: %INNO_SCRIPT%
    exit /b 1
)

if exist "%ProgramFiles%\Inno Setup 7\ISCC.exe" set "ISCC_PATH=%ProgramFiles%\Inno Setup 7\ISCC.exe"
if not defined ISCC_PATH if exist "%ProgramFiles(x86)%\Inno Setup 7\ISCC.exe" set "ISCC_PATH=%ProgramFiles(x86)%\Inno Setup 7\ISCC.exe"
if not defined ISCC_PATH if exist "%LOCALAPPDATA%\Programs\Inno Setup 7\ISCC.exe" set "ISCC_PATH=%LOCALAPPDATA%\Programs\Inno Setup 7\ISCC.exe"
if not defined ISCC_PATH if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC_PATH if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC_PATH if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
for /f "delims=" %%I in ('where ISCC.exe 2^>nul') do if not defined ISCC_PATH set "ISCC_PATH=%%I"

if not defined ISCC_PATH (
    echo ERROR: Inno Setup compiler ^(ISCC.exe^) was not found.
    echo Install Inno Setup from https://jrsoftware.org/isdl.php and run this script again.
    exit /b 1
)

echo %ISCC_PATH% | findstr /I /C:"Inno Setup 7" >nul
if errorlevel 1 (set "ISCC_MAJOR=6") else (set "ISCC_MAJOR=7")

echo Building installer version %APP_VERSION%...
if "%ISCC_MAJOR%"=="7" (
    "%ISCC_PATH%" --quiet-progress "--define=AppVersion=%APP_VERSION%" "%INNO_SCRIPT%"
) else (
    "%ISCC_PATH%" /Qp "/DAppVersion=%APP_VERSION%" "%INNO_SCRIPT%"
)
if errorlevel 1 (
    echo ERROR: Installer compilation failed.
    exit /b 1
)

set "INSTALLER_PATH=dist\FlightSimulatorModManager-%APP_VERSION%-Setup.exe"
if not exist "%INSTALLER_PATH%" (
    echo ERROR: Compiler completed without producing the expected installer.
    exit /b 1
)

echo Installer created successfully:
echo %CD%\%INSTALLER_PATH%
exit /b 0
