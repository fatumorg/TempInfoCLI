@echo off
REM Installs the TempInfoCLI shortcut (Desktop + Start Menu). Just double-click.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-shortcut.ps1"
pause
