#!/bin/bash
# Build the Quick-Start PDF from howto.html using headless Chrome.
# Drop screenshots into howto/screenshots/ (see names in howto.html), then run this.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT="$DIR/BFM-Debrief-QuickStart-v0.1.pdf"

"$CHROME" --headless=new --disable-gpu \
  --no-pdf-header-footer \
  --print-to-pdf="$OUT" \
  "file://$DIR/howto.html" 2>/dev/null

echo "wrote $OUT"
