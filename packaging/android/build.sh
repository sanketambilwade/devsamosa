#!/usr/bin/env bash
# Builds the APK straight from the SDK build-tools — no Gradle, so nothing is
# downloaded and the build works offline. Run from this directory.
set -e

SDK="${LOCALAPPDATA}/Android/Sdk"
BT="$SDK/build-tools/35.0.0"
JDK="/c/Program Files/Android/Android Studio/jbr/bin"
# d8.bat and apksigner.bat are Windows batch wrappers: they need a Windows-style
# JAVA_HOME, not the POSIX path Git Bash uses
export JAVA_HOME='C:\Program Files\Android\Android Studio\jbr'
PLATFORM="$SDK/platforms/android-35/android.jar"
OUT="d:/Dev Samosa/dist"
WORK="./.build"

rm -rf "$WORK"; mkdir -p "$WORK/res" "$WORK/gen" "$WORK/classes" "$OUT"

echo "1/6  compiling resources"
"$BT/aapt2.exe" compile --dir res -o "$WORK/res.zip"

echo "2/6  linking resources"
"$BT/aapt2.exe" link \
  -o "$WORK/base.apk" \
  -I "$PLATFORM" \
  --manifest AndroidManifest.xml \
  --java "$WORK/gen" \
  --min-sdk-version 24 --target-sdk-version 35 \
  "$WORK/res.zip"

echo "3/6  compiling java"
"$JDK/javac.exe" -source 17 -target 17 -nowarn \
  -classpath "$PLATFORM" \
  -d "$WORK/classes" \
  $(find src "$WORK/gen" -name '*.java')

echo "4/6  dexing"
"$BT/d8.bat" --release --min-api 24 --lib "$PLATFORM" \
  --output "$WORK" $(find "$WORK/classes" -name '*.class')

echo "5/6  packaging"
cp "$WORK/base.apk" "$WORK/unsigned.apk"
(cd "$WORK" && "$JDK/jar.exe" uf unsigned.apk classes.dex)
"$BT/zipalign.exe" -f -p 4 "$WORK/unsigned.apk" "$WORK/aligned.apk"

echo "6/6  signing"
KS="$WORK/devsamosa.keystore"
"$JDK/keytool.exe" -genkeypair -v -keystore "$KS" \
  -alias devsamosa -keyalg RSA -keysize 2048 -validity 10000 \
  -storepass devsamosa -keypass devsamosa \
  -dname "CN=DevSamosa, OU=Delivery, O=DevSamosa, L=Bengaluru, C=IN" >/dev/null 2>&1
"$BT/apksigner.bat" sign --ks "$KS" --ks-pass pass:devsamosa --key-pass pass:devsamosa \
  --out "$OUT/DevSamosa.apk" "$WORK/aligned.apk"
"$BT/apksigner.bat" verify --print-certs "$OUT/DevSamosa.apk" | head -3

echo ""
echo "built: $OUT/DevSamosa.apk"
ls -la "$OUT/DevSamosa.apk" | awk '{print "size: " int($5/1024) " KB"}'
