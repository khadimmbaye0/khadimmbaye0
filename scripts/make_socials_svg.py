#!/usr/bin/env python3
"""
Build the social badges shown in the README footer: rounded-square chips,
one SVG file per link (white glyph on brand background).

The rounded corners are baked as SVG geometry (rect rx=...), NOT as CSS --
GitHub strips inline styles from README HTML, but full SVG files render as
they are, so the radius always survives.

    python scripts/make_socials_svg.py [--refresh]

Output: socials/<name>.svg  (github, linkedin, x, instagram, email)
"""
import json
import os
import re
import sys

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "..", "data", "social-icons.json")
OUTDIR = os.path.join(HERE, "..", "socials")

SIZE = 72          # canvas side
RADIUS = 16        # corner radius, baked as geometry
GLYPH = 0.55       # glyph size relative to canvas

SOCIALS = [
    # (file name, iconify key, background colors -- 1 color = flat, 2+ = gradient)
    ("github", "simple-icons:github", ["#181717"]),
    ("linkedin", "mdi:linkedin", ["#0A66C2"]),
    ("x", "simple-icons:x", ["#000000"]),
    ("instagram", "simple-icons:instagram", ["#FEDA75", "#FA7E1E", "#D62976", "#962FBF", "#4F5BD5"]),
]


def fetch_icon(key):
    resp = requests.get(f"https://api.iconify.design/{key}.svg",
                        headers={"User-Agent": "profile-readme-bot/1.0"}, timeout=30)
    resp.raise_for_status()
    svg = resp.text
    vb = re.search(r'viewBox="([\d.\s-]+)"', svg)
    if not vb:
        raise RuntimeError(f"no viewBox for {key}")
    x0, y0, w, h = (float(v) for v in vb.group(1).split())
    paths = re.findall(r'<path[^>]*\bd="([^"]+)"', svg)
    if not paths:
        raise RuntimeError(f"no path found for {key}")
    return {"x": x0, "y": y0, "w": w, "h": h, "paths": paths}


def main():
    refresh = "--refresh" in sys.argv[1:]
    cache = {}
    if os.path.exists(CACHE) and not refresh:
        cache = json.load(open(CACHE))

    os.makedirs(OUTDIR, exist_ok=True)
    for name, key, colors in SOCIALS:
        if key not in cache:
            print(f"fetching {key}...")
            cache[key] = fetch_icon(key)

        ic = cache[key]
        s = SIZE * GLYPH / max(ic["w"], ic["h"])
        tx = (SIZE - ic["w"] * s) / 2 - ic["x"] * s
        ty = (SIZE - ic["h"] * s) / 2 - ic["y"] * s
        paths = "".join(f'<path d="{d}"/>' for d in ic["paths"])

        if len(colors) > 1:
            stops = "".join(
                f'<stop offset="{i / (len(colors) - 1):.2f}" stop-color="{c}"/>'
                for i, c in enumerate(colors)
            )
            defs = f'<defs><linearGradient id="g" x1="0" y1="1" x2="1" y2="0">{stops}</linearGradient></defs>'
            fill = "url(#g)"
        else:
            defs = ""
            fill = colors[0]

        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}" '
            f'viewBox="0 0 {SIZE} {SIZE}">{defs}'
            f'<rect width="{SIZE}" height="{SIZE}" rx="{RADIUS}" fill="{fill}"/>'
            f'<g transform="translate({tx:.2f} {ty:.2f}) scale({s:.4f})" fill="#ffffff">{paths}</g>'
            f'</svg>'
        )
        out = os.path.join(OUTDIR, f"{name}.svg")
        with open(out, "w") as f:
            f.write(svg)
        print(f"wrote {out}")

    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    json.dump(cache, open(CACHE, "w"), indent=1)


if __name__ == "__main__":
    main()
