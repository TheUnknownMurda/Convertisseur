# Compile l'installateur : dist\Convertisseur-Setup-<version>.exe
#   powershell -ExecutionPolicy Bypass -File installer\build.ps1
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$match = Select-String -LiteralPath (Join-Path $root 'convertisseur\__init__.py') -Pattern '__version__\s*=\s*"([^"]+)"'
if (-not $match) { throw 'Version introuvable dans convertisseur\__init__.py' }
$version = $match.Matches[0].Groups[1].Value

$candidates = @(
    (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'),
    (Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'),
    (Join-Path $env:ProgramFiles 'Inno Setup 6\ISCC.exe')
)
$iscc = $candidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
if (-not $iscc) { throw 'Inno Setup 6 est introuvable : https://jrsoftware.org/isdl.php' }

Write-Host "Convertisseur $version - compilation avec $iscc"
& $iscc "/DAppVersion=$version" (Join-Path $PSScriptRoot 'Convertisseur.iss')
exit $LASTEXITCODE
