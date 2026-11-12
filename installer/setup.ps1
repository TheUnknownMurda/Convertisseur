<#
  Convertisseur : installation des prérequis.

  Appelé par l'installateur, une étape à la fois. Peut aussi être lancé à la main pour réparer :
    powershell -ExecutionPolicy Bypass -File installer\setup.ps1 -Step python
  Étapes : python, ffmpeg, tools (-Names libreoffice,calibre,sevenzip,node), gpu, model, summary.
  Tout est noté dans installation.log, à la racine de l'application.
#>
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('python', 'ffmpeg', 'tools', 'elevated', 'gpu', 'model', 'summary')]
    [string]$Step,
    [string]$Names = '',
    [string]$LogFile = ''
)

$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
$App = Split-Path -Parent $PSScriptRoot
if (-not $LogFile) { $LogFile = Join-Path $App 'installation.log' }
$VenvPython = Join-Path $App '.venv\Scripts\python.exe'
$WingetLinks = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links'
$PipArgs = @('-m', 'pip', 'install', '--disable-pip-version-check', '--no-input', '--no-warn-script-location', '--progress-bar', 'off')

# Logiciels proposés par l'installateur (identifiants winget).
$Packages = [ordered]@{
    ffmpeg      = @{ Id = 'Gyan.FFmpeg'; Label = 'FFmpeg' }
    libreoffice = @{ Id = 'TheDocumentFoundation.LibreOffice'; Label = 'LibreOffice' }
    calibre     = @{ Id = 'calibre.calibre'; Label = 'Calibre' }
    sevenzip    = @{ Id = '7zip.7zip'; Label = '7-Zip' }
    node        = @{ Id = 'OpenJS.NodeJS.LTS'; Label = 'Node.js' }
}

# Accélération NVIDIA de la transcription (versions testées).
$CudaPackages = @('nvidia-cublas-cu12==12.9.2.10', 'nvidia-cudnn-cu12==9.28.1.4')

function Write-Log([string]$Message) {
    $line = '{0} [{1}] {2}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Step, $Message
    try { Add-Content -LiteralPath $LogFile -Value $line -Encoding UTF8 } catch { }
}

function Write-Output-ToLog {
    process {
        $text = "$_".TrimEnd()
        # winget affiche des barres de progression : on ne garde que les lignes utiles
        if ($text -and $text -notmatch '^[\s\-\\|/.]*$' -and $text -notmatch '[█▒]') { Write-Log "  $text" }
    }
}

function Update-Path {
    $parts = @([Environment]::GetEnvironmentVariable('Path', 'Machine'), [Environment]::GetEnvironmentVariable('Path', 'User')) |
        Where-Object { $_ }
    $env:Path = $parts -join ';'
}

function Find-First([object[]]$Paths) {
    foreach ($p in $Paths) {
        if ($p -and (Test-Path -LiteralPath $p -PathType Leaf)) { return [string]$p }
    }
    return $null
}

function Find-OnPath([string]$Exe) {
    $cmd = Get-Command $Exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($cmd) { return $cmd.Source }
    return $null
}

$ProgramDirs = @($env:ProgramFiles, $env:ProgramW6432, ${env:ProgramFiles(x86)}, $env:LOCALAPPDATA) |
    Where-Object { $_ } | Select-Object -Unique

function In-ProgramFiles([string]$Relative) {
    return @($ProgramDirs | ForEach-Object { Join-Path $_ $Relative })
}

# Mêmes emplacements que ceux cherchés par l'application (convertisseur\tools.py).
function Find-Tool([string]$Name) {
    switch ($Name) {
        'ffmpeg' { return Find-First (@((Join-Path $App 'bin\ffmpeg.exe'), (Find-OnPath 'ffmpeg.exe'), (Join-Path $WingetLinks 'ffmpeg.exe'))) }
        'libreoffice' { return Find-First (In-ProgramFiles 'LibreOffice\program\soffice.exe') }
        'calibre' { return Find-First ((In-ProgramFiles 'Calibre2\ebook-convert.exe') + (In-ProgramFiles 'Calibre\ebook-convert.exe')) }
        'sevenzip' { return Find-First (In-ProgramFiles '7-Zip\7z.exe') }
        'node' { return Find-First (@((Find-OnPath 'node.exe')) + (In-ProgramFiles 'nodejs\node.exe') + @((Join-Path $WingetLinks 'node.exe'))) }
    }
    return $null
}

