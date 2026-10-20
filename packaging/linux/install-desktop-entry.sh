#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

DESKTOP_SRC="$SCRIPT_DIR/tempinfo.desktop"

APPS_DIR="$HOME/.local/share/applications"
ICONS_DIR="$HOME/.local/share/icons/hicolor"

mkdir -p "$APPS_DIR" "$ICONS_DIR/scalable/apps" "$ICONS_DIR/256x256/apps"

if ! command -v tempinfo >/dev/null 2>&1; then
    echo "Note: the 'tempinfo' command was not found on your PATH."
    echo "Install it first - see the README's Install section."
    echo "(Installing the shortcut anyway - it will start working once 'tempinfo' is on PATH.)"
fi

cp "$REPO_ROOT/assets/tempinfo.svg" "$ICONS_DIR/scalable/apps/tempinfo.svg"
cp "$REPO_ROOT/assets/tempinfo-256.png" "$ICONS_DIR/256x256/apps/tempinfo.png"
cp "$DESKTOP_SRC" "$APPS_DIR/tempinfo.desktop"

command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPS_DIR" || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache "$ICONS_DIR" 2>/dev/null || true

echo "Done. TempInfoCLI should now appear in your application menu with its icon."
