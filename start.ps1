param([string]$Python = 'python')
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
if (!(Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    & $Python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 or later is required. Install Python or pass -Python with its full path.' }
}
& '.\.venv\Scripts\python.exe' -m pip install -r requirements-lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
if (!(Test-Path -LiteralPath '.env')) { Copy-Item -LiteralPath '.env.example' -Destination '.env' }
& '.\.venv\Scripts\python.exe' scripts/manage.py setup-key
& '.\.venv\Scripts\python.exe' -m backend.run
