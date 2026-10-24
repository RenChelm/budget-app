#!/usr/bin/env bash
# Creates desktop icons (and app-menu entries) that open a terminal and run
# run_on_emulator.sh. Re-run if you move the project folder.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/config.sh"

run_script="$PROJECT_DIR/scripts/emulator/run_on_emulator.sh"
icon="$PROJECT_DIR/assets/images/icon.png"
desktop_dir="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
apps_dir="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$desktop_dir" "$apps_dir"

# Wrap the command in whichever terminal is installed so logs stay visible.
terminal_exec() {
    if command -v gnome-terminal >/dev/null; then
        echo "gnome-terminal --title=\"$1\" -- \"$run_script\" $2 --hold"
    elif command -v ptyxis >/dev/null; then
        echo "ptyxis --new-window -- \"$run_script\" $2 --hold"
    elif command -v konsole >/dev/null; then
        echo "konsole -e \"$run_script\" $2 --hold"
    else
        echo "x-terminal-emulator -e \"$run_script\" $2 --hold"
    fi
}

write_launcher() {  # file-id, name, comment, run_on_emulator.sh flags
    local file="$apps_dir/$1.desktop"
    cat > "$file" <<EOF
[Desktop Entry]
Type=Application
Name=$2
Comment=$3
Exec=$(terminal_exec "$2" "$4")
Icon=$icon
Path=$PROJECT_DIR
Terminal=false
Categories=Development;
EOF
    chmod +x "$file"
    cp "$file" "$desktop_dir/$1.desktop"
    # GNOME only runs desktop-folder launchers that are marked trusted.
    gio set "$desktop_dir/$1.desktop" metadata::trusted true 2>/dev/null || true
    info "Created $desktop_dir/$1.desktop"
}

write_launcher budgetapp-emulator "Budget App (Emulator)" \
    "Install the latest APK on the Pixel 9 emulator and show its logs" ""

update-desktop-database "$apps_dir" 2>/dev/null || true
