#!config.PROJECT_HOMEbin/env bash
# zipclean.sh  --  Remove unnecessary files (venv, __pycache__, .pyd, .so, .whl) from an existing ZIP
#
# Usage:
#   ./zipclean.sh giwanos.zip cleaned_giwanos.zip
#
# Requirements:
#   - unzip, zip (InfoZIP) installed
#   - Sufficient disk space for temporary extraction
#
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <input_zip> <output_zip>"
  exit 1
fi

IN_ZIP="$1"
OUT_ZIP="$2"
TMP_DIR=$(mktemp -d)

trap 'rm -rf "$TMP_DIR"' EXIT

echo "[*] Extracting $IN_ZIP ..."
unzip -q "$IN_ZIP" -d "$TMP_DIR"

echo "[*] Removing virtual environments, caches and binaries ..."
find "$TMP_DIR" \( -path "*/venv*" -o -name "__pycache__" -o -name "*.pyd" -o -name "*.so" -o -name "*.whl" \) -prune -exec rm -rf {} +

echo "[*] Repacking to $OUT_ZIP ..."
cd "$TMP_DIR"
zip -rq "$OUT_ZIP" .

echo "[+] Clean archive created: $OUT_ZIP"

