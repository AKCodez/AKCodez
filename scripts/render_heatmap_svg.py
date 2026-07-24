"""Render data/contributions.json as an animated terminal-style SVG heatmap.

Pure CSS animation inside the SVG (no JS — GitHub's <img> sandbox strips it),
diagonal slide-in wave, native <title> hover tooltips, reduced-motion fallback.
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
FG, MUTED, GREEN = "#e6edf3", "#8b949e", "#7ee787"

PAD = 20
TITLEBAR = 34
GUTTER_LEFT = 34
GUTTER_TOP = 22
FOOTER = 44

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

CSS = """
text { font-family: ui-monospace, SFMono-Regular, 'Cascadia Code', Menlo, Consolas, monospace; }
.d { opacity: 0; animation: cell .45s cubic-bezier(.2,.7,.3,1) forwards; }
@keyframes cell {
  from { opacity: 0; transform: translate(-8px,-8px); }
  to   { opacity: 1; transform: translate(0,0); }
}
.fade { opacity: 0; animation: fadein .6s ease-out forwards; }
@keyframes fadein { to { opacity: 1; } }
@media (prefers-reduced-motion: reduce) {
  .d, .fade { animation: none; opacity: 1; }
}
"""


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
        f"<style>{CSS}</style>",
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="12" '
        f'fill="{BG}" stroke="{BORDER}"/>',
        # terminal titlebar
        f'<circle cx="{PAD + 6}" cy="{TITLEBAR // 2 + 2}" r="6" fill="#ff5f56"/>',
        f'<circle cx="{PAD + 26}" cy="{TITLEBAR // 2 + 2}" r="6" fill="#ffbd2e"/>',
        f'<circle cx="{PAD + 46}" cy="{TITLEBAR // 2 + 2}" r="6" fill="#27c93f"/>',
        f'<text x="{PAD + 66}" y="{TITLEBAR // 2 + 6}" font-size="12" fill="{MUTED}">'
        f'~/{data["username"]} &#8250; contributions --last-year</text>',
    ]

    # month labels: first week column where the month changes
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
                    f'<text class="fade" style="animation-delay:{wk * 26}ms" '
                    f'x="{lx}" y="{y0 - 8}" font-size="11" fill="{MUTED}">{MONTHS[m - 1]}</text>'
                )
            prev = m

    # day-of-week gutter labels
    for wd, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        parts.append(
            f'<text class="fade" x="{PAD}" y="{y0 + wd * PITCH + CELL - 3}" '
            f'font-size="10" fill="{MUTED}">{name}</text>'
        )

    # the grid — diagonal wave: delay grows with week+weekday
    for d in days:
        cx = x0 + d["week"] * PITCH
        cy = y0 + d["weekday"] * PITCH
        delay = (d["week"] + d["weekday"]) * 26
        n = d["count"]
        tip = f'{n} contribution{"" if n == 1 else "s"} on {d["date"]}'
        parts.append(
            f'<rect class="d" x="{cx}" y="{cy}" width="{CELL}" height="{CELL}" rx="3" '
            f'fill="{LEVELS[min(d["level"], 4)]}" style="animation-delay:{delay}ms">'
            f"<title>{tip}</title></rect>"
        )

    sweep_end = (weeks + 7) * 26 + 450
    fy = y0 + grid_h + 26

    # footer left: the headline stat
    parts.append(
        f'<text class="fade" style="animation-delay:{sweep_end}ms" x="{x0}" y="{fy}" '
        f'font-size="13" fill="{GREEN}">{data["total"]:,} contributions in the last year</text>'
    )
    # footer right: legend + sync stamp
    legend_x = width - PAD - 5 * PITCH - 76
    parts.append(
        f'<text class="fade" style="animation-delay:{sweep_end}ms" x="{legend_x - 34}" '
        f'y="{fy}" font-size="10" fill="{MUTED}">Less</text>'
    )
    for i, color in enumerate(LEVELS):
        parts.append(
            f'<rect class="fade" style="animation-delay:{sweep_end + i * 60}ms" '
            f'x="{legend_x + i * PITCH}" y="{fy - 10}" width="{CELL}" height="{CELL}" '
            f'rx="3" fill="{color}"/>'
        )
    parts.append(
        f'<text class="fade" style="animation-delay:{sweep_end + 300}ms" '
        f'x="{legend_x + 5 * PITCH + 6}" y="{fy}" font-size="10" fill="{MUTED}">More</text>'
    )
    parts.append(
        f'<text class="fade" style="animation-delay:{sweep_end + 300}ms" x="{width - PAD}" '
        f'y="{fy + 16}" text-anchor="end" font-size="9" fill="{MUTED}">'
        f'synced {data["generated_at"]}</text>'
    )

    parts.append("</svg>")
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"{OUT.name}: {weeks} weeks, {len(days)} cells, {width}x{height}")


if __name__ == "__main__":
    main()
