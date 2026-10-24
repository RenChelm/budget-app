#!/usr/bin/env bash
# Boots the Pixel 9 emulator (if it isn't already running), installs the newest
# APK from bin/, launches the app and streams its Python/crash logs.
#
# Usage: run_on_emulator.sh [--build] [--fresh] [--hold]
#   --build   run `buildozer android debug` first
#   --fresh   uninstall the app first (wipes its saved data)
#   --hold    wait for Enter before exiting (keeps a launcher's terminal open)
# Extra emulator flags can be passed via EMULATOR_ARGS, e.g. EMULATOR_ARGS="-no-snapshot-load".
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/config.sh"

build=0 fresh=0 hold=0
for arg in "$@"; do
    case "$arg" in
        --build) build=1 ;;
        --fresh) fresh=1 ;;
        --hold)  hold=1 ;;
        -h|--help) sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) die "unknown option: $arg" ;;
    esac
done

if (( hold )); then
    trap 'echo; read -rp "Press Enter to close this window..." _' EXIT
fi

[[ -x "$EMULATOR" && -x "$ADB" ]] || die "Emulator not installed. Run scripts/emulator/setup_emulator.sh first."
mkdir -p "$LOG_DIR"

# --- 1. Optional rebuild --------------------------------------------------------
if (( build )); then
    info "Building APK with buildozer (log: $LOG_DIR/build.log)"
    [[ -f "$PROJECT_DIR/kivyenv/bin/activate" ]] || die "kivyenv not found in $PROJECT_DIR"
    (
        cd "$PROJECT_DIR"
        source kivyenv/bin/activate
        buildozer android debug 2>&1 | tee "$LOG_DIR/build.log"
    ) || {
        grep -n "ERROR\|Exception\|error:" "$LOG_DIR/build.log" | tail -30 || true
        die "Build failed. Full log: $LOG_DIR/build.log"
    }
fi

apk="$(ls -t "$PROJECT_DIR"/bin/*.apk 2>/dev/null | head -n1 || true)"
[[ -n "$apk" ]] || die "No APK found in $PROJECT_DIR/bin. Run with --build."
info "APK: ${apk#"$PROJECT_DIR"/} (built $(date -r "$apk" '+%Y-%m-%d %H:%M'))"

# --- 2. Find or boot the emulator -----------------------------------------------
"$ADB" start-server >/dev/null 2>&1

find_serial() {
    local serial name
    for serial in $("$ADB" devices | awk '$1 ~ /^emulator-/ && $2 == "device" {print $1}'); do
        name="$("$ADB" -s "$serial" shell getprop ro.boot.qemu.avd_name 2>/dev/null | tr -d '\r')"
        [[ -n "$name" ]] || name="$("$ADB" -s "$serial" emu avd name 2>/dev/null | head -n1 | tr -d '\r')"
        if [[ "$name" == "$AVD_NAME" ]]; then echo "$serial"; return 0; fi
    done
    return 1
}

serial="$(find_serial || true)"
if [[ -z "$serial" ]]; then
    "$EMULATOR" -list-avds | grep -qx "$AVD_NAME" \
        || die "AVD '$AVD_NAME' not found. Run scripts/emulator/setup_emulator.sh first."
    info "Starting emulator '$AVD_NAME' (log: $LOG_DIR/emulator.log)"
    # setsid detaches it, so closing this terminal doesn't close the emulator.
    # shellcheck disable=SC2086
    setsid -w "$EMULATOR" -avd "$AVD_NAME" ${EMULATOR_ARGS:-} >"$LOG_DIR/emulator.log" 2>&1 < /dev/null &
    emu_pid=$!

    info "Waiting for the emulator to boot (the first boot can take a few minutes)"
    for (( i = 0; i < 300; i++ )); do
        kill -0 "$emu_pid" 2>/dev/null || { tail -20 "$LOG_DIR/emulator.log" >&2; die "Emulator exited during startup."; }
        serial="$(find_serial || true)"
        if [[ -n "$serial" ]]; then break; fi
        sleep 1
    done
    [[ -n "$serial" ]] || die "Timed out waiting for the emulator to appear in adb."
fi
export ANDROID_SERIAL="$serial"

for (( i = 0; i < 300; i++ )); do
    if [[ "$("$ADB" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" == "1" ]]; then break; fi
    sleep 1
done
[[ "$("$ADB" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" == "1" ]] \
    || die "Timed out waiting for Android to finish booting."
"$ADB" shell wm dismiss-keyguard >/dev/null 2>&1 || true
info "Emulator ready ($serial)"

# --- 3. Check the APK can run on this emulator's CPU ----------------------------
device_abis="$("$ADB" shell getprop ro.product.cpu.abilist | tr -d '\r')"
apk_abis="$(unzip -Z1 "$apk" 'lib/*' 2>/dev/null | cut -d/ -f2 | sort -u | tr '\n' ' ' || true)"
if [[ -n "$apk_abis" ]]; then
    compatible=0
    for abi in $apk_abis; do
        if [[ ",$device_abis," == *",$abi,"* ]]; then compatible=1; fi
    done
    (( compatible )) || die "APK is built for [$apk_abis] but the emulator supports [$device_abis].
       Add x86_64 to android.archs in buildozer.spec and rebuild (--build)."
fi

# --- 4. Install and launch ------------------------------------------------------
if (( fresh )); then
    info "Uninstalling $APP_PACKAGE (wiping app data)"
    "$ADB" uninstall "$APP_PACKAGE" >/dev/null 2>&1 || true
fi

info "Installing $APP_PACKAGE"
if ! out="$("$ADB" install -r -d -t "$apk" 2>&1)"; then
    if [[ "$out" == *INSTALL_FAILED_UPDATE_INCOMPATIBLE* ]]; then
        warn "Installed copy was signed with a different key; reinstalling (app data will be wiped)."
        "$ADB" uninstall "$APP_PACKAGE" >/dev/null
        out="$("$ADB" install -t "$apk" 2>&1)" || die "Install failed: $out"
    else
        die "Install failed: $out"
    fi
fi

activity="$("$ADB" shell cmd package resolve-activity --brief -c android.intent.category.LAUNCHER "$APP_PACKAGE" \
    | tr -d '\r' | tail -n1)"
[[ "$activity" == */* ]] || activity="$APP_PACKAGE/org.kivy.android.PythonActivity"

"$ADB" logcat -c
"$ADB" shell am force-stop "$APP_PACKAGE"
info "Launching $activity"
out="$("$ADB" shell am start -n "$activity" 2>&1 | tr -d '\r')"
[[ "$out" != *Error* ]] || die "Launch failed: $out"

# --- 5. Stream app logs -----------------------------------------------------------
# python:I = Kivy/print output and tracebacks (python:V adds ~1000 "extracting" lines per install);
# AndroidRuntime/DEBUG/libc = Java and native crashes.
info "Streaming app logs (Ctrl+C to stop; the emulator keeps running)"
trap ':' INT
"$ADB" logcat -v time -s python:I PythonActivity:W SDL:W AndroidRuntime:E DEBUG:V libc:F || true
trap - INT
