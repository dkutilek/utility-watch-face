#!/bin/zsh
# Builds a signed, installable APK at build/utility-classic.apk.
# Pass a Python with Pillow via PYTHON=... to regenerate icons and the face first.
set -euo pipefail

cd "${0:A:h}"
SDK="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
TOOLS="$SDK/build-tools/36.1.0"
ANDROID_JAR="$SDK/platforms/android-36/android.jar"
KEYSTORE="$HOME/.android/utility-classic.keystore"
OUT=build
SRC_RES="${RES_DIR:-res}"

"${PYTHON:-python3}" tools/generate.py

rm -rf "$OUT"
mkdir -p "$OUT"

"$TOOLS/aapt2" compile --dir "$SRC_RES" -o "$OUT/res.zip"
"$TOOLS/aapt2" link \
  -o "$OUT/unsigned.apk" \
  -I "$ANDROID_JAR" \
  --manifest AndroidManifest.xml \
  --min-sdk-version 34 \
  --target-sdk-version 36 \
  --version-code 1 \
  --version-name 1.0 \
  "$OUT/res.zip"

"$TOOLS/zipalign" -f 4 "$OUT/unsigned.apk" "$OUT/aligned.apk"

# A personal signing key. Keep it: Android only accepts updates signed with the same key.
if [[ ! -f "$KEYSTORE" ]]; then
  mkdir -p "${KEYSTORE:h}"
  keytool -genkeypair -keystore "$KEYSTORE" -alias watchface \
    -storepass android -keypass android -keyalg RSA -keysize 2048 -validity 10000 \
    -dname "CN=Utility Classic Watch Face" 2>/dev/null
fi

"$TOOLS/apksigner" sign --ks "$KEYSTORE" --ks-pass pass:android --key-pass pass:android \
  --out "$OUT/utility-classic.apk" "$OUT/aligned.apk"

"$TOOLS/apksigner" verify "$OUT/utility-classic.apk"
echo "Built $OUT/utility-classic.apk"
