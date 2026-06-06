param(
  [string]$PythonEnv = "vlm_minecraft",
  [int]$Steps = 5,
  [switch]$NoVLM
)

$ErrorActionPreference = "Stop"

Write-Host "[run_all] starting Node skill server..."
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot/../bot'; npm start"

Start-Sleep -Seconds 2

$noVlmArg = ""
if ($NoVLM) { $noVlmArg = "--no-vlm" }

Write-Host "[run_all] starting Python layered agent..."
$cmd = "conda run --no-capture-output -n $PythonEnv python -u -m src.main --steps $Steps $noVlmArg"
Invoke-Expression $cmd
