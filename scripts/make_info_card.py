"""Hand-author the neofetch-style info card as an animated SVG (info-card.svg).

SMIL animation only (CSS keyframes don't run reliably in GitHub's camo <img>
sandbox). Static attributes are the final visible state, so with animations
unavailable the card renders complete instead of blank.

Height is exactly 348 to match hackerman.gif rendered at width 370 (200x188).
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "info-card.svg"

BG, BORDER = "#0d1117", "#30363d"
FG, MUTED, GREEN = "#e6edf3", "#8b949e", "#7ee787"

WIDTH, HEIGHT = 480, 348
PAD = 22
TITLEBAR = 34
LINE_H = 25
FONT_SIZE = 13
CHAR_W = 7.8

HEADER = "aria@github"
FIELDS = [
    ("OS",     "Windows 11 · PowerShell 7"),
    ("Host",   "ariacodez.ai"),
    ("Kernel", "Claude Code + RTX 5090"),
    ("Shell",  "Git Bash (when nobody's watching)"),
    ("Stack",  "TypeScript · Python · Next.js · Postgres"),
    ("Ships",  "viral engines · trend radars · DM funnels"),
    ("Focus",  "reverse-engineering the algorithm"),
]
PALETTE = ["#ff5f56", "#ffbd2e", "#27c93f", "#39d353", "#7ee787",
           "#58a6ff", "#bc8cff", "#e6edf3"]

FONT = "ui-monospace, SFMono-Regular, 'Cascadia Code', Menlo, Consolas, monospace"


def reveal(delay: float, dur: float = 0.4) -> str:
    """Fade-in hidden from t=0 until `delay`; degrades to visible if SMIL is off."""
    total = delay + dur
    k = max(delay / total, 0.0001)
    return (
        f'<animate attributeName="opacity" dur="{total:.3f}s" values="0;0;1" '
        f'keyTimes="0;{k:.4f};1" fill="freeze"/>'
    )


def main() -> None:
    label_w = max(len(label) for label, _ in FIELDS) + 2

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="AriaCodez terminal info card">',
        f"<style>text {{ font-family: {FONT}; }}</style>",
        f'<rect x="1" y="1" width="{WIDTH - 2}" height="{HEIGHT - 2}" rx="12" '
        f'fill="{BG}" stroke="{BORDER}"/>',
        f'<circle cx="{PAD + 4}" cy="{TITLEBAR // 2 + 2}" r="6" fill="#ff5f56"/>',
        f'<circle cx="{PAD + 24}" cy="{TITLEBAR // 2 + 2}" r="6" fill="#ffbd2e"/>',
        f'<circle cx="{PAD + 44}" cy="{TITLEBAR // 2 + 2}" r="6" fill="#27c93f">'
        '<animate attributeName="opacity" values="1;0.35;1" dur="2.2s" '
        'repeatCount="indefinite"/></circle>',
        f'<text x="{PAD + 64}" y="{TITLEBAR // 2 + 6}" font-size="12" fill="{MUTED}">'
        "aria@github: ~ (fetch)</text>",
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

    # prompt with an eternally blinking cursor
    y += LINE_H + 3
    delay += 0.5
    prompt = f'<tspan fill="{GREEN}">aria@github</tspan><tspan fill="{MUTED}"> ~ $</tspan>'
    parts.append(
        f'<text x="{PAD}" y="{y}" font-size="{FONT_SIZE}" xml:space="preserve">'
        f"{prompt}{reveal(delay)}</text>"
    )
    cursor_x = PAD + int(15 * CHAR_W) + 6
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
