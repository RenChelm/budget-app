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