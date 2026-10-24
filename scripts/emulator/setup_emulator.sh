#!/usr/bin/env bash
# One-time setup: installs the Android emulator + a Pixel 9 virtual device into
# ~/Android/Sdk without needing the full Android Studio IDE. Safe to re-run.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/config.sh"

FALLBACK_CMDLINE_TOOLS="commandlinetools-linux-13114758_latest.zip"

# --- 1. Command-line tools (sdkmanager / avdmanager) -------------------------
if [[ ! -x "$SDKMANAGER" ]]; then
    info "Downloading Android command-line tools into $ANDROID_SDK_ROOT"
    command -v unzip >/dev/null || die "unzip is required (sudo apt install unzip)"
    tmp="$(mktemp -d)"
    trap 'rm -rf "$tmp"' EXIT

    zip_name="$(curl -fsSL https://dl.google.com/android/repository/repository2-3.xml \
        | grep -oE 'commandlinetools-linux-[0-9]+_latest\.zip' | sort -t- -k3 -n | tail -n1 || true)"
    zip_name="${zip_name:-$FALLBACK_CMDLINE_TOOLS}"

    curl -fL --progress-bar -o "$tmp/tools.zip" "https://dl.google.com/android/repository/$zip_name"
    unzip -q "$tmp/tools.zip" -d "$tmp"
    mkdir -p "$ANDROID_SDK_ROOT/cmdline-tools"
    rm -rf "$ANDROID_SDK_ROOT/cmdline-tools/latest"
    mv "$tmp/cmdline-tools" "$ANDROID_SDK_ROOT/cmdline-tools/latest"
fi

# --- 2. Licenses ---------------------------------------------------------------
# Reuse the licenses already accepted for Buildozer's SDK; otherwise prompt.
buildozer_licenses="$HOME/.buildozer/android/platform/android-sdk/licenses"
mkdir -p "$ANDROID_SDK_ROOT/licenses"
if [[ -d "$buildozer_licenses" ]]; then
    cp -n "$buildozer_licenses"/* "$ANDROID_SDK_ROOT/licenses/" 2>/dev/null || true
fi
if [[ ! -s "$ANDROID_SDK_ROOT/licenses/android-sdk-license" ]]; then
    info "Review and accept the Android SDK licenses"
    "$SDKMANAGER" --licenses
fi

# --- 3. Emulator, platform-tools (adb) and the system image -------------------
info "Installing platform-tools, emulator and $SYSTEM_IMAGE (first run downloads ~2 GB)"
if [[ -x "$ANDROID_CLI" ]]; then
    "$ANDROID_CLI" --no-metrics --sdk="$ANDROID_SDK_ROOT" sdk install platform-tools emulator "$SYSTEM_IMAGE"
else
    "$SDKMANAGER" --install "platform-tools" "emulator" "$SYSTEM_IMAGE"
fi

# --- 4. Hardware acceleration check -------------------------------------------
if ! "$EMULATOR" -accel-check >/dev/null 2>&1; then
    "$EMULATOR" -accel-check || true
    warn "KVM acceleration is unavailable; the emulator will be extremely slow."
    warn "Enable virtualization in BIOS and/or run: sudo usermod -aG kvm \$USER (then log out/in)"
fi

# --- 5. Pixel 9 virtual device -------------------------------------------------
if "$EMULATOR" -list-avds 2>/dev/null | grep -qx "$AVD_NAME"; then
    info "AVD '$AVD_NAME' already exists"
else
    info "Creating AVD '$AVD_NAME' ($AVD_DEVICE, $SYSTEM_IMAGE)"
    echo no | "$AVDMANAGER" create avd --name "$AVD_NAME" --device "$AVD_DEVICE" --package "$SYSTEM_IMAGE"
fi

# Match Android Studio's defaults: typing with the PC keyboard and GPU acceleration.
avd_config="$HOME/.android/avd/$AVD_NAME.avd/config.ini"
set_config() {
    if grep -q "^$1=" "$avd_config"; then
        sed -i "s|^$1=.*|$1=$2|" "$avd_config"
    else
        echo "$1=$2" >> "$avd_config"
    fi
}
set_config hw.keyboard yes
set_config hw.gpu.enabled yes
set_config hw.gpu.mode auto

info "Setup complete. Run scripts/emulator/run_on_emulator.sh to test the app."
