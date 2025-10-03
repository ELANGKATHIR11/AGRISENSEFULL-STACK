# Local CI helper: create venv, install backend deps and run tests
param(
  [switch]$InstallML
)

$ErrorActionPreference = 'Stop'
$repo = Resolve-Path .
$venv = Join-Path $repo '.venv-ci'
if (-Not (Test-Path $venv)) {
    python -m venv $venv
}
$python = Join-Path $venv 'Scripts\python.exe'
& $python -m pip install --upgrade pip
if (Test-Path "agrisense_app/backend/requirements-dev.txt") {
    & $python -m pip install -r agrisense_app/backend/requirements-dev.txt
} else {
    & $python -m pip install -r agrisense_app/backend/requirements.txt
}
if ($InstallML -and (Test-Path "agrisense_app/backend/requirements-ml.txt")) {
    & $python -m pip install -r agrisense_app/backend/requirements-ml.txt
}
# Run tests with ML disabled by default
$env:AGRISENSE_DISABLE_ML = '1'
& $python -m pytest -q
