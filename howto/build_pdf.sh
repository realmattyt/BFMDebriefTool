#!/bin/bash
# Build the Quick-Start PDF from howto.html using headless Chrome.
# Drop screenshots into howto/screenshots/ (see names in howto.html), then run this.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
# derive version from the howto's cover (e.g. "Version <b>0.2</b>")
VER="$(grep -oE 'Version <b>[0-9.]+</b>' "$DIR/howto.html" | grep -oE '[0-9.]+' | head -1)"
VER="${VER:-0.2}"
OUT="$DIR/BFM-Debrief-QuickStart-v${VER}.pdf"

"$CHROME" --headless=new --disable-gpu \
  --no-pdf-header-footer \
  --print-to-pdf="$OUT" \
  "file://$DIR/howto.html" 2>/dev/null

echo "wrote $OUT"
