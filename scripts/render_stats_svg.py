#!/usr/bin/env python3
"""
Render data/contributions.json + data/stats.json as a terminal-window stats
strip (860 wide) in the same visual language as the other cards: six stat
tiles fade/slide in with count-up numbers, then a monthly-contributions bar
chart grows underneath. Pure SMIL/CSS inside the SVG (GitHub runs both in
<img> SVGs, never JS).

    python scripts/render_stats_svg.py [contributions.json] [stats.json] [out.svg]

STATIC=1 emits the frozen end-state (for local previews).
"""
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_CONTRIB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "data", "contributions.json")
SRC_STATS = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "data", "stats.json")
OUT = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, "..", "stats.svg")
STATIC = bool(os.environ.get("STATIC"))

BG = "#0d1117"
BG2 = "#111722"
TILE = "#161b22"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#e6edf3"
GREEN = "#39d353"
BAR = "#26a641"
ACCENT = "#22d3ee"
GOLD = "#f2cc60"

W, H = 860, 544
PAD = 24
TITLEBAR_H = 32
COLS, ROWS = 3, 2
GAP = 14
TILE_W = (W - PAD * 2 - GAP * (COLS - 1)) / COLS
TILE_H = 128
TILES_TOP = TITLEBAR_H + 20
CHART_TOP = TILES_TOP + ROWS * TILE_H + (ROWS - 1) * GAP + 18
CHART_H = H - PAD - CHART_TOP

# timing (seconds)
TILE_STAGGER = 0.12
SLIDE_DUR = 0.4
COUNT_DUR = 1.0
FRAMES = 14
BAR_START = TILE_STAGGER * 6 + 0.5
BAR_STAGGER = 0.05
BAR_DUR = 0.5

contrib = json.load(open(SRC_CONTRIB))
stats = json.load(open(SRC_STATS))

cur, best = contrib["current_streak"], contrib["best_day"]
n_days = len(contrib["days"])


def short(d):
    return datetime.date.fromisoformat(d).strftime("%b %-d")


def fmt(v):
    return f"{int(round(v)):,}"


tiles = [
    ("current streak", cur["length"], " days", short(cur["start"]) + " – " + short(cur["end"]), GREEN),
    ("contributions", contrib["total_contributions"], "", "in the last year", INK),
    ("merged PRs", stats["merged_prs"], "", "authored · public", ACCENT),
    ("public repos", stats["public_repos"], "", "github.com/" + stats["username"], INK),
    ("best day", best["count"], "", short(best["date"]), GOLD),
    ("active days", contrib["active_days"], f" / {n_days}", f'{contrib["active_days"] / n_days:.0%} of the year', INK),
]

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
    '<style>'
    f'.t{{opacity:0;animation:in {SLIDE_DUR}s ease-out both}}'
    '@keyframes in{0%{opacity:0;transform:translateY(14px)}100%{opacity:1;transform:translateY(0)}}'
    f'.b{{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow {BAR_DUR}s ease-out both}}'
    '@keyframes grow{to{transform:scaleY(1)}}'
    '@media (prefers-reduced-motion: reduce){.t,.b{opacity:1!important;transform:none!important;animation:none!important}}'
    '</style>',
    f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
    f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>',
    f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]
for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dot}"/>')
parts.append(f'<text x="{W/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
             f'text-anchor="middle">khadim@github: ~$ ./stats.sh</text>')

