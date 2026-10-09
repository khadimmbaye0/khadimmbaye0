#!/usr/bin/env python3
"""
Build stack.svg -- a terminal-window tech-stack card in the same visual
language as the rest of the profile art (dark frame, monospace, reveal
animation). Monochrome icons (Iconify: simple-icons / devicon-plain sets)
are tinted with the profile palette, one accent per group, revealed group
by group with a small pop-in per icon.

    python scripts/make_stack_svg.py [--refresh] [out.svg]

--refresh re-downloads the icon paths (cached in data/stack-icons.json).
STATIC=1 emits the frozen end-state (for local previews).
"""
import json
import os
import re
import sys

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "..", "data", "stack-icons.json")

# palette (same as the other cards)
BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
MUTED = "#7d8590"
CYAN = "#22d3ee"
GREEN = "#39d353"
GOLD = "#f2cc60"
BLUE = "#58a6ff"

W, PAD, TITLEBAR_H = 860, 24, 30
ICON, IGAP = 36, 22
LABEL_SIZE, LABEL_H, LABEL_GAP = 13, 16, 10
GROUP_GAP = 26

GROUPS = [
    ("Languages", CYAN, [
        ("simple-icons:python", "Python"),
        ("mdi:language-java", "Java"),
        ("simple-icons:javascript", "JavaScript"),
        ("simple-icons:html5", "HTML5"),
    ]),
    ("Frameworks · Cloud · Big Data", GREEN, [
        ("simple-icons:react", "React"),
        ("simple-icons:springboot", "Spring Boot"),
        ("simple-icons:amazonwebservices", "AWS"),
        ("simple-icons:terraform", "Terraform"),
        ("simple-icons:apachemaven", "Maven"),
        ("simple-icons:apachespark", "Apache Spark"),
        ("simple-icons:apacheairflow", "Apache Airflow"),
    ]),
    ("Data · Machine Learning", GOLD, [
        ("simple-icons:mysql", "MySQL"),
        ("simple-icons:postgresql", "PostgreSQL"),
        ("simple-icons:numpy", "NumPy"),
        ("simple-icons:pandas", "pandas"),
        ("devicon-plain:matplotlib", "Matplotlib"),
        ("simple-icons:jupyter", "Jupyter"),
        ("simple-icons:scikitlearn", "scikit-learn"),
        ("simple-icons:pytorch", "PyTorch"),
        ("simple-icons:tensorflow", "TensorFlow"),
        ("simple-icons:keras", "Keras"),
    ]),
    ("Developer Tools", BLUE, [
        ("simple-icons:git", "Git"),
        ("simple-icons:github", "GitHub"),
        ("simple-icons:githubactions", "GitHub Actions"),
        ("simple-icons:docker", "Docker"),
        ("simple-icons:linux", "Linux"),
        ("simple-icons:visualstudiocode", "VS Code"),
    ]),
]


def fetch_icon(key):
    resp = requests.get(f"https://api.iconify.design/{key}.svg",
                        headers={"User-Agent": "profile-readme-bot/1.0"}, timeout=30)
    resp.raise_for_status()
    svg = resp.text
    vb = re.search(r'viewBox="([\d.\s-]+)"', svg)
    if not vb:
        raise RuntimeError(f"no viewBox for {key}")
    x0, y0, vw, vh = (float(v) for v in vb.group(1).split())
    paths = re.findall(r'<path[^>]*\bd="([^"]+)"', svg)
    if not paths:
        raise RuntimeError(f"no path found for {key}")
    return {"x": x0, "y": y0, "w": vw, "h": vh, "paths": paths}


def load_icons(refresh=False):
    cache = {}
    if os.path.exists(CACHE) and not refresh:
        cache = json.load(open(CACHE))
    keys = [k for _, _, icons in GROUPS for k, _ in icons]
    missing = [k for k in keys if k not in cache]
    if missing:
        print(f"fetching {len(missing)} icons from iconify...")
        for k in missing:
            cache[k] = fetch_icon(k)
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        json.dump(cache, open(CACHE, "w"), indent=1)
        print(f"cached -> {CACHE}")
    return cache


def main():
    args = list(sys.argv[1:])
    refresh = "--refresh" in args
    args = [a for a in args if not a.startswith("--")]
    out = args[0] if args else os.path.join(HERE, "..", "stack.svg")

    icons = load_icons(refresh)
    static = bool(os.environ.get("STATIC"))

    # layout: measure first
    body_top = TITLEBAR_H + 26
    y = body_top
    layout = []
    for i, (label, color, items) in enumerate(GROUPS):
        row_w = len(items) * ICON + (len(items) - 1) * IGAP
        layout.append((y, label, color, items, (W - row_w) / 2))
        y += LABEL_H + LABEL_GAP + ICON
        if i < len(GROUPS) - 1:
            y += GROUP_GAP
    H = y + 24

    css = (
        '.l{opacity:0;animation:in .45s ease-out both}'
        '.i{transform-box:fill-box;transform-origin:center;opacity:0;'
        'animation:pop .4s cubic-bezier(.2,.8,.2,1) both}'
        '@keyframes in{0%{opacity:0;transform:translateY(10px)}100%{opacity:1;transform:translateY(0)}}'
        '@keyframes pop{0%{opacity:0;transform:translateY(8px) scale(.72)}100%{opacity:1;transform:translateY(0) scale(1)}}'
        '@media (prefers-reduced-motion: reduce){.l,.i{opacity:1!important;transform:none!important;animation:none!important}}'
    ) if not static else ""

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H:.0f}" viewBox="0 0 {W} {H:.0f}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
    ]
    if css:
        parts.append(f'<style>{css}</style>')
    parts += [
        '<defs>'
        f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
        f'<rect width="{W}" height="{H:.0f}" rx="12" fill="url(#bg)"/>',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1:.0f}" rx="12" fill="none" stroke="{FRAME}"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]
    for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dot}"/>')
    parts.append(f'<text x="{W/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
                 f'text-anchor="middle">khadim@github: ~$ ./stack.sh</text>')

    for i, (gy, label, color, items, start_x) in enumerate(layout):
        label_delay = 0.2 + i * 0.45
        lab = (f'<text x="{W/2}" y="{gy + 12}" fill="{color}" font-size="{LABEL_SIZE}" '
               f'text-anchor="middle">&#8212; {label} &#8212;</text>')
        parts.append(f'<g>{lab}</g>' if static else f'<g class="l" style="animation-delay:{label_delay:.2f}s">{lab}</g>')
        iy = gy + LABEL_H + LABEL_GAP
        for j, (key, name) in enumerate(items):
            icon = icons[key]
            s = ICON / max(icon["w"], icon["h"])
            tx = start_x + j * (ICON + IGAP) + (ICON - icon["w"] * s) / 2 - icon["x"] * s
            ty = iy + (ICON - icon["h"] * s) / 2 - icon["y"] * s
            paths = "".join(f'<path d="{d}"/>' for d in icon["paths"])
            inner = (f'<title>{name}</title>'
                     f'<g transform="translate({tx:.2f} {ty:.2f}) scale({s:.4f})" fill="{color}">{paths}</g>')
            if static:
                parts.append(f'<g>{inner}</g>')
            else:
                d = label_delay + 0.12 + j * 0.05
                parts.append(f'<g class="i" style="animation-delay:{d:.2f}s">{inner}</g>')

    parts.append("</svg>")
    svg = "".join(parts)
    with open(out, "w") as f:
        f.write(svg)
    print(f"wrote {out}: {W} x {H:.0f}, {len(svg)//1024} KB, {len(layout)} groups")


if __name__ == "__main__":
    main()
