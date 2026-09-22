@echo off
setlocal EnableExtensions

cd /d "%~dp0"

set "OUTPUT_DIR=dist"
set "ARCHIVE_NAME=flightsimulator_mod_manager.zip"
set "ARCHIVE_PATH=%OUTPUT_DIR%\%ARCHIVE_NAME%"

if not exist "src\fs24_mod_manager\__init__.py" (
    echo ERROR: Application package not found: src\fs24_mod_manager
    exit /b 1
)

for %%F in (README.md SPECIFICATION.md pyproject.toml requirements.txt .python-version) do (
    if not exist "%%F" (
        echo ERROR: Required deployment file not found: %%F
        exit /b 1
    )
)

if not exist "%OUTPUT_DIR%" (
    mkdir "%OUTPUT_DIR%"
    if errorlevel 1 (
        echo ERROR: Could not create output directory: %OUTPUT_DIR%
        exit /b 1
    )
)

if exist "%ARCHIVE_PATH%" (
    del /f /q "%ARCHIVE_PATH%"
    if errorlevel 1 (
        echo ERROR: Could not replace existing archive: %ARCHIVE_PATH%
        exit /b 1
    )
)

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ErrorActionPreference = 'Stop';" ^
    "$deploymentFiles = @('src', 'README.md', 'SPECIFICATION.md', 'pyproject.toml', 'requirements.txt', '.python-version');" ^
    "if (Test-Path -LiteralPath 'LICENSE') { $deploymentFiles += 'LICENSE' };" ^
    "Compress-Archive -LiteralPath $deploymentFiles -DestinationPath '%ARCHIVE_PATH%' -CompressionLevel Optimal -Force"

if errorlevel 1 (
    echo ERROR: Deployment archive creation failed.
    exit /b 1
)

echo Deployment archive created successfully:
echo %CD%\%ARCHIVE_PATH%
exit /b 0