# ---- stat tiles ------------------------------------------------------------
for i, (label, value, suffix, caption, accent) in enumerate(tiles):
    col, row = i % COLS, i // COLS
    x = PAD + col * (TILE_W + GAP)
    y = TILES_TOP + row * (TILE_H + GAP)
    start = i * TILE_STAGGER
    count_start = start + SLIDE_DUR * 0.7
    num_y = y + 86

    group_open = "<g>" if STATIC else f'<g class="t" style="animation-delay:{start:.2f}s">'
    parts.append(group_open)
    parts.append(f'<rect x="{x:.1f}" y="{y}" width="{TILE_W:.1f}" height="{TILE_H}" rx="10" '
                 f'fill="{TILE}" stroke="{FRAME}"/>')
    parts.append(f'<text x="{x+20:.1f}" y="{y+34}" fill="{MUTED}" font-size="19">$ {label}</text>')

    if STATIC:
        parts.append(
            f'<text x="{x+20:.1f}" y="{num_y}" font-size="44" font-weight="700" fill="{accent}">'
            f'{fmt(value)}<tspan font-size="20" font-weight="400" fill="{MUTED}">{suffix}</tspan></text>'
        )
    else:
        for k in range(1, FRAMES + 1):
            p = k / FRAMES
            v = value * (1 - (1 - p) ** 3)
            t_on = count_start + COUNT_DUR * (k - 1) / FRAMES
            t_off = count_start + COUNT_DUR * k / FRAMES
            anim = f'<set attributeName="opacity" to="1" begin="{t_on:.3f}s"/>'
            if k < FRAMES:
                anim += f'<set attributeName="opacity" to="0" begin="{t_off:.3f}s"/>'
            parts.append(
                f'<text x="{x+20:.1f}" y="{num_y}" opacity="0" font-size="44" font-weight="700" fill="{accent}">'
                f'{fmt(v)}<tspan font-size="20" font-weight="400" fill="{MUTED}">{suffix}</tspan>{anim}</text>'
            )
    parts.append(f'<text x="{x+20:.1f}" y="{y+114}" fill="{MUTED}" font-size="17">{caption}</text>')
    parts.append('</g>')

# ---- monthly bars ----------------------------------------------------------
monthly = contrib["monthly"]
chart_x = PAD
chart_w = W - PAD * 2

chart_open = "<g>" if STATIC else f'<g class="t" style="animation-delay:{BAR_START - 0.3:.2f}s">'
parts.append(chart_open)
parts.append(f'<rect x="{chart_x}" y="{CHART_TOP}" width="{chart_w}" height="{CHART_H}" rx="10" '
             f'fill="{TILE}" stroke="{FRAME}"/>')
parts.append(f'<text x="{chart_x+20}" y="{CHART_TOP+34}" fill="{MUTED}" font-size="19">$ contributions / month</text>')
parts.append('</g>')

plot_top = CHART_TOP + 56
plot_bot = CHART_TOP + CHART_H - 36
plot_l, plot_r = chart_x + 22, chart_x + chart_w - 22
slot = (plot_r - plot_l) / len(monthly)
bar_w = slot * 0.6
peak = max(m["total"] for m in monthly) or 1

for i, m in enumerate(monthly):
    h = max(2, (plot_bot - plot_top) * m["total"] / peak)
    bx = plot_l + i * slot + (slot - bar_w) / 2
    fill = GREEN if m["total"] == peak else BAR
    cls = "" if STATIC else f' class="b" style="animation-delay:{BAR_START + i * BAR_STAGGER:.2f}s"'
    parts.append(f'<rect{cls} x="{bx:.1f}" y="{plot_bot - h:.1f}" width="{bar_w:.1f}" height="{h:.1f}" '
                 f'rx="3" fill="{fill}"/>')
    mon = datetime.date.fromisoformat(m["month"] + "-01").strftime("%b")[0]
    parts.append(f'<text x="{bx + bar_w/2:.1f}" y="{plot_bot + 26}" fill="{MUTED}" font-size="15" '
                 f'text-anchor="middle">{mon}</text>')
    if m["total"] == peak:
        label_cls = "" if STATIC else f' class="t" style="animation-delay:{BAR_START + i * BAR_STAGGER + BAR_DUR:.2f}s"'
        parts.append(f'<text{label_cls} x="{bx + bar_w/2:.1f}" y="{plot_bot - h - 8:.1f}" fill="{INK}" '
                     f'font-size="15" text-anchor="middle">{peak:,}</text>')

parts.append("</svg>")
svg = "".join(parts)
with open(OUT, "w") as f:
    f.write(svg)
print(f"wrote {OUT}: {W} x {H}, {len(svg)//1024} KB")
