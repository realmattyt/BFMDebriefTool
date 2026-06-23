#!/usr/bin/env python3
"""
Build overlays.js from the raw KML/KMZ files in "Raw KML Files/".

The viewer (index.html) draws optional overlays on top of the flight tracks:
  - AIRSPACE  : the working areas / restricted areas / run-ins for a base.
                These auto-enable when an uploaded track's centroid falls
                inside the airspace's region box (see index.html detection).
  - ROUTE     : low-level TAM route waypoints. Never auto-enabled; the user
                ticks these by hand.

Each overlay carries a `region` (lat/lon bounding box, padded) used purely for
the "which airspace is this flight in?" auto-detection. The three airspaces are
hundreds of miles apart (El Centro CA, Kingsville TX, off the SoCal coast), so a
simple centroid-in-box test picks the right one unambiguously.

Output is a single self-contained `overlays.js` that defines `window.OVERLAYS`.
index.html loads it directly; build_standalone.py inlines it for the offline
single-file build. Re-run this whenever the raw files change:

    python3 convert_overlays.py        # -> overlays.js
"""
import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "Raw KML Files")
OUT = os.path.join(HERE, "overlays.js")
KML_NS = "{http://www.opengis.net/kml/2.2}"

# How much to pad each airspace's bounding box (degrees) for auto-detection, so
# a flight that drifts just outside the drawn areas still matches its base.
REGION_PAD = 0.05
ROUND = 5  # coordinate decimal places (~1 m); keeps overlays.js small


def load_kml(path):
    """Return the KML XML text from a .kml or .kmz file."""
    if path.lower().endswith(".kmz"):
        with zipfile.ZipFile(path) as z:
            name = next((n for n in z.namelist() if n.lower().endswith(".kml")), None)
            if not name:
                sys.exit(f"{path}: no .kml inside the .kmz")
            return z.read(name).decode("utf-8")
    with open(path, encoding="utf-8") as f:
        return f.read()


def parse_coords(text):
    """KML <coordinates> text -> [[lon,lat], ...] (altitude dropped, rounded)."""
    pts = []
    for tok in (text or "").split():
        p = tok.split(",")
        if len(p) >= 2:
            try:
                pts.append([round(float(p[0]), ROUND), round(float(p[1]), ROUND)])
            except ValueError:
                pass
    return pts


def name_of(pm):
    n = pm.find(KML_NS + "name")
    return (n.text or "").strip() if n is not None else ""


def is_real_name(name):
    """A label worth drawing on the map (skip placeholders / verbose auto-names)."""
    if not name:
        return False
    low = name.lower()
    if low.startswith("untitled") or low.startswith("line ") or "radius circle" in low:
        return False
    return True


def extract_airspace(path):
    """Pull polygons (areas) and linestrings (run-ins/boundaries) from an airspace file."""
    root = ET.fromstring(load_kml(path))
    areas, lines = [], []
    poly_names = set()
    for pm in root.iter(KML_NS + "Placemark"):
        name = name_of(pm)
        poly = pm.find(".//" + KML_NS + "Polygon")
        if poly is not None:
            ring = poly.find(".//" + KML_NS + "outerBoundaryIs//" + KML_NS + "coordinates")
            if ring is None:
                ring = poly.find(".//" + KML_NS + "coordinates")
            coords = parse_coords(ring.text if ring is not None else "")
            if len(coords) >= 3:
                areas.append({"name": name, "coords": coords})
                if is_real_name(name):
                    poly_names.add(name)
            continue
        ls = pm.find(".//" + KML_NS + "LineString//" + KML_NS + "coordinates")
        if ls is not None:
            coords = parse_coords(ls.text)
            if len(coords) >= 2:
                lines.append({"name": name, "coords": coords})
    # Drop a linestring that just retraces a polygon of the same name (the raw
    # files store many areas as both a filled Polygon and a duplicate outline).
    lines = [l for l in lines if l["name"] not in poly_names]
    return areas, lines


def extract_route(path):
    """Pull ordered point waypoints from a route file (IR217.kml = VR-227)."""
    root = ET.fromstring(load_kml(path))
    wpts = []
    for pm in root.iter(KML_NS + "Placemark"):
        pt = pm.find(".//" + KML_NS + "Point//" + KML_NS + "coordinates")
        if pt is None:
            continue
        coords = parse_coords(pt.text)
        if not coords:
            continue
        lon, lat = coords[0]
        name = name_of(pm)
        if not name or name.lower().startswith("untitled"):
            name = str(len(wpts) + 1)
        wpts.append({"name": name, "lat": lat, "lon": lon})
    return wpts


