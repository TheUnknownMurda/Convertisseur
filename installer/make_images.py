"""Génère les images de l'assistant d'installation (thèmes clair et sombre, plusieurs résolutions).

    .venv\\Scripts\\python installer\\make_images.py
"""
import io
from pathlib import Path

import resvg_py
from PIL import Image

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
ICON = HERE.parent / "web" / "icon.svg"
SPECTRUM = ["#ff6b8b", "#ffa94d", "#ffd43b", "#5fe0b0", "#4dabf7", "#9775fa"]

THEMES = {
    "light": {"bg": "#f3f2ee", "mix": 0.14, "ink": 0.62, "glow": 0.10,
              "video": "#7d5cff", "image": "#12a877", "doc": "#3d7dff", "pdf": "#ef4a4f"},
    "dark": {"bg": "#101115", "mix": 0.18, "ink": 1.0, "glow": 0.16,
             "video": "#9b80ff", "image": "#34d39b", "doc": "#6b9cff", "pdf": "#ff6b6f"},
}


def mix(c1: str, c2: str, t: float) -> str:
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def stops() -> str:
    return "".join(f'<stop offset="{i / (len(SPECTRUM) - 1):.2f}" stop-color="{c}"/>' for i, c in enumerate(SPECTRUM))


def wizard_svg(theme: str) -> str:
    """Grande image (164 x 314) : des formats entrent dans le symbole et ressortent convertis, de haut en bas."""
    t = THEMES[theme]
    ink_ref = "#ffffff" if theme == "dark" else "#15141a"
    chips, lines = [], []
    gx, gy, gw, gh = 57, 118, 50, 84                  # symbole vertical : rond en haut, carré en bas

    def chip(cx, cy, label, fam):
        col = t[fam]
        fill = mix(t["bg"], col, t["mix"])
        text = col if theme == "dark" else mix(col, ink_ref, 1 - t["ink"])
        chips.append(f'<rect x="{cx - 22}" y="{cy - 11}" width="44" height="22" rx="7" fill="{fill}" stroke="{col}" '
                     f'stroke-opacity=".55" stroke-width="1"/>'
                     f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" font-family="Bahnschrift" font-weight="600" '
                     f'font-size="10.5" letter-spacing=".6" fill="{text}">{label}</text>')

    for cx, (label, fam) in zip((33, 82, 131), (("MOV", "video"), ("HEIC", "image"), ("DOCX", "doc"))):
        chip(cx, 54, label, fam)
        lines.append(f'<path d="M{cx} 65 C{cx} 95 82 92 82 {gy - 3}" fill="none" stroke="{t[fam]}" stroke-width="1.6" '
                     f'stroke-opacity=".55" stroke-dasharray="1.5 5" stroke-linecap="round"/>')
    for cx, (label, fam) in zip((33, 82, 131), (("MP4", "video"), ("JPG", "image"), ("PDF", "pdf"))):
        chip(cx, 262, label, fam)
        lines.append(f'<path d="M82 {gy + gh + 3} C82 228 {cx} 225 {cx} 251" fill="none" stroke="{t[fam]}" stroke-width="1.6" '
                     f'stroke-opacity=".55" stroke-dasharray="1.5 5" stroke-linecap="round"/>')
    r, c = gw / 2, gh * 0.07
    s1, s2, sh = gy + gh * 0.443, gy + gh * 0.638, gh * 0.062
    glyph = (f'<path mask="url(#m)" fill="url(#g)" d="M{gx} {gy + r} A{r} {r} 0 0 1 {gx + gw} {gy + r} '
             f'V{gy + gh - c} Q{gx + gw} {gy + gh} {gx + gw - c} {gy + gh} H{gx + c} Q{gx} {gy + gh} {gx} {gy + gh - c} Z"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 164 314">
  <defs>
    <linearGradient id="g" gradientUnits="userSpaceOnUse" x1="0" y1="{gy}" x2="0" y2="{gy + gh}">{stops()}</linearGradient>
    <radialGradient id="ga" cx="1" cy="0" r="1"><stop offset="0" stop-color="#9775fa" stop-opacity="{t['glow']}"/><stop offset="1" stop-color="#9775fa" stop-opacity="0"/></radialGradient>
    <radialGradient id="gb" cx="0" cy="1" r="1"><stop offset="0" stop-color="#ffa94d" stop-opacity="{t['glow']}"/><stop offset="1" stop-color="#ffa94d" stop-opacity="0"/></radialGradient>
    <filter id="blur" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="12"/></filter>
    <mask id="m" maskUnits="userSpaceOnUse"><rect x="0" y="0" width="164" height="314" fill="#fff"/>
      <rect x="{gx - 4}" y="{s1}" width="{gw + 8}" height="{sh}" fill="#000"/><rect x="{gx - 4}" y="{s2}" width="{gw + 8}" height="{sh}" fill="#000"/></mask>
  </defs>
  <rect width="164" height="314" fill="{t['bg']}"/>
  <rect width="164" height="314" fill="url(#ga)"/>
  <rect width="164" height="314" fill="url(#gb)"/>
  {''.join(lines)}
  <ellipse cx="82" cy="{gy + gh / 2}" rx="34" ry="46" fill="url(#g)" opacity=".45" filter="url(#blur)"/>
  {glyph}
  {''.join(chips)}
</svg>'''


def render(svg: str, width: int) -> Image.Image:
    return Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=svg, width=width)))).convert("RGBA")


def save_bmp(img: Image.Image, bg: str, path: Path):
    flat = Image.new("RGBA", img.size, bg)
    flat.alpha_composite(img)
    flat.convert("RGB").save(path, "BMP")


def main():
    ASSETS.mkdir(exist_ok=True)
    icon_svg = ICON.read_text(encoding="utf-8")
    for theme, t in THEMES.items():
        svg = wizard_svg(theme)
        for w in (164, 246, 328):
            save_bmp(render(svg, w), t["bg"], ASSETS / f"wizard-{theme}-{w}.bmp")
        for w in (55, 83, 110):
            canvas = Image.new("RGBA", (w, w), t["bg"])
            logo = render(icon_svg, round(w * 0.86))
            canvas.alpha_composite(logo, ((w - logo.width) // 2, (w - logo.height) // 2))
            save_bmp(canvas, t["bg"], ASSETS / f"small-{theme}-{w}.bmp")
    print("images :", ", ".join(sorted(p.name for p in ASSETS.glob("*.bmp"))))


if __name__ == "__main__":
    main()
