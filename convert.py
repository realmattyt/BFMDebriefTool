#!/usr/bin/env python3
"""
Convert ForeFlight KML track logs into trackdata.js for the BFM recreation viewer.

Usage:
    python3 convert.py JET1.kml JET2.kml [JET3.kml ...]
    python3 convert.py            # uses the two filenames below by default

Writes trackdata.js next to this script:  window.TRACK_DATA = { ... }

Coordinate frame (matches the viewer):
    x = East (m), y = Up (m), z = North (m), all relative to the mean lat/lon.
    Each sample is [E, Up, North, t_seconds_since_shared_epoch].
    All tracks share one absolute clock (epoch = earliest start), so the
    relative geometry between jets is preserved.
"""
import sys, os, json, math
import xml.etree.ElementTree as ET
from datetime import datetime

DEFAULTS = [
    "TrackLog_303426AD-88DE-45BA-BFA8-A898CF32FD66.kml",
    "TrackLog_CCF53BFD-53A0-44F7-9124-ECD463D4F39D.kml",
]

def parse(fn):
    root = ET.parse(fn).getroot()
    whens, coords = [], []
    for el in root.iter():
        tag = el.tag.split('}')[-1]
        if tag == 'when':
            whens.append(el.text.strip())
        elif tag == 'coord':                       # gx:coord  ->  "lon lat alt"
            lon, lat, alt = map(float, el.text.strip().split())
            coords.append((lon, lat, alt))
    if not coords:
        raise SystemExit(f"{fn}: no <gx:coord> samples found")
    if len(whens) != len(coords):
        # tolerate; zip will truncate to the shorter
        print(f"  warn: {fn} has {len(whens)} timestamps vs {len(coords)} coords")
    return whens, coords

def tail_of(fn):
    base = os.path.basename(fn)
    base = base[:-4] if base.lower().endswith('.kml') else base
    if base.startswith('TrackLog_'):
        base = base[len('TrackLog_'):]
    return base.split('-')[0][:8] or base

def main(paths):
    parsed, all_coords, starts = [], [], []
    for fn in paths:
        w, c = parse(fn)
        t0 = datetime.strptime(w[0][:19], '%Y-%m-%dT%H:%M:%S')
        parsed.append((fn, w, c, t0))
        all_coords += c
        starts.append(t0)

    epoch = min(starts)
    lat0 = sum(p[1] for p in all_coords) / len(all_coords)
    lon0 = sum(p[0] for p in all_coords) / len(all_coords)
    mlat = 110570.0
    mlon = 111320.0 * math.cos(math.radians(lat0))

    out = {"ref": {"lat0": lat0, "lon0": lon0},
           "epoch": epoch.strftime('%Y-%m-%dT%H:%M:%SZ'),
           "tracks": []}
    tmax = 0.0
    for i, (fn, w, c, t0) in enumerate(parsed):
        pts = []
        last = t0
        for (lon, lat, alt), wt in zip(c, w):
            t = datetime.strptime(wt[:19], '%Y-%m-%dT%H:%M:%S')
            sec = (t - epoch).total_seconds()
            e = (lon - lon0) * mlon
            n = (lat - lat0) * mlat
            u = max(alt, 0.0)
            pts.append([round(e, 1), round(u, 1), round(n, 1), round(sec)])
            tmax = max(tmax, sec)
            last = t
        out["tracks"].append({
            "label": f"JET {i+1}",
            "tail": tail_of(fn),
            "start": round((t0 - epoch).total_seconds()),
            "maxalt_ft": round(max(p[2] for p in c) * 3.280839895),
            "pts": pts,
        })
    out["tmax"] = round(tmax)

    js = "window.TRACK_DATA = " + json.dumps(out, separators=(',', ':')) + ";\n"
    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trackdata.js")
    with open(dest, "w") as f:
        f.write(js)

    print(f"wrote {dest}  ({len(js):,} bytes)")
    print(f"epoch {out['epoch']}   tmax {out['tmax']}s")
    for t in out["tracks"]:
        print(f"  {t['label']} [{t['tail']}]  {len(t['pts'])} pts  "
              f"start +{t['start']}s  max {t['maxalt_ft']:,} ft")

if __name__ == "__main__":
    args = sys.argv[1:] or DEFAULTS
    missing = [p for p in args if not os.path.exists(p)]
    if missing:
        raise SystemExit("missing file(s): " + ", ".join(missing))
    main(args)
