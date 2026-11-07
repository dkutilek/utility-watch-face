#!/bin/zsh
# Installs the built face on a watch connected over wireless debugging and makes it active.
# Usage: ./install.sh <watch-ip>:<connect-port>
set -euo pipefail

cd "${0:A:h}"
ADB="${ANDROID_HOME:-$HOME/Library/Android/sdk}/platform-tools/adb"
APK=build/utility-classic.apk
FACE=com.drewkutilek.watchface.utilityclassic

if [[ $# -ne 1 ]]; then
  echo "Usage: ./install.sh <watch-ip>:<connect-port>" >&2
  exit 2
fi
if [[ ! -f "$APK" ]]; then
  echo "$APK is missing. Run ./build.sh first." >&2
  exit 1
fi

"$ADB" connect "$1"
"$ADB" -s "$1" install -r "$APK"
"$ADB" -s "$1" shell am broadcast -a com.google.android.wearable.app.DEBUG_SURFACE \
  --es operation set-watchface --es watchFaceId "$FACE"
echo "Installed. If the face did not switch, long-press the watch face and pick Utility Classic."
