# Shared settings for the emulator scripts. Sourced, not executed.
# Any of these can be overridden by exporting the variable before running a script.

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Same SDK location Android Studio uses, so Studio will pick it up if installed later.
ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}"
export ANDROID_SDK_ROOT ANDROID_HOME="$ANDROID_SDK_ROOT"

AVD_NAME="${AVD_NAME:-Pixel_9}"
AVD_DEVICE="${AVD_DEVICE:-pixel_9}"
# Google APIs images include ARM->x86 translation, needed because the APK is arm64/armv7 only.
SYSTEM_IMAGE="${SYSTEM_IMAGE:-system-images;android-35;google_apis;x86_64}"

SDKMANAGER="$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager"
# Google's newer CLI; sdkmanager now forwards to it but can't turn off its usage metrics.
ANDROID_CLI="$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/android"
AVDMANAGER="$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/avdmanager"
ADB="$ANDROID_SDK_ROOT/platform-tools/adb"
EMULATOR="$ANDROID_SDK_ROOT/emulator/emulator"

LOG_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/budgetapp-emulator"

# Package id comes from buildozer.spec (package.domain + package.name).
spec_value() {
    sed -n -E "s/^$1[[:space:]]*=[[:space:]]*(.*[^[:space:]])[[:space:]]*$/\1/p" "$PROJECT_DIR/buildozer.spec" | head -n1
}
APP_PACKAGE="${APP_PACKAGE:-$(spec_value 'package\.domain').$(spec_value 'package\.name')}"

info() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mwarning:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }
