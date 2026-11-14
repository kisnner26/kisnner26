"""genera assets/aportes.svg: tarjeta de aportes aceptados, mismo estilo de boceto que sketch.svg y counter.svg.
solo biblioteca estándar. los datos son fijos y se verificaron contra github antes de escribirlos."""
import random
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W, H = 1700, 1270
FONT = "'Segoe Print','Comic Sans MS','Bradley Hand',cursive"
PAPER, INK, BODY, LINE = "#f6efe0", "#2b2621", "#4a433a", "#d9cdb0"
ORANGE, YELLOW, GREEN, BLUE, LAV, DARK, PEACH, SAND, SKY = "#f05033", "#f2c12e", "#2fa86b", "#3b82c4", "#8b7bd8", "#1f1b16", "#f6c89a", "#e8dfc9", "#bcd7ea"
rnd = random.Random(26)


def j(v, a=2.2):
    return v + rnd.uniform(-a, a)


def wobbly(x, y, w, h, fill="none", stroke=INK, sw=2.6, opacity=0.9, rot=0.0, dash=None):
    """rectángulo dibujado a mano: cada lado son dos curvas con un poco de ruido."""
    pts = []
    for (ax, ay, bx, by) in ((x, y, x + w, y), (x + w, y, x + w, y + h), (x + w, y + h, x, y + h), (x, y + h, x, y)):
        mx, my = (ax + bx) / 2, (ay + by) / 2
        pts.append(f"Q {j(mx)} {j(my)} {j(bx)} {j(by)}")
    d = f"M {j(x)} {j(y)} " + " ".join(pts) + " Z"
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    cx, cy = x + w / 2, y + h / 2
    return f'<g transform="rotate({rot} {cx} {cy})"><path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{opacity}"{dash_attr} stroke-linejoin="round"/></g>'


def text(x, y, s, size=20, fill=BODY, weight=500, anchor="start", rot=0.0, style="normal"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" font-style="{style}" '
            f'text-anchor="{anchor}" transform="rotate({rot} {x} {y})">{escape(s)}</text>')


def underline(x, y, w, color=ORANGE, sw=5):
    return f'<path d="M {x} {y} Q {x + w / 2} {y - 4} {x + w} {y + 1}" stroke="{color}" stroke-width="{sw}" fill="none" opacity="0.88" stroke-linecap="round"/>'


def tag(x, y, label, fill=SAND, ink=INK, size=17):
    w = len(label) * (size * 0.62) + 28
    return (wobbly(x, y - size - 6, w, size + 16, fill=fill, stroke=INK, sw=1.8, opacity=0.8) + text(x + w / 2, y + 2, label, size, ink, 700, "middle")), w


def card(x, y, w, h, title, stars, bullets, fill, ink=INK, body=BODY, rot=-0.4, border=INK, tag_fill=SAND):
    out = [wobbly(x, y, w, h, fill=fill, stroke=border, sw=2.6, rot=rot)]
    out.append(text(x + 30, y + 52, title, 33, ink, 800, rot=rot))
    t, tw = tag(x + 30, y + 92, stars, fill=tag_fill)
    out.append(t)
    yy = y + 142
    for line in bullets:
        out.append(text(x + 30, yy, line, 20, body, 500))
        yy += 33
    return "\n".join(out)


