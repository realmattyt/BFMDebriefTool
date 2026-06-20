#!/usr/bin/env python3
"""
Build a single, fully self-contained bfm-debrief.html.

Inlines Three.js and the demo track data directly into the page so it makes
ZERO network requests — it works opened straight from the Files app, an email
attachment, or AirDrop, even with CDNs blocked and no internet at all.

Users can still drop their own KML files; that has always run in-browser.

Usage:
    python3 build_standalone.py            # -> bfm-debrief-v<version>.html

The version (and the output filename) is read straight from index.html's
<title>, so the standalone always matches the source — bump the version once
in index.html and the build follows automatically.
"""
import base64, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC   = os.path.join(HERE, "index.html")
THREE = os.path.join(HERE, "vendor", "three.module.min.js")
DEMO  = os.path.join(HERE, "trackdata.js")

CDN_URL = "https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.0/three.module.min.js"
FONT_LINK = ('<link href="https://fonts.googleapis.com/css2?family=Chakra+Petch:'
             'wght@500;600;700&family=Azeret+Mono:wght@400;500;600&display=swap" '
             'rel="stylesheet">')

def read(p):
    if not os.path.exists(p):
        sys.exit(f"missing {p}" + ("  (run: curl -sSL -o vendor/three.module.min.js "
                 + CDN_URL + ")" if p == THREE else ""))
    with open(p, encoding="utf-8") as f:
        return f.read()

def main():
    html  = read(SRC)
    three = read(THREE)
    demo  = read(DEMO)

    # Version + output filename follow index.html's <title> (e.g. "...v0.2").
    m = re.search(r"<title>[^<]*?v(\d+(?:\.\d+)+)", html)
    version = m.group(1) if m else "0"
    out = os.path.join(HERE, f"bfm-debrief-v{version}.html")

    # 1) Three.js -> base64 data: URL inside the existing importmap (code unchanged).
    b64 = base64.b64encode(three.encode("utf-8")).decode("ascii")
    data_url = "data:text/javascript;base64," + b64
    if CDN_URL not in html:
        sys.exit("could not find the Three.js CDN URL in index.html — did the importmap change?")
    html = html.replace(CDN_URL, data_url)

    # 2) Inline the demo data so the "View demo flight" button works offline.
    #    (The on-demand loader short-circuits when window.TRACK_DATA already exists.)
    inline_demo = "<script>/* inlined demo data */\n" + demo.strip() + "\n</script>\n"
    marker = '<script type="importmap">'
    html = html.replace(marker, inline_demo + marker, 1)

    # 3) Drop all Google Fonts <link>s (they would fail offline; CSS already has fallbacks).
    for tag in (FONT_LINK,
                '<link rel="preconnect" href="https://fonts.googleapis.com">',
                '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'):
        html = html.replace(tag, "")
    html = html.replace("<head>\n", "<head>\n<!-- self-contained build: no external requests -->\n", 1)

    # (Title/version already live in index.html, so no stamping needed.)

    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    size = os.path.getsize(out)
    print(f"wrote {out}  ({size:,} bytes, {size/1_048_576:.1f} MB)")
    print("Fully self-contained: no CDN, no fonts, no trackdata.js needed. Share it directly.")

if __name__ == "__main__":
    main()
