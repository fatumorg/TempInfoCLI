$ErrorActionPreference = "Stop"

$iconPath = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "assets\tempinfo.ico"

if (-not (Get-Command tempinfo -ErrorAction SilentlyContinue)) {
    Write-Warning "The 'tempinfo' command was not found on PATH."
    Write-Warning "Install it first - see the README's Install section. (Creating the shortcut anyway.)"
}

function New-TempInfoShortcut {
    param([Parameter(Mandatory)] [string]$Path)
    $shell    = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($Path)
    $shortcut.TargetPath       = "$env:WINDIR\System32\cmd.exe"
    $shortcut.Arguments        = "/K tempinfo"
    $shortcut.WorkingDirectory = "$env:USERPROFILE"
    $shortcut.Description      = "Live terminal temperature dashboard"
    if (Test-Path $iconPath) { $shortcut.IconLocation = "$iconPath,0" }
    $shortcut.Save()
    Write-Host "Created: $Path"
}

New-TempInfoShortcut -Path (Join-Path ([Environment]::GetFolderPath("Desktop")) "TempInfoCLI.lnk")

$startMenuDir = Join-Path ([Environment]::GetFolderPath("StartMenu")) "Programs\TempInfoCLI"
New-Item -ItemType Directory -Force -Path $startMenuDir | Out-Null
New-TempInfoShortcut -Path (Join-Path $startMenuDir "TempInfoCLI.lnk")

Write-Host "Done. TempInfoCLI now has a shortcut on the Desktop and in the Start Menu."
