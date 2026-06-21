param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$ArgsFromUser
)

$ErrorActionPreference = "Stop"
$scriptPath = Join-Path $PSScriptRoot "..\skills\videogen\scripts\videogen.py"
python $scriptPath @ArgsFromUser
exit $LASTEXITCODE
