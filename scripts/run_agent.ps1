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

conda run -n vlm_minecraft python -m src.main --mode $Mode --steps $Steps $onceArg