function Get-Winget {
    $found = Find-OnPath 'winget.exe'
    if ($found) { return $found }
    return Find-First @((Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps\winget.exe'))
}

function Invoke-Winget([string]$Id) {
    $winget = Get-Winget
    if (-not $winget) {
        Write-Log "winget est introuvable : $Id n'a pas pu être installé automatiquement."
        return 1
    }
    $arguments = @('install', '--id', $Id, '--exact', '--source', 'winget', '--silent', '--disable-interactivity',
        '--accept-package-agreements', '--accept-source-agreements')
    Write-Log ('winget ' + ($arguments -join ' '))
    & $winget @arguments 2>&1 | Write-Output-ToLog
    $code = $LASTEXITCODE
    Write-Log "winget a terminé (code $code)."
    Update-Path
    return $code
}

function Find-Python {
    foreach ($hive in @('HKCU:', 'HKLM:')) {
        $key = "$hive\Software\Python\PythonCore\3.13\InstallPath"
        if (Test-Path $key) {
            $props = Get-ItemProperty -Path $key
            $exe = $props.ExecutablePath
            if (-not $exe -and $props.'(default)') { $exe = Join-Path $props.'(default)' 'python.exe' }
            if ($exe -and (Test-Path -LiteralPath $exe)) { return [string]$exe }
        }
    }
    $found = Find-First @((Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe'), (Join-Path $env:ProgramFiles 'Python313\python.exe'))
    if ($found) { return $found }
    $launcher = Find-OnPath 'py.exe'
    if ($launcher) {
        $exe = & $launcher -3.13 -c 'import sys; print(sys.executable)' 2>$null
        if ($LASTEXITCODE -eq 0 -and $exe) { return ("$exe").Trim() }
    }
    return $null
}

function Test-AppModules {
    if (-not (Test-Path -LiteralPath $VenvPython)) { return $false }
    & $VenvPython -c 'import flask, pymupdf, PIL, pillow_heif, pdf2docx, openpyxl, pptx, faster_whisper, yt_dlp, pysubs2, fontTools, yaml, segno, barcode, zxingcpp' 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)
}

function Install-PythonEnvironment {
    $python = Find-Python
    if (-not $python) {
        Write-Log 'Python 3.13 est absent : installation avec winget.'
        Invoke-Winget 'Python.Python.3.13' | Out-Null
        $python = Find-Python
    }
    if (-not $python) {
        Write-Log 'ÉCHEC : Python 3.13 est introuvable. Installez-le depuis https://www.python.org puis relancez l''installateur.'
        return 3
    }
    Write-Log "Python : $python"
    if (-not (Test-Path -LiteralPath $VenvPython)) {
        & $python -m venv (Join-Path $App '.venv') 2>&1 | Write-Output-ToLog
    }
    if (-not (Test-Path -LiteralPath $VenvPython)) {
        Write-Log 'ÉCHEC : l''environnement Python n''a pas pu être créé.'
        return 4
    }
    & $VenvPython @PipArgs --upgrade pip 2>&1 | Write-Output-ToLog
    & $VenvPython @PipArgs -r (Join-Path $App 'requirements-lock.txt') 2>&1 | Write-Output-ToLog
    if ($LASTEXITCODE -ne 0) {
        Write-Log 'Les versions testées n''ont pas pu être installées : nouvel essai avec les versions récentes.'
        & $VenvPython @PipArgs -r (Join-Path $App 'requirements.txt') 2>&1 | Write-Output-ToLog
    }
    if (Test-AppModules) {
        Write-Log 'Modules Python prêts.'
        return 0
    }
    Write-Log 'ÉCHEC : certains modules Python manquent (voir les lignes ci-dessus).'
    return 5
}

function Install-Tools([string[]]$Wanted) {
    $missing = @()
    foreach ($name in $Wanted) {
        if (-not $Packages.Contains($name)) { continue }
        $where = Find-Tool $name
        if ($where) { Write-Log "$($Packages[$name].Label) : déjà installé ($where)." }
        else { $missing += $name }
    }
    if (-not $missing.Count) { return 0 }
    Write-Log ('À installer avec l''autorisation administrateur : ' + (($missing | ForEach-Object { $Packages[$_].Label }) -join ', '))
    $arguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`"", '-Step', 'elevated',
        '-Names', ($missing -join ','), '-LogFile', "`"$LogFile`"")
    try {
        # Une seule demande d'autorisation Windows pour tous les logiciels
        $proc = Start-Process -FilePath (Join-Path $PSHOME 'powershell.exe') -ArgumentList $arguments -Verb RunAs `
            -WindowStyle Hidden -Wait -PassThru
        Write-Log "Installation administrateur terminée (code $($proc.ExitCode))."
    }
    catch {
        Write-Log "Autorisation administrateur refusée ou impossible : $($_.Exception.Message)"
    }
    Update-Path
    foreach ($name in $missing) {
        $where = Find-Tool $name
        if ($where) { Write-Log "$($Packages[$name].Label) : installé ($where)." }
        else { Write-Log "$($Packages[$name].Label) : non installé." }
    }
    return 0
}

function Test-Nvidia {
    if (Test-Path -LiteralPath (Join-Path $env:SystemRoot 'System32\nvidia-smi.exe')) { return $true }
    try {
        return [bool](Get-CimInstance Win32_VideoController -ErrorAction Stop | Where-Object { $_.Name -like '*NVIDIA*' })
    }
    catch { return $false }
}

Write-Log '----- début'
$code = 0
switch ($Step) {
    'python' {
        $code = Install-PythonEnvironment
    }
    'ffmpeg' {
        $where = Find-Tool 'ffmpeg'
        if ($where) { Write-Log "FFmpeg : déjà installé ($where)." }
        else {
            Invoke-Winget $Packages['ffmpeg'].Id | Out-Null
            $where = Find-Tool 'ffmpeg'
            if ($where) { Write-Log "FFmpeg : installé ($where)." } else { Write-Log 'FFmpeg : non installé.'; $code = 1 }
        }
    }
    'tools' {
        $code = Install-Tools ($Names -split ',' | Where-Object { $_ })
    }
    'elevated' {
        foreach ($name in ($Names -split ',' | Where-Object { $_ })) {
            if ($Packages.Contains($name)) { Invoke-Winget $Packages[$name].Id | Out-Null }
        }
    }
    'gpu' {
        if (-not (Test-Nvidia)) { Write-Log 'Aucune carte NVIDIA détectée : étape ignorée.' }
        elseif (-not (Test-Path -LiteralPath $VenvPython)) { Write-Log 'Environnement Python absent : étape ignorée.'; $code = 4 }
        else {
            & $VenvPython @PipArgs @CudaPackages 2>&1 | Write-Output-ToLog
            $code = $LASTEXITCODE
            Write-Log "Bibliothèques NVIDIA : code $code."
        }
    }
    'model' {
        if (-not (Test-Path -LiteralPath $VenvPython)) { Write-Log 'Environnement Python absent : étape ignorée.'; $code = 4 }
        else {
            $env:CONVERTISSEUR_MODELES = Join-Path $App 'modeles\whisper'
            & $VenvPython -c "import os; from faster_whisper import download_model; print(download_model('small', cache_dir=os.environ['CONVERTISSEUR_MODELES']))" 2>&1 |
                Write-Output-ToLog
            $code = $LASTEXITCODE
            Write-Log "Modèle de transcription : code $code."
        }
    }
    'summary' {
        # Résumé lu par l'installateur pour sa dernière page (ASCII : clé=état).
        $lines = @('python=' + $(if (Test-AppModules) { 'ok' } else { 'absent' }))
        foreach ($name in $Packages.Keys) { $lines += "$name=" + $(if (Find-Tool $name) { 'ok' } else { 'absent' }) }
        $lines += 'nvidia=' + $(if (Test-Nvidia) { 'ok' } else { 'absent' })
        Set-Content -LiteralPath (Join-Path $App 'installation-resume.txt') -Value $lines -Encoding ASCII
        $lines | ForEach-Object { Write-Log $_ }
    }
}
Write-Log "----- fin (code $code)"
exit $code
