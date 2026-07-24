"""Render data/contributions.json as an animated terminal-style SVG heatmap.

Animation is pure SMIL — CSS keyframes never run behind GitHub's camo image
proxy. Static attributes are always the finished visible state and reveals
begin at 0.01s (never exactly 0), so paused or blocked timelines degrade to
fully-visible static art instead of a blank panel.

The show: a matrix-rain glyph layer drizzles behind everything forever, cells
pop in with scale overshoot and a bright green flash as the wave sweeps left
to right, a scan beam rides the reveal then ghost-sweeps on a 9s loop, bright
cells shimmer, random cells twinkle with star glints, and the yearly total
types itself out next to a blinking cursor.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

CELL, GAP = 13, 3
PITCH = CELL + GAP
HALF = CELL / 2

LEVELS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
BG, BORDER = "#0d1117", "#30363d"
MUTED, GREEN = "#8b949e", "#7ee787"
FLASH = "#b6ffca"

PAD = 20
TITLEBAR = 34
GUTTER_LEFT = 34
GUTTER_TOP = 22
FOOTER = 44

POP_DUR = 0.55           # per-cell pop time (scale 0 -> 1.35 -> 1)
COL_STEP = 0.030         # delay per week column
ROW_STEP = 0.055         # delay per weekday within a column
SWEEP = 53 * COL_STEP + 6 * ROW_STEP + POP_DUR

RAIN_CHARS = "0101010110ZEXA357F*+=-"  # XML-safe only: no < > &

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

FONT = "ui-monospace, SFMono-Regular, 'Cascadia Code', Menlo, Consolas, monospace"


def reveal(delay: float, dur: float = 0.35) -> str:
    """Fade-in hidden from ~t=0 until `delay`; paused timelines show the base
    attributes (visible) because begin is 0.01s, not 0."""
    total = delay + dur
    k = max(delay / total, 0.0001)
    return (
        f'<animate attributeName="opacity" begin="0.01s" dur="{total:.3f}s" '
        f'values="0;0;1" keyTimes="0;{k:.4f};1" fill="freeze"/>'
    )


def matrix_rain(width: int, height: int, clip_id: str,
                step: int = 32, group_opacity: float = 0.13, seed: int = 7) -> str:
    """Endless falling-glyph columns, clipped to the panel — STEPPED, not smooth.

    Film-authentic matrix rain jumps one glyph row at a time, and discrete
    steps on a shared clock are also what keeps this cheap: between steps every
    sampled value is constant, so the SVG raster doesn't repaint every frame
    (continuous translates on ~30 columns pegged a core in testing). Columns
    de-sync via whole-step negative begins and per-column glyph patterns, some
    fall at half speed. Deterministic hash keeps daily re-renders diff-stable.
    A paused timeline shows glyphs parked mid-fall — still fine as texture.
    """
    line = 18
    n = height // line + 2
    period = n * line
    step_time = 0.42
    cols = []
    for i, x in enumerate(range(10, width - 6, step)):
        h = i * 73 + seed * 131
        speed = 1 + (h % 3 == 0)  # a third of the columns fall at half speed
        dur = n * step_time * speed
        begin = -(h % n) * step_time * speed
        tspans = []
        for j in range(2 * n):
            c = RAIN_CHARS[(h + (j % n) * 29) % len(RAIN_CHARS)]
            fo = max(0.10, 0.55 - (j % n) * (0.45 / n))
            tspans.append(
                f'<tspan x="{x}" y="{j * line - period}" fill-opacity="{fo:.2f}">{c}</tspan>'
            )
        offsets = ";".join(f"0 {k * line}" for k in range(n))
        key_times = ";".join(f"{k / n:.4f}" for k in range(n))
        cols.append(
            f'<text font-size="13" fill="{GREEN}">' + "".join(tspans)
            + f'<animateTransform attributeName="transform" type="translate" '
              f'values="{offsets}" keyTimes="{key_times}" calcMode="discrete" '
              f'dur="{dur:.2f}s" begin="{begin:.2f}s" repeatCount="indefinite"/></text>'
        )
    return (
        f'<g opacity="{group_opacity}" clip-path="url(#{clip_id})">'
        + "".join(cols) + "</g>"
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
        f'<clipPath id="panelclip"><rect x="1" y="1" width="{width - 2}" '
        f'height="{height - 2}" rx="12"/></clipPath>'
        "</defs>",
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="12" '
        f'fill="{BG}" stroke="{BORDER}"/>',
        # the rain: behind everything, clipped to the rounded panel
        matrix_rain(width, height, "panelclip"),
        # terminal titlebar; the green dot pulses like a recording light
        f'<circle cx="{PAD + 6}" cy="{TITLEBAR // 2 + 2}" r="6" fill="#ff5f56"/>',
        f'<circle cx="{PAD + 26}" cy="{TITLEBAR // 2 + 2}" r="6" fill="#ffbd2e"/>',
        f'<circle cx="{PAD + 46}" cy="{TITLEBAR // 2 + 2}" r="6" fill="#27c93f">'
        '<animate attributeName="opacity" values="1;0.35;1" dur="2.2s" '
        'repeatCount="indefinite"/></circle>',
        f'<text x="{PAD + 66}" y="{TITLEBAR // 2 + 6}" font-size="12" fill="{MUTED}">'
        f'~/{data["username"]} &#8250; contributions --last-year</text>',
    ]

    # month labels appear as the wave reaches their column
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

    # the grid — cells pop in (scale overshoot + green flash) as the wave
    # sweeps; empty cells are slightly translucent so the rain peeks through
    for d in days:
        cx = x0 + d["week"] * PITCH + HALF
        cy = y0 + d["weekday"] * PITCH + HALF
        delay = d["week"] * COL_STEP + d["weekday"] * ROW_STEP
        total = delay + POP_DUR
        k1 = max(delay / total, 0.0001)
        k2 = min((delay + 0.30) / total, 0.9999)
        color = LEVELS[min(d["level"], 4)]
        n = d["count"]
        tip = f'{n} contribution{"" if n == 1 else "s"} on {d["date"]}'
        fo = ' fill-opacity="0.85"' if d["level"] == 0 else ""

        anims = (
            f'<animateTransform attributeName="transform" type="scale" '
            f'begin="0.01s" dur="{total:.3f}s" values="0;0;1.35;1" '
            f'keyTimes="0;{k1:.4f};{k2:.4f};1" calcMode="spline" '
            f'keySplines="0 0 1 1;0.2 0.7 0.3 1;0.3 0 0.5 1" fill="freeze"/>'
            f'<animate attributeName="fill" begin="0.01s" dur="{total:.3f}s" '
            f'values="{FLASH};{FLASH};{color}" keyTimes="0;{k1:.4f};1" fill="freeze"/>'
        )
        if d["level"] >= 3:  # bright cells pulse briefly, then hold (cheap)
            stagger = (d["week"] * 7 + d["weekday"]) * 0.13 % 4.7
            anims += (
                f'<animate attributeName="opacity" values="1;0.72;1;1" '
                f'keyTimes="0;0.09;0.18;1" dur="5.2s" '
                f'begin="{SWEEP + stagger:.2f}s" repeatCount="indefinite"/>'
            )

        # star glints twinkle forever on a deterministic subset of cells;
        # short flash + long constant hold keeps the raster mostly idle
        glint = ""
        h = (d["week"] * 2654435761 + d["weekday"] * 40503) % 1000
        if h < 200 and d["level"] >= 1:
            gl_begin = 3.0 + (h % 87) / 10.0
            gl_dur = 5.5 + (h % 40) / 10.0
            glint = (
                '<g opacity="0">'
                '<path d="M0 -5.5 L1.3 -1.3 L5.5 0 L1.3 1.3 L0 5.5 L-1.3 1.3 '
                'L-5.5 0 L-1.3 -1.3 Z" fill="#eaffef"/>'
                f'<animate attributeName="opacity" values="0;0.95;0;0" '
                f'keyTimes="0;0.08;0.16;1" dur="{gl_dur:.2f}s" begin="{gl_begin:.2f}s" '
                f'repeatCount="indefinite"/></g>'
            )

        parts.append(
            f'<g transform="translate({cx:.1f},{cy:.1f})">'
            f'<rect x="-{HALF}" y="-{HALF}" width="{CELL}" height="{CELL}" rx="3" '
            f'fill="{color}"{fo}><title>{tip}</title>{anims}</rect>{glint}</g>'
        )

    # scan beam: first pass rides the wave, then ghost-sweeps every 9s
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
