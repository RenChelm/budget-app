## Building
### Capture errors from Buildozer build log:
```bash
buildozer android debug 2>&1 | tee <build-log-filename>.txt
```
- The `2>&1 | tee build_output.txt` captures both stdout and stderr to `<build-log-filename>.txt` while still printing to the terminal. 

### Search captured build log for errors:
```bash
grep -n "ERROR\|Exception\|error:" <build-log-filename>.txt | tail -30
```
- `grep -n` prints matching lines with their line numbers. `tail -30` limits output to the last 30 matches, since build errors typically appear near the end of the log.

## Testing on the Android Emulator
### One-time setup (Pixel 9 emulator, no Android Studio needed):
```bash
scripts/emulator/setup_emulator.sh
scripts/emulator/install_desktop_launchers.sh
```
- Installs the emulator, adb and an Android 15 system image into `~/Android/Sdk` and creates a `Pixel_9` virtual device. Android Studio uses the same location, so it will see this device if installed later.
- Adds a **Budget App (Emulator)** icon to the desktop and app menu.

### Install and run the latest APK:
```bash
scripts/emulator/run_on_emulator.sh            # newest APK in bin/
scripts/emulator/run_on_emulator.sh --build    # rebuild with buildozer first
scripts/emulator/run_on_emulator.sh --fresh    # uninstall first (wipes saved data)
```
- Boots the emulator if needed, installs the APK, launches the app and streams the Python logs and tracebacks. Ctrl+C stops the logs; the emulator keeps running.

## Creating a Release
### Upload new release to github
```bash
gh release create v<version-number> bin/<apk-filename>.apk \
--title "<title>" \
--notes "<notes>"
```

- Example:
```bash
gh release create v0.12 bin/budgetapp-0.12-arm64-v8a_armeabi-v7a-debug.apk \
--title "v0.12 - Custom Categories" \
--notes "Added the option to create custom categories. Refactored Entry Row layout for better maintainability."
```

### Upload new release with notes from a markdown file
```bash
gh release create v<version-number> bin/<apk-filename>.apk \
--title "<title>" \
--notes-file <notes-filename>.md
```
- `--notes-file` (or `-F`) uses the whole file as the release description, and GitHub renders its markdown (headings, bullet lists, bold text). The file doesn't need to be committed, so a gitignored file like `PATCH_NOTES.md` works.
- The file is published as-is, so first remove anything meant only for you, such as an "Unreleased" heading or notes about commits.
- Add `--draft` to save the release without publishing it. Check how it looks on the repo's Releases page, then click **Publish release** there (or run `gh release edit v<version-number> --draft=false`).

- Example:
```bash
gh release create v0.4 bin/budgetapp-0.4-arm64-v8a_armeabi-v7a-debug.apk \
--title "v0.4 - Weekly Budgeting" \
--notes-file PATCH_NOTES.md \
--draft
```