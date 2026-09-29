$ErrorActionPreference = "Stop"
$project = Split-Path -Parent $PSScriptRoot
$buildVenv = Join-Path $project ".build-venv"
$python = (Get-Command python.exe -ErrorAction Stop).Source
if (-not (Test-Path (Join-Path $buildVenv "Scripts\python.exe"))) { & $python -m venv $buildVenv }
$venvPython = Join-Path $buildVenv "Scripts\python.exe"
& $venvPython -m pip install --disable-pip-version-check -r (Join-Path $project "build-requirements.txt")
Remove-Item -Recurse -Force (Join-Path $project "build"), (Join-Path $project "dist") -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path (Join-Path $project "release") | Out-Null
& $venvPython -m PyInstaller --clean --noconfirm (Join-Path $project "packaging\KMZPreview.spec")
$makensis = Get-Command makensis.exe -ErrorAction SilentlyContinue
$localMakensis = Join-Path $project ".tools\nsis-local\Bin\makensis.exe"
if ($makensis) { & $makensis.Source (Join-Path $project "packaging\installer.nsi") }
elseif (Test-Path $localMakensis) { & $localMakensis (Join-Path $project "packaging\installer.nsi") }
else { throw "NSIS makensis.exe was not found. Install NSIS or place its portable tools under .tools\nsis-local." }
if ($LASTEXITCODE -ne 0) { throw "NSIS failed to build release\install.exe (exit code $LASTEXITCODE)." }
Write-Host "Generated release\install.exe. The selected install folder will contain uninstall.exe."
