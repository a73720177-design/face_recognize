$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
& "$taskRoot\.venv\Scripts\python.exe" "$taskRoot\py\recognition.py" @args
exit $LASTEXITCODE
