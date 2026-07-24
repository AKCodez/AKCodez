"""Hand-author the neofetch-style info card as an animated SVG (info-card.svg).

Lines fade in one by one like terminal output; ends with a blinking block cursor.
No volatile numbers here on purpose — the heatmap is the live element.
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "info-card.svg"

BG, BORDER = "#0d1117", "#30363d"
FG, MUTED, GREEN = "#e6edf3", "#8b949e", "#7ee787"

WIDTH = 480
PAD = 22
TITLEBAR = 34
LINE_H = 23
FONT = 13

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

CSS = """
text { font-family: ui-monospace, SFMono-Regular, 'Cascadia Code', Menlo, Consolas, monospace; }
.ln { opacity: 0; animation: rise .5s ease-out forwards; }
@keyframes rise {
  from { opacity: 0; transform: translateY(4px); }
  to   { opacity: 1; transform: translateY(0); }
}
.cur { animation: blink 1.1s steps(1) infinite; }
@keyframes blink { 0%, 55% { opacity: 1; } 56%, 100% { opacity: 0; } }
@media (prefers-reduced-motion: reduce) {
  .ln { animation: none; opacity: 1; }
}
"""


def main() -> None:
    n_lines = 2 + len(FIELDS)  # header + separator + fields
    body_h = n_lines * LINE_H + 14 + 26  # + palette row + prompt row
    height = TITLEBAR + PAD + body_h + PAD

    label_w = max(len(label) for label, _ in FIELDS) + 2  # align values

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img" aria-label="AriaCodez terminal info card">',
        f"<style>{CSS}</style>",
        f'<rect x="1" y="1" width="{WIDTH - 2}" height="{height - 2}" rx="12" '
        f'fill="{BG}" stroke="{BORDER}"/>',
        f'<circle cx="{PAD + 4}" cy="{TITLEBAR // 2 + 2}" r="6" fill="#ff5f56"/>',
        f'<circle cx="{PAD + 24}" cy="{TITLEBAR // 2 + 2}" r="6" fill="#ffbd2e"/>',
        f'<circle cx="{PAD + 44}" cy="{TITLEBAR // 2 + 2}" r="6" fill="#27c93f"/>',
        f'<text x="{PAD + 64}" y="{TITLEBAR // 2 + 6}" font-size="12" fill="{MUTED}">'
        "aria@github: ~ (fetch)</text>",
    ]

    y = TITLEBAR + PAD + FONT
    delay = 150

    def line(content: str, d: int) -> str:
        return (
            f'<text class="ln" style="animation-delay:{d}ms" x="{PAD}" y="{y}" '
            f'font-size="{FONT}" xml:space="preserve">{content}</text>'
        )

    parts.append(line(f'<tspan fill="{GREEN}" font-weight="bold">{HEADER}</tspan>', delay))
    y += LINE_H
    delay += 150
    parts.append(line(f'<tspan fill="{BORDER}">{"&#9472;" * len(HEADER)}</tspan>', delay))

    for label, value in FIELDS:
        y += LINE_H
        delay += 150
        pad = "&#160;" * (label_w - len(label) - 1)
        parts.append(
            line(
                f'<tspan fill="{GREEN}">{label}:</tspan>{pad}'
                f'<tspan fill="{FG}">{value}</tspan>',
                delay,
            )
        )

    # neofetch signature palette strip
    y += LINE_H + 2
    delay += 200
    for i, color in enumerate(PALETTE):
        parts.append(
            f'<rect class="ln" style="animation-delay:{delay + i * 60}ms" '
            f'x="{PAD + i * 24}" y="{y - 11}" width="18" height="12" rx="2" fill="{color}"/>'
        )

    # prompt with blinking cursor
    y += 26
    delay += 700
    prompt = f'<tspan fill="{GREEN}">aria@github</tspan><tspan fill="{MUTED}"> ~ $</tspan>'
    parts.append(
        f'<g class="ln" style="animation-delay:{delay}ms">'
        f'<text x="{PAD}" y="{y}" font-size="{FONT}" xml:space="preserve">{prompt}</text>'
        f'<rect class="cur" x="{PAD + 122}" y="{y - 11}" width="8" height="14" fill="{GREEN}"/>'
        "</g>"
    )

    parts.append("</svg>")
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"{OUT.name}: {WIDTH}x{height}, {len(FIELDS)} fields")


if __name__ == "__main__":
    main()
