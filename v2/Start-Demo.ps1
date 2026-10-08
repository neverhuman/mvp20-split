param(
    [ValidateSet('original', 'successor')][string]$Scenario = 'original',
    [ValidateRange(1, 86400)][int]$DurationSeconds = 86400,
    [string]$PreviewPublicDirectory,
    [switch]$NoBrowser
)
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
$demoRepo = Split-Path -Parent $PSScriptRoot
$demoPython = Join-Path $demoRepo '.test-results/acceptance-owner-final-b/environment/Scripts/python.exe'
$demoQualifiedScenario = 'frozen-' + $Scenario
$demoQualification = Join-Path $demoRepo ('.test-results/demo-20261008/' + $demoQualifiedScenario)
$demoRoot = 'C:/Users/alb_p/AppData/Local/Packages/PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0/LocalCache/Local/Amphora/local-v2/restore-20261007b'
$demoSession = Join-Path $demoRepo ('.test-results/demo-20261008/sessions/' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8))
if (!(Test-Path -LiteralPath $demoPython) -or !(Test-Path -LiteralPath (Join-Path $demoQualification 'evidence.json'))) {
    throw 'Qualified local demo installation is missing. See docs/Demo/2026-10-08 Internal Demo.md.'
}
$demoArgs = @((Join-Path $PSScriptRoot 'dev/present_local_demo.py'), '--qualification', $demoQualification,
    '--root', $demoRoot, '--output', $demoSession, '--duration', $DurationSeconds)
if (!$NoBrowser) { $demoArgs += '--open' }
if ($PreviewPublicDirectory) {
    $demoArgs += @('--preview-public', (Resolve-Path -LiteralPath $PreviewPublicDirectory).Path)
}
Write-Host 'Starting retained synthetic research walkthrough. No model charges or new campaign execution.'
Write-Host ('Session folder: ' + $demoSession)
Write-Host 'Keep this terminal open. Press Ctrl+C to stop before switching scenarios.'
& $demoPython @demoArgs
if ($LASTEXITCODE -ne 0) { throw 'Demo did not finish cleanly. Use the screenshot fallback and inspect this session before retrying.' }
