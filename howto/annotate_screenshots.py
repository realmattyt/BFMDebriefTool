#!/usr/bin/env python3
"""Annotate the raw iPad screenshots with a highlight box on the key tap target,
writing doc-named copies into howto/screenshots/. Also emits _contact_sheet.png
for quick visual verification of every box at once.

Boxes are given in normalized fractions of the 1488x2266 source so they're easy
to eyeball and tweak. Re-run after editing TARGETS."""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "screenshots", "raw")
OUT = os.path.join(HERE, "screenshots")

ORANGE = (212, 99, 26)          # --j2
GLOW = (212, 99, 26, 70)

# src file, dest name, [ (x0,y0,x1,y1) normalized boxes ... ]
TARGETS = [
    ("IMG_0042.PNG", "01-edge-installed.png", [(0.82, 0.104, 0.99, 0.153)]),
    ("IMG_0043.PNG", "02-file-in-files.png",  [(0.0, 0.385, 1.0, 0.45)]),
    ("IMG_0047.PNG", "03-open-in-edge.png",   [(0.12, 0.465, 0.88, 0.505)]),
    ("IMG_0053.PNG", "04-tool-in-edge.png",   []),  # result shot, no callout
    ("IMG_0054.PNG", "05-ff-enable-tracklog.png", [(0.0, 0.150, 1.0, 0.262)]),
    ("IMG_0036.PNG", "06-ff-open-tracklogs.png",  [(0.70, 0.40, 0.99, 0.455)]),
    ("IMG_0038.PNG", "07-ff-pick-flight.png",     [(0.0, 0.147, 0.43, 0.215)]),
    ("IMG_0037.PNG", "08-ff-export-share.png",    [(0.90, 0.035, 0.995, 0.075)]),
    ("IMG_0039.PNG", "09-ff-open-kml-in.png",     [(0.685, 0.115, 0.875, 0.205)]),
    # two options in the same share sheet: AirDrop (top) and Save to Files (bottom)
    ("IMG_0040.PNG", "10-ff-save-to-files.png",   [(0.515, 0.145, 0.625, 0.225), (0.505, 0.282, 0.61, 0.372)]),
    # save-to-files picker: MDM blocks Downloads, so use On My iPad -> Edge
    ("IMG_0044.PNG", "10b-save-to-edge.png",  [(0.085, 0.224, 0.445, 0.262), (0.78, 0.108, 0.945, 0.225)]),
    ("IMG_0053.PNG", "11-start-screen.png",   [(0.07, 0.40, 0.92, 0.58)]),
    # replay / loaded shots — clean overviews, single callout where there's a next action
    ("IMG_0056.PNG", "12-replay-demo.png",    []),
    ("IMG_0057.PNG", "13-start-loaded.png",   [(0.34, 0.578, 0.66, 0.632)]),
    ("IMG_0058.PNG", "14-replay-loaded.png",  []),
]


def draw_box(im, frac):
    W, H = im.size
    x0, y0, x1, y1 = frac[0]*W, frac[1]*H, frac[2]*W, frac[3]*H  # frac = (x0,y0,x1,y1)
    r = max(14, int(W*0.018))
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    # soft glow underneath
    for w, a in ((26, 40), (16, 70)):
        d.rounded_rectangle([x0, y0, x1, y1], radius=r, outline=(212, 99, 26, a), width=w)
    d.rounded_rectangle([x0, y0, x1, y1], radius=r, outline=ORANGE + (255,), width=8)
    return Image.alpha_composite(im.convert("RGBA"), overlay)


def main():
    thumbs = []
    for src, dest, boxes in TARGETS:
        im = Image.open(os.path.join(RAW, src)).convert("RGBA")
        for b in boxes:
            im = draw_box(im, b)
        im.convert("RGB").save(os.path.join(OUT, dest))
        # thumb for contact sheet
        t = im.convert("RGB").copy()
        t.thumbnail((300, 460))
        thumbs.append((dest, t))
        print("wrote", dest, "boxes:", len(boxes))

    # contact sheet: 3 columns
    cols, pad, lbl = 3, 16, 22
    cw = 300 + pad
    ch = 460 + pad + lbl
    rows = (len(thumbs) + cols - 1)//cols
    sheet = Image.new("RGB", (cols*cw + pad, rows*ch + pad), (255, 255, 255))
    dd = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 16)
    except Exception:
        font = ImageFont.load_default()
    for i, (name, t) in enumerate(thumbs):
        cx = pad + (i % cols)*cw
        cy = pad + (i//cols)*ch
        dd.text((cx, cy), name, fill=(20, 30, 40), font=font)
        sheet.paste(t, (cx, cy+lbl))
    sheet.save(os.path.join(OUT, "_contact_sheet.png"))
    print("wrote _contact_sheet.png")


if __name__ == "__main__":
    main()