def region_of(*coord_lists):
    """Padded lat/lon bounding box over any number of [lon,lat] point lists."""
    lons = [c[0] for lst in coord_lists for c in lst]
    lats = [c[1] for lst in coord_lists for c in lst]
    return {
        "lonMin": round(min(lons) - REGION_PAD, ROUND),
        "lonMax": round(max(lons) + REGION_PAD, ROUND),
        "latMin": round(min(lats) - REGION_PAD, ROUND),
        "latMax": round(max(lats) + REGION_PAD, ROUND),
    }


def all_area_line_coords(areas, lines):
    out = []
    for a in areas:
        out.append(a["coords"])
    for l in lines:
        out.append(l["coords"])
    return out


# --- IR-135 route (Kingsville TW-2): no source KML, kept here as the master copy ---
IR135 = [
    {"name": "1. Terror Camp",  "lat": 27.3459001011446,  "lon": -98.12422847280098},
    {"name": "2. Sweatshop",    "lat": 27.20047304741218, "lon": -98.14274423597273},
    {"name": "3. INS #1",       "lat": 27.03219251758544, "lon": -98.13940081553994},
    {"name": "4. Bordello",     "lat": 26.8925562664702,  "lon": -98.13484394407575},
    {"name": "5. Sam Site",     "lat": 26.85588465880714, "lon": -98.33088763375012},
    {"name": "6. Mig Base",     "lat": 26.72050842506632, "lon": -98.56051551671253},
    {"name": "7. Kaffie",       "lat": 27.07596467891384, "lon": -98.60110334348073},
    {"name": "8. Training Camp","lat": 27.31820213291066, "lon": -98.68029231975439},
    {"name": "9. Rail Yard",    "lat": 27.42722696508979, "lon": -98.84763620583124},
    {"name": "10. Mine",        "lat": 27.62271010792919, "lon": -98.82278426914367},
    {"name": "11. INS #2",      "lat": 27.77407077455658, "lon": -98.84604894155773},
    {"name": "12. Freer Hangar","lat": 27.88611489241125, "lon": -98.59882317545561},
]


def route_region(wpts):
    pts = [[w["lon"], w["lat"]] for w in wpts]
    return region_of(pts)


def main():
    njk_areas, njk_lines = extract_airspace(os.path.join(RAW, "NJK Airspace.kmz"))
    nqi_areas, nqi_lines = extract_airspace(os.path.join(RAW, "NQI AIRSPACE.kmz"))
    nzy_areas, nzy_lines = extract_airspace(os.path.join(RAW, "NZY Airspace.kmz"))
    vr227 = extract_route(os.path.join(RAW, "IR217.kml"))  # mislabeled IR217; it is VR-227

    overlays = [
        # ---- airspaces (auto-detected by track location) ----
        {
            "id": "air_njk", "kind": "airspace",
            "label": "NJK Airspace — El Centro", "color": "#9ad84a",
            "region": region_of(*all_area_line_coords(njk_areas, njk_lines)),
            "areas": njk_areas, "lines": njk_lines,
        },
        {
            "id": "air_nqi", "kind": "airspace",
            "label": "NQI Airspace — Kingsville TW-2", "color": "#ff9e3b",
            "region": region_of(*all_area_line_coords(nqi_areas, nqi_lines)),
            "areas": nqi_areas, "lines": nqi_lines,
        },
        {
            "id": "air_nzy", "kind": "airspace",
            "label": "NZY Airspace — W-291 / North Island", "color": "#5aa0ff",
            "region": region_of(*all_area_line_coords(nzy_areas, nzy_lines)),
            "areas": nzy_areas, "lines": nzy_lines,
        },
        # ---- TAM routes (manual only) ----
        {
            "id": "tam_nqi_ir135", "kind": "route",
            "label": "TAM — NQI / IR-135", "color": "#ffd23b",
            "region": route_region(IR135), "waypoints": IR135,
        },
        {
            "id": "tam_njk_vr227", "kind": "route",
            "label": "TAM — NJK / VR-227", "color": "#c77dff",
            "region": route_region(vr227), "waypoints": vr227,
        },
    ]

    body = json.dumps(overlays, separators=(",", ":"))
    js = ("/* GENERATED by convert_overlays.py from \"Raw KML Files/\" — do not edit by hand. */\n"
          "window.OVERLAYS = " + body + ";\n")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(js)

    size = os.path.getsize(OUT)
    print(f"wrote {OUT}  ({size:,} bytes)")
    for o in overlays:
        if o["kind"] == "airspace":
            r = o["region"]
            print(f"  {o['id']:14} {len(o['areas']):2} areas {len(o['lines']):2} lines  "
                  f"region lat[{r['latMin']:.2f},{r['latMax']:.2f}] lon[{r['lonMin']:.2f},{r['lonMax']:.2f}]")
        else:
            print(f"  {o['id']:14} {len(o['waypoints']):2} waypoints")


if __name__ == "__main__":
    main()
