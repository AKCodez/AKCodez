"""Render data/contributions.json as an animated terminal-style SVG heatmap.

Animation is pure SMIL (<animate>/<animateTransform>) — CSS keyframe animations
are NOT reliable inside GitHub's camo-proxied <img> sandbox, SMIL is.
Every element's static attributes are its FINAL visible state, and reveals use
the values="0;0;1" + keyTimes delay trick from t=0 — so if animations ever
don't run, the whole graph degrades to fully-visible static instead of blank.

The show: matrix-style column rain reveals the grid behind a green scan beam,
the beam keeps ghost-sweeping forever, bright cells shimmer, the total types
itself out next to a blinking cursor.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

CELL, GAP = 13, 3
PITCH = CELL + GAP

LEVELS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
BG, BORDER = "#0d1117", "#30363d"
MUTED, GREEN = "#8b949e", "#7ee787"

PAD = 20
TITLEBAR = 34
GUTTER_LEFT = 34
GUTTER_TOP = 22
FOOTER = 44

RAIN_DUR = 0.38          # per-cell drop time
COL_STEP = 0.030         # delay per week column
ROW_STEP = 0.055         # delay per weekday within a column
SWEEP = 53 * COL_STEP + 6 * ROW_STEP + RAIN_DUR  # ≈ full reveal time

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

FONT = "ui-monospace, SFMono-Regular, 'Cascadia Code', Menlo, Consolas, monospace"


def reveal(delay: float, dur: float = 0.35) -> str:
    """Fade-in that hides the element from ~t=0 until `delay`, no CSS needed.

    begin is 0.01s, NOT 0: Chromium sometimes hands GitHub's proxy a cached
    SVG image whose SMIL timeline is paused at t=0. An animation active at
    exactly 0 would freeze the element at values[0] (hidden) — with a tiny
    begin offset the paused state shows the base attributes instead, i.e.
    the finished static art. Never blank.
    """
    total = delay + dur
    k = max(delay / total, 0.0001)
    return (
        f'<animate attributeName="opacity" begin="0.01s" dur="{total:.3f}s" '
        f'values="0;0;1" keyTimes="0;{k:.4f};1" fill="freeze"/>'
    )


def drop(delay: float) -> str:
    """Rain-drop: hold above the slot, then fall in with deceleration."""
    total = delay + RAIN_DUR
    k = max(delay / total, 0.0001)
    return (
        f'<animateTransform attributeName="transform" type="translate" '
        f'begin="0.01s" dur="{total:.3f}s" values="0 -14;0 -14;0 0" '
        f'keyTimes="0;{k:.4f};1" '
        f'calcMode="spline" keySplines="0 0 1 1;0.16 0.84 0.32 1" fill="freeze"/>'
    )


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    days = data["days"]
    weeks = max(d["week"] for d in days) + 1

    grid_w = weeks * PITCH - GAP
    grid_h = 7 * PITCH - GAP
    width = PAD + GUTTER_LEFT + grid_w + PAD
    height = TITLEBAR + GUTTER_TOP + grid_h + FOOTER + PAD
    x0, y0 = PAD + GUTTER_LEFT, TITLEBAR + GUTTER_TOP

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{data["total"]:,} GitHub contributions in the last year">',
        f"<style>text {{ font-family: {FONT}; }}</style>",
        "<defs>"
        '<linearGradient id="beam" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0" stop-color="#39d353" stop-opacity="0"/>'
        '<stop offset="0.5" stop-color="#39d353" stop-opacity="0.85"/>'
        '<stop offset="1" stop-color="#39d353" stop-opacity="0"/>'
        "</linearGradient>"
        "</defs>",
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="12" '
        f'fill="{BG}" stroke="{BORDER}"/>',
        # terminal titlebar; the green dot pulses like a recording light
        f'<circle cx="{PAD + 6}" cy="{TITLEBAR // 2 + 2}" r="6" fill="#ff5f56"/>',
        f'<circle cx="{PAD + 26}" cy="{TITLEBAR // 2 + 2}" r="6" fill="#ffbd2e"/>',
        f'<circle cx="{PAD + 46}" cy="{TITLEBAR // 2 + 2}" r="6" fill="#27c93f">'
        '<animate attributeName="opacity" values="1;0.35;1" dur="2.2s" '
        'repeatCount="indefinite"/></circle>',
        f'<text x="{PAD + 66}" y="{TITLEBAR // 2 + 6}" font-size="12" fill="{MUTED}">'
        f'~/{data["username"]} &#8250; contributions --last-year</text>',
    ]

    # month labels appear as the rain front reaches their column
    week_month = {}
    for d in days:
        wk = d["week"]
        if wk not in week_month or d["date"] < week_month[wk][0]:
            week_month[wk] = (d["date"], int(d["date"][5:7]))
    prev = None
    for wk in sorted(week_month):
        m = week_month[wk][1]
        if m != prev:
            lx = x0 + wk * PITCH
            if lx < width - 44:
                parts.append(
                    f'<text x="{lx}" y="{y0 - 8}" font-size="11" fill="{MUTED}">'
                    f"{MONTHS[m - 1]}{reveal(wk * COL_STEP)}</text>"
                )
            prev = m

    for wd, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        parts.append(
            f'<text x="{PAD}" y="{y0 + wd * PITCH + CELL - 3}" font-size="10" '
            f'fill="{MUTED}">{name}{reveal(wd * ROW_STEP)}</text>'
        )

    # the grid — matrix rain: columns sweep left to right, cells drop into place
    for d in days:
        cx = x0 + d["week"] * PITCH
        cy = y0 + d["weekday"] * PITCH
        delay = d["week"] * COL_STEP + d["weekday"] * ROW_STEP
        n = d["count"]
        tip = f'{n} contribution{"" if n == 1 else "s"} on {d["date"]}'
        anims = reveal(delay, RAIN_DUR) + drop(delay)
        if d["level"] >= 3:  # bright cells keep breathing forever
            stagger = (d["week"] * 7 + d["weekday"]) * 0.13 % 2.6
            anims += (
                f'<animate attributeName="opacity" values="1;0.7;1" dur="3.8s" '
                f'begin="{SWEEP + stagger:.2f}s" repeatCount="indefinite"/>'
            )
        parts.append(
            f'<rect x="{cx}" y="{cy}" width="{CELL}" height="{CELL}" rx="3" '
            f'fill="{LEVELS[min(d["level"], 4)]}"><title>{tip}</title>{anims}</rect>'
        )

    # scan beam: first pass rides the rain front, then ghost-sweeps every 9s
    beam_travel = grid_w + 120
    parts.append(
        f'<g><rect x="{x0 - 40}" y="{y0 - 4}" width="30" height="{grid_h + 8}" '
        f'rx="4" fill="url(#beam)" opacity="0">'
        '<animate attributeName="opacity" values="0;0.55;0.55;0;0" '
        'keyTimes="0;0.02;0.2;0.26;1" dur="9s" repeatCount="indefinite"/>'
        "</rect>"
        f'<animateTransform attributeName="transform" type="translate" '
        f'values="0 0;{beam_travel} 0;{beam_travel} 0" keyTimes="0;0.26;1" '
        f'dur="9s" repeatCount="indefinite"/></g>'
    )

    fy = y0 + grid_h + 26
    total_text = f'{data["total"]:,} contributions in the last year'
    text_w = int(len(total_text) * 7.9)

    # headline stat types itself out behind an animated clip
    steps = 10
    clip_vals = ";".join(str(round(text_w * i / steps)) for i in range(steps + 1))
    type_start, type_dur = SWEEP - 0.4, 0.9
    total_t = type_start + type_dur
    key_times = ["0", f"{type_start / total_t:.4f}"]
    for i in range(1, steps):
        key_times.append(f"{(type_start + type_dur * i / steps) / total_t:.4f}")
    key_times.append("1")
    parts.append(
        "<defs><clipPath id=\"typeclip\">"
        f'<rect x="{x0}" y="{fy - 13}" width="{text_w}" height="18">'
        f'<animate attributeName="width" begin="0.01s" dur="{total_t:.3f}s" '
        f'values="0;0;{clip_vals[2:]}" keyTimes="{";".join(key_times)}" '
        f'calcMode="discrete" fill="freeze"/>'
        "</rect></clipPath></defs>"
    )
    parts.append(
        f'<text x="{x0}" y="{fy}" font-size="13" fill="{GREEN}" '
        f'clip-path="url(#typeclip)">{total_text}</text>'
    )
    # blinking block cursor lives forever at the end of the line
    parts.append(
        f'<rect x="{x0 + text_w + 5}" y="{fy - 12}" width="8" height="15" '
        f'fill="{GREEN}" opacity="0">'
        f'<animate attributeName="opacity" values="0;1;1;0;0" '
        f'keyTimes="0;0.001;0.5;0.501;1" dur="1.1s" begin="{total_t:.2f}s" '
        f'repeatCount="indefinite"/></rect>'
    )

    legend_x = width - PAD - 5 * PITCH - 76
    legend_delay = SWEEP + 0.2
    parts.append(
        f'<text x="{legend_x - 34}" y="{fy}" font-size="10" fill="{MUTED}">Less'
        f"{reveal(legend_delay)}</text>"
    )
    for i, color in enumerate(LEVELS):
        parts.append(
            f'<rect x="{legend_x + i * PITCH}" y="{fy - 10}" width="{CELL}" '
            f'height="{CELL}" rx="3" fill="{color}">'
            f"{reveal(legend_delay + i * 0.06)}</rect>"
        )
    parts.append(
        f'<text x="{legend_x + 5 * PITCH + 6}" y="{fy}" font-size="10" '
        f'fill="{MUTED}">More{reveal(legend_delay + 0.3)}</text>'
    )
    parts.append(
        f'<text x="{width - PAD}" y="{fy + 16}" text-anchor="end" font-size="9" '
        f'fill="{MUTED}">synced {data["generated_at"]}{reveal(legend_delay + 0.3)}</text>'
    )

    parts.append("</svg>")
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"{OUT.name}: {weeks} weeks, {len(days)} cells, {width}x{height}, "
          f"sweep {SWEEP:.2f}s")


if __name__ == "__main__":
    main()
