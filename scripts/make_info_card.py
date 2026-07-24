"""Hand-author the neofetch-style info card as an animated SVG (info-card.svg).

SMIL animation only (CSS keyframes don't run reliably in GitHub's camo <img>
sandbox). Static attributes are the final visible state, so with animations
unavailable the card renders complete instead of blank.

Height is exactly 301 to match hackerman.gif (200x188) rendered at width 320.
Widths are chosen so gif (320) + card (440) + table chrome fit inside GitHub's
~790px profile README column WITHOUT max-width squeezing — a squeezed column
scales one image and silently breaks the height match.
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "info-card.svg"

BG, BORDER = "#0d1117", "#30363d"
FG, MUTED, GREEN = "#e6edf3", "#8b949e", "#7ee787"

WIDTH, HEIGHT = 440, 301
PAD = 20
TITLEBAR = 32
LINE_H = 19
FONT_SIZE = 12
CHAR_W = 7.2

HEADER = "AriaCodez@github"
FIELDS = [
    ("OS",     "Windows 11 · PowerShell 7"),
    ("Host",   "ariacodez.ai"),
    ("Kernel", "Claude Code + RTX 5090"),
    ("Shell",  "Git Bash (when nobody's watching)"),
    ("Stack",  "TypeScript · Python · Next.js · Postgres"),
    ("Ships",  "viral engines · trend radars · DM funnels"),
    ("Focus",  "reverse-engineering the algorithm"),
    ("Social", "@AriaCodez · IG / TikTok / YouTube"),
]
PALETTE = ["#ff5f56", "#ffbd2e", "#27c93f", "#39d353", "#7ee787",
           "#58a6ff", "#bc8cff", "#e6edf3"]

RAIN_CHARS = "0101010110ZEXA357F*+=-"  # XML-safe only: no < > &

FONT = "ui-monospace, SFMono-Regular, 'Cascadia Code', Menlo, Consolas, monospace"


def matrix_rain(width: int, height: int, clip_id: str,
                step: int = 32, group_opacity: float = 0.10, seed: int = 3) -> str:
    """Endless falling-glyph columns, clipped to the panel — STEPPED discrete
    jumps on a shared clock (see heatmap script for why: film-authentic AND
    keeps the raster idle between steps; smooth translates pegged a core)."""
    line = 18
    n = height // line + 2
    period = n * line
    step_time = 0.42
    cols = []
    for i, x in enumerate(range(10, width - 6, step)):
        h = i * 73 + seed * 131
        speed = 1 + (h % 3 == 0)
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


def reveal(delay: float, dur: float = 0.4) -> str:
    """Fade-in hidden from ~t=0 until `delay`.

    begin=0.01s (not 0) so a SMIL timeline paused at t=0 — which Chromium's
    image cache produces sometimes — shows the visible base attributes
    instead of freezing on the hidden first value. Degrades static, not blank.
    """
    total = delay + dur
    k = max(delay / total, 0.0001)
    return (
        f'<animate attributeName="opacity" begin="0.01s" dur="{total:.3f}s" '
        f'values="0;0;1" keyTimes="0;{k:.4f};1" fill="freeze"/>'
    )


def main() -> None:
    label_w = max(len(label) for label, _ in FIELDS) + 2

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="AriaCodez terminal info card">',
        f"<style>text {{ font-family: {FONT}; }}</style>",
        f'<defs><clipPath id="cardclip"><rect x="1" y="1" width="{WIDTH - 2}" '
        f'height="{HEIGHT - 2}" rx="12"/></clipPath></defs>',
        f'<rect x="1" y="1" width="{WIDTH - 2}" height="{HEIGHT - 2}" rx="12" '
        f'fill="{BG}" stroke="{BORDER}"/>',
        matrix_rain(WIDTH, HEIGHT, "cardclip"),
        f'<circle cx="{PAD + 4}" cy="{TITLEBAR // 2 + 2}" r="6" fill="#ff5f56"/>',
        f'<circle cx="{PAD + 24}" cy="{TITLEBAR // 2 + 2}" r="6" fill="#ffbd2e"/>',
        f'<circle cx="{PAD + 44}" cy="{TITLEBAR // 2 + 2}" r="6" fill="#27c93f">'
        '<animate attributeName="opacity" values="1;0.35;1" dur="2.2s" '
        'repeatCount="indefinite"/></circle>',
        f'<text x="{PAD + 64}" y="{TITLEBAR // 2 + 6}" font-size="12" fill="{MUTED}">'
        "AriaCodez@github: ~ (fetch)</text>",
    ]

    y = TITLEBAR + 20 + FONT_SIZE
    delay = 0.15

    def line(content: str, d: float) -> str:
        return (
            f'<text x="{PAD}" y="{y}" font-size="{FONT_SIZE}" xml:space="preserve">'
            f"{content}{reveal(d)}</text>"
        )

    parts.append(line(f'<tspan fill="{GREEN}" font-weight="bold">{HEADER}</tspan>', delay))
    y += LINE_H
    delay += 0.15
    parts.append(line(f'<tspan fill="{BORDER}">{"&#9472;" * len(HEADER)}</tspan>', delay))

    for label, value in FIELDS:
        y += LINE_H
        delay += 0.15
        pad = "&#160;" * (label_w - len(label) - 1)
        parts.append(
            line(
                f'<tspan fill="{GREEN}">{label}:</tspan>{pad}'
                f'<tspan fill="{FG}">{value}</tspan>',
                delay,
            )
        )

    # neofetch signature palette strip
    y += LINE_H + 3
    delay += 0.2
    for i, color in enumerate(PALETTE):
        parts.append(
            f'<rect x="{PAD + i * 24}" y="{y - 11}" width="18" height="12" rx="2" '
            f'fill="{color}">{reveal(delay + i * 0.06)}</rect>'
        )

    # prompt with an eternally blinking cursor, anchored to the card's bottom
    # edge so it lines up with the bottom of hackerman.gif next door
    y = HEIGHT - 13
    delay += 0.5
    prompt = f'<tspan fill="{GREEN}">{HEADER}</tspan><tspan fill="{MUTED}"> ~ $</tspan>'
    parts.append(
        f'<text x="{PAD}" y="{y}" font-size="{FONT_SIZE}" xml:space="preserve">'
        f"{prompt}{reveal(delay)}</text>"
    )
    cursor_x = PAD + int((len(HEADER) + 4) * CHAR_W) + 6
    parts.append(
        f'<rect x="{cursor_x}" y="{y - 12}" width="8" height="15" fill="{GREEN}" '
        f'opacity="0"><animate attributeName="opacity" values="0;1;1;0;0" '
        f'keyTimes="0;0.001;0.5;0.501;1" dur="1.1s" begin="{delay + 0.5:.2f}s" '
        f'repeatCount="indefinite"/></rect>'
    )

    parts.append("</svg>")
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"{OUT.name}: {WIDTH}x{HEIGHT}, bottom row at y={y}")


if __name__ == "__main__":
    main()