def build():
    o = []
    o.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" font-family="{FONT}">')
    o.append('''<title>Accepted contributions in other people's projects: AltStore and AltSign, radare2, Node.js, pefile, Geode, pyelftools, swift-llm-kit.</title>
<defs>
  <filter id="paperTex" x="-5%" y="-5%" width="110%" height="110%">
    <feTurbulence type="fractalNoise" baseFrequency="0.012 0.018" numOctaves="2" seed="11" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.05 0"/>
  </filter>
</defs>''')
    o.append(f'<rect width="{W}" height="{H}" fill="{PAPER}"/><rect width="{W}" height="{H}" fill="#000" filter="url(#paperTex)" opacity="0.5"/>')
    for yy in range(70, H - 30, 56):
        o.append(f'<line x1="36" y1="{yy}" x2="{W - 36}" y2="{yy}" stroke="{LINE}" stroke-width="1" opacity="0.5"/>')
    o.append(wobbly(18, 14, W - 36, H - 28, stroke=INK, sw=2.2, opacity=0.5, rot=0))

    o.append(text(90, 104, "accepted contributions", 46, INK, 800, rot=-1))
    o.append(underline(90, 122, 520))
    o.append(text(90, 166, "pull requests merged into other people's projects, accepted by their maintainers", 21, BODY, 500))

    # --- altstore / altsign (tarjeta oscura grande)
    hx, hy, hw, hh = 90, 204, 1520, 318
    o.append(wobbly(hx, hy, hw, hh, fill=DARK, stroke=INK, sw=2.6, rot=-0.3))
    o.append(text(hx + 36, hy + 62, "AltStore / AltSign", 40, "#ffffff", 800))
    t, _ = tag(hx + 36, hy + 104, "15k stars", fill=YELLOW)
    o.append(t)
    lines = [
        "the macOS 27 sign-in failure (error -80045): traced the cause and sent the fix",
        "the creator of AltStore built on it to fix AltStore Classic itself",
        "it shipped in the official AltServer 1.8.2 and Classic 2.3.1, and the",
        "official account thanked me for it in public",
        "later: the HTTP 415 error when asking for the SMS code, merged as AltSign#62",
    ]
    yy = hy + 156
    for i, line in enumerate(lines):
        pad = 28 if i == 3 else 0
        o.append(text(hx + 36 + pad, yy, ("- " if i not in (3,) else "") + line, 22, "#f1e8d6", 500))
        yy += 32
    # pegatina: agradecimiento
    sx, sy = hx + hw - 290, hy + 44
    o.append(f'<g transform="rotate(5 {sx + 110} {sy + 115})">' + wobbly(sx, sy, 220, 230, fill=YELLOW, stroke="#ffffff", sw=3, opacity=0.95, rot=0) +
             text(sx + 110, sy + 62, "thanked by", 25, INK, 800, "middle") + text(sx + 110, sy + 98, "the official", 25, INK, 800, "middle") +
             text(sx + 110, sy + 134, "AltStore", 25, INK, 800, "middle") + text(sx + 110, sy + 170, "account", 25, INK, 800, "middle") +
             f'<path d="M {sx + 50} {sy + 188} Q {sx + 110} {sy + 180} {sx + 170} {sy + 188}" stroke="{ORANGE}" stroke-width="4" fill="none" stroke-linecap="round"/></g>')

    # --- fila 2
    cw, gap = 486, 31
    xs = [90, 90 + cw + gap, 90 + 2 * (cw + gap)]
    y2, h2 = 556, 330
    o.append(card(xs[0], y2, cw, h2, "radare2", "25k stars", [
        "3 pull requests, merged by its",
        "maintainer",
        "- nested memory references in",
        "  numeric expressions (+220 lines)",
        "- two cleanups of the help text",
    ], PEACH, rot=-0.4))
    o.append(card(xs[1], y2, cw, h2, "Node.js", "124k stars", [
        "documentation fix reviewed and",
        "merged by the project",
        "- QuicStream direction and id",
        "  types, corrected in the docs",
    ], "#ffffff", rot=0.3, tag_fill=SKY))
    o.append(card(xs[2], y2, cw, h2, "pefile", "2k stars", [
        "4 pull requests, merged by its",
        "maintainer",
        "- PEiD signatures and wildcards",
        "- repeated import threshold",
        "- python 3 byte buffers",
    ], SKY, rot=-0.3, tag_fill=SAND))

    # --- fila 3
    y3, h3 = 920, 170
    small = [
        ("Geode bindings", "112 stars", "Windows 2.2091 addresses fixed", PAPER),
        ("pyelftools", "2k stars", "packaging metadata fixed", PAPER),
        ("swift-llm-kit", "Swift", "a Keychain race on concurrent saves", PAPER),
    ]
    for i, (t, s, d, f) in enumerate(small):
        o.append(wobbly(xs[i], y3, cw, h3, fill="#fbf6e9", stroke=INK, sw=2.4, rot=0.3 if i % 2 else -0.3))
        o.append(text(xs[i] + 28, y3 + 50, t, 28, INK, 800))
        tg, _ = tag(xs[i] + 28, y3 + 92, s, fill=SAND, size=16)
        o.append(tg)
        o.append(text(xs[i] + 28, y3 + 138, d, 20, BODY, 500))

    # --- en revisión
    y4 = 1166
    o.append(wobbly(90, y4 - 36, 1520, 84, fill="none", stroke=INK, sw=2.2, opacity=0.7, dash="9 7"))
    o.append(text(122, y4 + 10, "in review", 28, INK, 800))
    px = 300
    for label in ("Apple swift-nio", "Apple swift-nio-extras", "rizin", "GEF"):
        t, w = tag(px, y4 + 8, label, fill=LAV if label.startswith("Apple") else SAND, ink="#ffffff" if label.startswith("Apple") else INK, size=20)
        o.append(t)
        px += w + 26
    o.append(text(W - 96, H - 24, "sketched by kisnner", 24, INK, 700, "end", rot=-1, style="italic"))
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    (ROOT / "assets" / "aportes.svg").write_text(build())
    print("listo: assets/aportes.svg")
