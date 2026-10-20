#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

DESKTOP_SRC="$SCRIPT_DIR/tempinfocli.desktop"
ICON_SRC="$REPO_ROOT/assets/icon.png"

APPS_DIR="$HOME/.local/share/applications"
ICONS_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"

mkdir -p "$APPS_DIR" "$ICONS_DIR"

if ! command -v tempinfocli >/dev/null 2>&1; then
    echo "Note: the 'tempinfocli' command was not found on your PATH."
    echo "Install it first - see the README's Install section."
    echo "(Installing the shortcut anyway - it will start working once 'tempinfocli' is on PATH.)"
fi

cp "$ICON_SRC" "$ICONS_DIR/tempinfocli.png"
cp "$DESKTOP_SRC" "$APPS_DIR/tempinfocli.desktop"
chmod +x "$APPS_DIR/tempinfocli.desktop"

command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPS_DIR" || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

echo "Done. TempInfoCLI should now appear in your application menu with its icon."
