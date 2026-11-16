"""genera assets/enlaces/*.svg: una pegatina de boceto por cada enlace de la sección "links to every pull request".
cada pegatina es una imagen, así el readme la envuelve en un enlace real y se mantiene el estilo de cuaderno.
solo biblioteca estándar; los enlaces se verificaron contra github antes de escribirlos."""
import random
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SALIDA = ROOT / "assets" / "enlaces"
FONT = "'Segoe Print','Comic Sans MS','Bradley Hand',cursive"
INK, DARK = "#2b2621", "#1f1b16"
PEACH, SKY, SAND, PAPER, LAV, YELLOW, WHITE = "#f6c89a", "#bcd7ea", "#e8dfc9", "#fbf6e9", "#8b7bd8", "#f2c12e", "#ffffff"

# (archivo, texto, relleno, tinta, rotación, borde punteado)
GRUPOS = {
    "altstore": [
        ("altstore-1834", "altstore #1834", DARK, WHITE, -1.2, False),
        ("altsign-61", "altsign #61", DARK, WHITE, 1.0, False),
        ("altsign-62", "altsign #62", DARK, WHITE, -0.8, False),
        ("agradecimiento", "thanks from the official account", YELLOW, INK, 1.2, False),
    ],
    "radare2": [
        ("radare2-26920", "radare2 #26920", PEACH, INK, -1.0, False),
        ("radare2-26749", "radare2 #26749", PEACH, INK, 1.0, False),
        ("radare2-26745", "radare2 #26745", PEACH, INK, -0.7, False),
    ],
    "node": [("node-66687", "node.js #66687", WHITE, INK, 0.9, False)],
    "pefile": [
        ("pefile-617", "pefile #617", SKY, INK, 1.0, False),
        ("pefile-618", "pefile #618", SKY, INK, -0.9, False),
        ("pefile-619", "pefile #619", SKY, INK, 0.8, False),
        ("pefile-620", "pefile #620", SKY, INK, -1.1, False),
    ],
    "otros": [
        ("geode-1396", "geode bindings #1396", PAPER, INK, -0.8, False),
        ("pyelftools-674", "pyelftools #674", PAPER, INK, 1.0, False),
        ("swift-llm-kit-27", "swift-llm-kit #27", PAPER, INK, -0.9, False),
    ],
    "revision": [
        ("revision-swift-nio", "swift-nio", LAV, WHITE, 0.9, True),
        ("revision-swift-nio-extras", "swift-nio-extras", LAV, WHITE, -1.0, True),
        ("revision-rizin", "rizin", SAND, INK, 0.8, True),
        ("revision-gef", "gef", SAND, INK, -0.9, True),
    ],
    "escritos": [
        ("escrito-altserver", "altserver -80045", SAND, INK, -0.9, False),
        ("escrito-apple-watch", "apple watch", SAND, INK, 1.0, False),
        ("escrito-sidecar", "sidecar -203", SAND, INK, -0.8, False),
        ("escrito-portafolio", "portfolio", YELLOW, INK, 1.1, False),
    ],
}

TAM = 22
ALTO = 58


def mano(x, y, w, h, rnd, a=1.6):
    """contorno de rectángulo a mano: cada lado es una curva con un poco de ruido."""
    def j(v):
        return v + rnd.uniform(-a, a)
    lados = ((x, y, x + w, y), (x + w, y, x + w, y + h), (x + w, y + h, x, y + h), (x, y + h, x, y))
    d = f"M {j(x)} {j(y)} " + " ".join(f"Q {j((ax + bx) / 2)} {j((ay + by) / 2)} {j(bx)} {j(by)}" for ax, ay, bx, by in lados) + " Z"
    return d


def pegatina(nombre, texto, relleno, tinta, rot, punteado, etiqueta=False):
    rnd = random.Random(nombre)
    w = round(len(texto) * TAM * 0.6 + 44)
    ancho, alto = w + 16, ALTO
    x, y, h = 8, 10, ALTO - 20
    borde = "#f1e8d6" if relleno == DARK else INK
    trazo = f'stroke="{borde}" stroke-width="2.4"' + (' stroke-dasharray="7 5"' if punteado else "")
    if etiqueta:
        relleno, tinta = "#f6efe0", INK
    sombra = f'<path d="{mano(x + 3, y + 3.5, w, h, rnd)}" fill="{INK}" opacity=".16"/>'
    cuerpo = (f'<path d="{mano(x, y, w, h, rnd)}" fill="{relleno}" {trazo} stroke-linejoin="round" filter="url(#lapiz)"/>'
              f'<path d="{mano(x + 2, y + 2, w - 4, h - 4, rnd, 1.0)}" fill="none" stroke="{WHITE if relleno == DARK else INK}" '
              f'stroke-width="1" opacity=".18"/>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho} {alto}" width="{ancho}" height="{alto}" role="img" aria-label="{escape(texto)}">
<title>{escape(texto)}</title>
<defs><filter id="lapiz" x="-5%" y="-10%" width="110%" height="120%">
  <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="4" result="n"/>
  <feDisplacementMap in="SourceGraphic" in2="n" scale="1.4"/>
</filter></defs>
<g transform="rotate({rot} {ancho / 2} {alto / 2})" font-family="{FONT}">
{sombra}
{cuerpo}
<text x="{x + w / 2}" y="{y + h / 2 + 7.5}" font-size="{TAM}" font-weight="700" fill="{tinta}" text-anchor="middle">{escape(texto)}</text>
</g>
</svg>"""


ETIQUETAS = {"etiqueta-revision": "in review", "etiqueta-escritos": "write-ups"}


def titulo():
    w, h = 1700, 150
    rnd = random.Random("titulo")
    reglas = "".join(f'<line x1="40" y1="{y}" x2="{w - 40}" y2="{y}" stroke="#d9cdb0" stroke-width="1" opacity=".5"/>' for y in (118,))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" font-family="{FONT}" role="img" aria-label="links to every pull request">
<title>links to every pull request</title>
<defs><filter id="papel" x="-5%" y="-5%" width="110%" height="110%">
  <feTurbulence type="fractalNoise" baseFrequency="0.012 0.018" numOctaves="2" seed="11" result="n"/>
  <feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.05 0"/>
</filter></defs>
<rect width="{w}" height="{h}" fill="#f6efe0"/><rect width="{w}" height="{h}" fill="#000" filter="url(#papel)" opacity=".5"/>
{reglas}
<path d="{mano(18, 14, w - 36, h - 28, rnd, 3)}" fill="none" stroke="{INK}" stroke-width="2.2" opacity=".5"/>
<text x="90" y="82" font-size="44" font-weight="800" fill="{INK}" transform="rotate(-1 90 82)">links to every pull request</text>
<path d="M 90 98 Q 330 92 570 99" stroke="#f05033" stroke-width="5" fill="none" opacity=".88" stroke-linecap="round"/>
<text x="{w - 96}" y="124" font-size="22" font-weight="500" fill="#4a433a" text-anchor="end">tap any sticker to open it</text>
</svg>"""


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    (SALIDA / "titulo.svg").write_text(titulo())
    for nombre, texto in ETIQUETAS.items():
        (SALIDA / f"{nombre}.svg").write_text(pegatina(nombre, texto, "none", INK, 0, False, etiqueta=True))
    for items in GRUPOS.values():
        for nombre, texto, relleno, tinta, rot, punteado in items:
            (SALIDA / f"{nombre}.svg").write_text(pegatina(nombre, texto, relleno, tinta, rot, punteado))
    print("listo: assets/enlaces/")


if __name__ == "__main__":
    main()
