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

for %%F in (README.md SPECIFICATION.md ARCHITECTURE.md pyproject.toml requirements.txt requirements-build.txt build.bat installer.bat) do (
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
    "$deploymentFiles = @('src', 'packaging', 'README.md', 'SPECIFICATION.md', 'ARCHITECTURE.md', 'pyproject.toml', 'requirements.txt', 'requirements-build.txt', 'build.bat', 'installer.bat');" ^
    "if (Test-Path -LiteralPath 'LICENSE') { $deploymentFiles += 'LICENSE' };" ^
    "$temporaryRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath());" ^
    "$staging = Join-Path $temporaryRoot ('fs24-mod-manager-deploy-' + [guid]::NewGuid().ToString('N'));" ^
    "try {" ^
    "  New-Item -ItemType Directory -Path $staging | Out-Null;" ^
    "  foreach ($item in $deploymentFiles) { $name = [IO.Path]::GetFileName($item.TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)); Copy-Item -LiteralPath $item -Destination (Join-Path $staging $name) -Recurse };" ^
    "  Get-ChildItem -LiteralPath $staging -Directory -Filter '__pycache__' -Recurse | Remove-Item -Recurse -Force;" ^
    "  Get-ChildItem -LiteralPath $staging -File -Recurse | Where-Object { $_.Extension -in '.pyc', '.pyo' } | Remove-Item -Force;" ^
    "  $archiveItems = @(Get-ChildItem -LiteralPath $staging | Select-Object -ExpandProperty FullName);" ^
    "  Compress-Archive -LiteralPath $archiveItems -DestinationPath '%ARCHIVE_PATH%' -CompressionLevel Optimal -Force;" ^
    "} finally {" ^
    "  $resolved = [IO.Path]::GetFullPath($staging);" ^
    "  $prefix = [IO.Path]::Combine($temporaryRoot, 'fs24-mod-manager-deploy-');" ^
    "  if ($resolved.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase) -and (Test-Path -LiteralPath $resolved)) { Remove-Item -LiteralPath $resolved -Recurse -Force };" ^
    "}"

if errorlevel 1 (
    echo ERROR: Deployment archive creation failed.
    exit /b 1
)

echo Deployment archive created successfully:
echo %CD%\%ARCHIVE_PATH%
exit /b 0
