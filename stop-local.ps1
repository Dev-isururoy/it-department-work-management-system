$ErrorActionPreference='Stop'
$kelunPidFile=Join-Path $PSScriptRoot 'data\local-server.pid'
if (!(Test-Path -LiteralPath $kelunPidFile)) { Write-Output 'No background launcher PID file was found. Stop a foreground server with Ctrl+C.'; exit 0 }
$kelunProcessId=[int](Get-Content -LiteralPath $kelunPidFile -Raw)
$kelunProcess=Get-CimInstance Win32_Process -Filter "ProcessId=$kelunProcessId" -ErrorAction SilentlyContinue
$kelunPython=Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if ($kelunProcess -and $kelunProcess.CommandLine -like '*backend.run*' -and $kelunProcess.ExecutablePath -eq $kelunPython) {
    # Windows virtual-environment launchers can keep the real interpreter as a child.
    $kelunChildren=Get-CimInstance Win32_Process -Filter "ParentProcessId=$kelunProcessId"
    foreach ($kelunChild in $kelunChildren) {
        if ($kelunChild.CommandLine -like '*backend.run*') { Stop-Process -Id $kelunChild.ProcessId -ErrorAction SilentlyContinue }
    }
    Stop-Process -Id $kelunProcessId -ErrorAction SilentlyContinue
    Write-Output 'Kelun background process stopped. Data is retained. Check that all sync has finished before taking a backup.'
} else { Write-Output 'The recorded process is no longer the Kelun server; no process was stopped.' }
