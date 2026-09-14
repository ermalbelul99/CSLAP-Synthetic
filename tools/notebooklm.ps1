param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $NotebookLMArgs
)

$ErrorActionPreference = 'Stop'

$uvxCommand = Get-Command uvx -ErrorAction SilentlyContinue
$uvxPath = if ($uvxCommand) { $uvxCommand.Source } else { $null }

if (-not $uvxPath) {
    $candidatePaths = @(
        (Join-Path $env:USERPROFILE '.local\bin\uvx.exe')
    )
    if ($env:APPDATA) {
        $candidatePaths += @(Get-ChildItem -Path (Join-Path $env:APPDATA 'Python\Python*\Scripts\uvx.exe') -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
    }
    if ($env:LOCALAPPDATA) {
        $candidatePaths += @(Get-ChildItem -Path (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python*\Scripts\uvx.exe') -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
    }
    $uvxPath = $candidatePaths | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -Last 1
}

if (-not $uvxPath) {
    throw 'uvx was not found. Install uv with: py -m pip install --user uv; then run: py -m uv python install 3.12'
}

& $uvxPath --python 3.12 --from notebooklm-skill --with rookiepy notebooklm @NotebookLMArgs
exit $LASTEXITCODE
