# BFM Debrief Tool

A browser-based 3D BFM debrief. Load two aircraft's [ForeFlight](https://foreflight.com)
KML track logs and replay the engagement — synchronized on a shared clock, with slant range,
closure rate, per-jet altitude/groundspeed/vertical-speed/G readouts, and the merge point
marked on the timeline.

**Everything runs client-side.** KML files are parsed in your browser and never uploaded
anywhere, so the whole thing is a single static page you can host for free.

## Use it

Open `index.html` (or the deployed site) and either:

- **Drop your KML files** — typically two `.kml` exports, one per jet — onto the landing screen, or
- Click **View demo flight** to watch the bundled sample engagement.

### Getting KML from ForeFlight

In ForeFlight, open a track log and share/export it as **KML**. Do this for each aircraft,
then drop both files into the tool.

### Airspace & route overlays

The landing screen lists optional **map overlays** — the working areas / restricted areas
for NJK (El Centro), NQI (Kingsville TW-2), and NZY (W-291), plus the IR-135 and VR-227 TAM
routes. When you pick your KML files, the tool reads where the flight happened and
**auto-checks the matching airspace** (a "detected" badge appears next to it); the three
regions are far enough apart that this is unambiguous. TAM routes are never auto-checked —
tick those by hand. In the viewer, **⚙ Display → Overlays** toggles everything on/off.

> Auto-detection keys off where the *fight* happened. A low-level route flown well north of
> its base's working areas won't trip airspace detection — just tick that route manually.

## Controls

- **Drag** to orbit · **scroll / pinch** to zoom · **scrub** the timeline at the bottom
- View presets: God's Eye, Chase J1/J2, Side, Free Orbit
- **⚙ Display** toggles altitude curtains, the range vector, full traces, ground shadows,
  the grid, vertical exaggeration, and trail length

## Files

| File | Purpose |
|------|---------|
| `index.html` | The entire viewer + in-browser KML→track converter |
| `trackdata.js` | Bundled demo dataset (`window.TRACK_DATA`); ship it alongside `index.html` |
| `overlays.js` | Airspace + TAM-route overlays (`window.OVERLAYS`); ship it alongside `index.html` |
| `convert.py` | Optional offline CLI to regenerate `trackdata.js` from KML files |
| `convert_overlays.py` | Regenerates `overlays.js` from the source files in `Raw KML Files/` |

The viewer pulls [Three.js](https://threejs.org) from a CDN at runtime, so it needs an
internet connection and must be served over HTTPS (GitHub Pages does this automatically).

### Regenerating the demo data (optional)

```bash
python3 convert.py JET1.kml JET2.kml
```

Writes `trackdata.js` next to the script. Standard library only — no dependencies.

To rebuild the airspace/route overlays after editing the source KML/KMZ files in
`Raw KML Files/`, run `python3 convert_overlays.py` (writes `overlays.js`).

## Shareable offline file (no server, no CDN)

If hosting is blocked (e.g. locked-down/managed devices) you can hand someone a single
self-contained HTML file that works with **zero network requests** — opened straight from
the Files app, an email attachment, or AirDrop, with no internet at all. Users can still
drop in their own KML files.

```bash
python3 build_standalone.py     # -> bfm-debrief.html (~1 MB, everything inlined)
```

It inlines Three.js (vendored in `vendor/`), the demo data, and the overlay data, and strips
the web-font links (falls back to system fonts offline). Just share `bfm-debrief.html` directly.

> Requires Safari 16.4+ / a 2023-or-newer browser (it uses an import map). Older browsers
> won't run it even though the file is local.

## Deploy

It's a static site. Any static host works (GitHub Pages, Netlify, Cloudflare Pages, S3).
With GitHub Pages: push this repo, then **Settings → Pages → Deploy from branch**.

## License

Copyright © 2026 Matthew Thomas. Licensed under the
[PolyForm Noncommercial License 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/)
(see [`LICENSE`](LICENSE)). **Free for any noncommercial use** — personal, educational, and
government/public-safety use included. Commercial use requires prior written permission.
