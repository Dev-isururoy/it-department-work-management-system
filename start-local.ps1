# Start the already-installed application quietly on this computer.
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
$kelunPython=Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $kelunPython)) { throw 'Run start.ps1 once to install the application first.' }
$kelunRunFolder=Join-Path $PSScriptRoot 'data'
New-Item -ItemType Directory -Force -Path $kelunRunFolder | Out-Null
$kelunPidFile=Join-Path $kelunRunFolder 'local-server.pid'
if (Test-Path -LiteralPath $kelunPidFile) {
    $kelunPreviousId=[int](Get-Content -LiteralPath $kelunPidFile -Raw)
    $kelunPrevious=Get-CimInstance Win32_Process -Filter "ProcessId=$kelunPreviousId" -ErrorAction SilentlyContinue
    if ($kelunPrevious -and $kelunPrevious.CommandLine -like '*backend.run*' -and $kelunPrevious.ExecutablePath -eq $kelunPython) { Write-Output 'Kelun is already running. Open http://127.0.0.1:8000'; exit 0 }
}
if (!(Test-Path -LiteralPath '.env')) { Copy-Item -LiteralPath '.env.example' -Destination '.env' }
if (Select-String -LiteralPath (Join-Path $PSScriptRoot '.env') -Pattern '^AI_PROVIDER=ollama$' -Quiet) {
    $kelunOllama=Get-Command ollama -ErrorAction SilentlyContinue
    if ($kelunOllama) {
        try { Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 3 | Out-Null }
        catch { Start-Process -FilePath $kelunOllama.Source -ArgumentList 'serve' -WindowStyle Hidden | Out-Null }
    }
}
& $kelunPython scripts/manage.py setup-key
$kelunProcess=Start-Process -FilePath $kelunPython -ArgumentList '-m','backend.run' -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $kelunRunFolder 'local-server.log') -RedirectStandardError (Join-Path $kelunRunFolder 'local-server-error.log') -PassThru
Set-Content -LiteralPath $kelunPidFile -Value $kelunProcess.Id
Write-Output 'Kelun started. Default address: http://127.0.0.1:8000. Stop it with .\stop-local.ps1. Check data\local-server-error.log if it does not open.'
