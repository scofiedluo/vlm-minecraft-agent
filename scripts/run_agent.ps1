param(
    [string]$Mode = "dry-run",
    [int]$Steps = 5,
    [switch]$Once
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$onceArg = ""
if ($Once) {
    $onceArg = "--once"
}

conda run --no-capture-output -n vlm_minecraft python -u -m src.main --mode $Mode --steps $Steps $onceArg
