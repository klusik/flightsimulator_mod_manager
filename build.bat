@echo off
setlocal EnableExtensions

cd /d "%~dp0"

set "APP_NAME=FlightSimulatorModManager"
set "ENTRY_POINT=src\fs24_mod_manager\__main__.py"
set "OUTPUT_DIR=dist"
set "OUTPUT_EXE=%OUTPUT_DIR%\%APP_NAME%.exe"
set "BUILD_REQUIREMENTS=requirements-build.txt"
set "BUILD_ROOT=%TEMP%\fs24-mod-manager-build-%RANDOM%-%RANDOM%"

if not exist "%ENTRY_POINT%" (
    echo ERROR: Application entry point not found: %ENTRY_POINT%
    echo Implement the application entry point before running the executable build.
    exit /b 1
)

if not exist "%BUILD_REQUIREMENTS%" (
    echo ERROR: Build requirements not found: %BUILD_REQUIREMENTS%
    exit /b 1
)

where py.exe >nul 2>nul
if errorlevel 1 (
    echo ERROR: The Python launcher ^(py.exe^) was not found.
    echo Install Python 3.13 or newer and try again.
    exit /b 1
)

py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 13) else 1)" >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python 3.13 or newer is required.
    exit /b 1
)

if exist "%BUILD_ROOT%" (
    echo ERROR: Refusing to reuse temporary build directory: %BUILD_ROOT%
    exit /b 1
)

mkdir "%BUILD_ROOT%"
if errorlevel 1 (
    echo ERROR: Could not create temporary build directory: %BUILD_ROOT%
    exit /b 1
)

echo Creating isolated Python build environment...
py -3 -m venv "%BUILD_ROOT%\venv"
if errorlevel 1 goto :build_failed

echo Installing application and build dependencies...
"%BUILD_ROOT%\venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt -r "%BUILD_REQUIREMENTS%"
if errorlevel 1 goto :build_failed

echo Building %APP_NAME%.exe...
"%BUILD_ROOT%\venv\Scripts\python.exe" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --windowed ^
    --name "%APP_NAME%" ^
    --paths "src" ^
    --workpath "%BUILD_ROOT%\work" ^
    --specpath "%BUILD_ROOT%\spec" ^
    --distpath "%BUILD_ROOT%\output" ^
    "%ENTRY_POINT%"
if errorlevel 1 goto :build_failed

if not exist "%BUILD_ROOT%\output\%APP_NAME%.exe" (
    echo ERROR: PyInstaller completed without producing the expected executable.
    goto :build_failed
)

if not exist "%OUTPUT_DIR%" (
    mkdir "%OUTPUT_DIR%"
    if errorlevel 1 goto :build_failed
)

if exist "%OUTPUT_EXE%" (
    del /f /q "%OUTPUT_EXE%"
    if errorlevel 1 (
        echo ERROR: Could not replace existing executable: %OUTPUT_EXE%
        goto :build_failed
    )
)

move /y "%BUILD_ROOT%\output\%APP_NAME%.exe" "%OUTPUT_EXE%" >nul
if errorlevel 1 goto :build_failed

call :cleanup
if errorlevel 1 exit /b 1

echo Build completed successfully:
echo %CD%\%OUTPUT_EXE%
exit /b 0

:build_failed
set "BUILD_EXIT_CODE=%ERRORLEVEL%"
if "%BUILD_EXIT_CODE%"=="0" set "BUILD_EXIT_CODE=1"
echo ERROR: Executable build failed.
call :cleanup
exit /b %BUILD_EXIT_CODE%

:cleanup
if not exist "%BUILD_ROOT%" exit /b 0

echo Cleaning temporary build files...
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ErrorActionPreference = 'Stop';" ^
    "$temporaryRoot = [IO.Path]::GetFullPath([Environment]::GetEnvironmentVariable('TEMP'));" ^
    "$buildRoot = [IO.Path]::GetFullPath('%BUILD_ROOT%');" ^
    "$expectedPrefix = [IO.Path]::Combine($temporaryRoot, 'fs24-mod-manager-build-');" ^
    "if (-not $buildRoot.StartsWith($expectedPrefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe temporary build path.' };" ^
    "Remove-Item -LiteralPath $buildRoot -Recurse -Force"
if errorlevel 1 (
    echo ERROR: Temporary build cleanup failed: %BUILD_ROOT%
    exit /b 1
)
exit /b 0
