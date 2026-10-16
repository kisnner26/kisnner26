"""genera los svg animados del perfil. solo biblioteca estándar.

uso:  python scripts/generate.py             consulta github (GITHUB_TOKEN o la sesión de gh)
      python scripts/generate.py --offline   reutiliza data/snapshot.json
"""

import json
import math
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SNAPSHOT = ROOT / "data" / "snapshot.json"
LOGIN = "kisnner26"

# blanco y negro, y grises entre los dos
BLACK, INK, WHITE = "#000000", "#0b0b0c", "#ffffff"
FONT = "font-family=\"-apple-system,'SF Pro Display','SF Pro Text','Helvetica Neue',Helvetica,Arial,sans-serif\""
MONO = "font-family=\"'SF Mono',Menlo,Consolas,monospace\""

ROLES = ["Apps nativas para Apple.", "Backend transaccional.", "Ingeniería inversa.", "Open source."]

# (etiqueta, titular, subtítulo, meta, color de la animación)
TILES = [
    ("ALTSERVER", ["Vuelve a iniciar", "sesión."], ["Arreglo propuesto para AltServer", "en macOS 27."], "PR abierto en AltStore"),
    ("RELEVO", ["Reparte el", "trabajo."], ["Servicio en Node con worker threads", "y balanceador propio."], "REST · GraphQL · WebSocket · 36 pruebas"),
    ("LUMORA", ["La letra,", "en escena."], ["Lyric videos en vivo con un director", "local que no usa internet."], "Canvas 2D · Mac y navegador"),
]


# ---------------------------------------------------------------- datos
def rest(path):
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request = urllib.request.Request("https://api.github.com/" + path, headers={
            "Authorization": f"bearer {token}", "User-Agent": "profile-generator", "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    return json.loads(subprocess.run(["gh", "api", path], check=True, capture_output=True, text=True).stdout)


def collect():
    merged = rest(f"search/issues?q=author:{LOGIN}+type:pr+is:merged+-user:{LOGIN}&per_page=100")["items"]
    projects = sorted({item["repository_url"].rsplit("/", 1)[-1] for item in merged})
    downloads = None
    try:
        releases = rest(f"repos/{LOGIN}/AltStore/releases")
        downloads = sum(asset["download_count"] for release in releases[:1] for asset in release["assets"][:1])
    except Exception:  # el número es un adorno: si falla, se conserva el anterior
        pass
    return dict(generated=datetime.now(timezone.utc).strftime("%Y-%m-%d"), merged=len(merged), projects=projects, downloads=downloads)


# ---------------------------------------------------------------- piezas
def svg(width, height, title, desc, body, extra_style="", defs=""):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="t d">
  <title id="t">{escape(title)}</title>
  <desc id="d">{escape(desc)}</desc>
  <defs>
{defs}
    <style>
      {extra_style}
      @media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
    </style>
  </defs>
{body}
</svg>
"""


def text(x, y, s, size, fill=WHITE, weight=400, anchor="start", opacity=1, spacing=0, kind="sans", extra=""):
    family = FONT if kind == "sans" else MONO
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    op = f' opacity="{opacity}"' if opacity != 1 else ""
    return f'<text x="{x}" y="{y}" {family} font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{ls}{op} {extra}>{escape(str(s))}</text>'


def hero():
    # barras que laten como un ecualizador, más altas al centro y desvanecidas en los bordes
    bars, count, cy = [], 64, 506
    for i in range(count):
        envelope = math.exp(-(((i - (count - 1) / 2) / 17) ** 2))
        height = 26 + 112 * envelope + 12 * math.sin(i * 1.7)
        x = 30 + i * 17.8
        duration = 1.1 + (math.sin(i * 12.9898) * 43758.5453 % 1) * 1.5
        delay = -(math.sin(i * 78.233) * 43758.5453 % 1) * duration
        bars.append(f'<rect class="bar" x="{x:.1f}" y="{cy - height / 2:.1f}" width="7" height="{height:.1f}" rx="3.5" style="animation-duration:{duration:.2f}s;animation-delay:{delay:.2f}s"/>')
    roles = "".join(f'<g class="role{" first" if i == 0 else ""}" style="animation-delay:{i * 3.2}s">'
                    f'{text(600, 330, role, 46, WHITE, 600, "middle", spacing=-1)}</g>' for i, role in enumerate(ROLES))
    defs = """    <linearGradient id="name" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#8e8e93"/></linearGradient>
    <radialGradient id="glow" cx=".5" cy="0" r=".9"><stop offset="0" stop-color="#fff" stop-opacity=".16"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
    <linearGradient id="edge" x1="0" x2="1"><stop offset="0" stop-color="#000"/><stop offset=".22" stop-color="#fff"/><stop offset=".78" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>
    <mask id="fade"><rect width="1200" height="640" fill="url(#edge)"/></mask>
    <filter id="focus" x="-10%" y="-30%" width="120%" height="160%"><feGaussianBlur stdDeviation="0"><animate attributeName="stdDeviation" from="22" to="0" dur="1.6s" begin="0s" fill="freeze" calcMode="spline" keySplines=".2 .8 .2 1" keyTimes="0;1"/></feGaussianBlur></filter>"""
    body = f"""  <rect width="1200" height="640" rx="32" fill="{BLACK}"/>
  <rect width="1200" height="640" rx="32" fill="url(#glow)" class="glow"/>
  {text(600, 118, "MANAGUA, NICARAGUA", 17, WHITE, 500, "middle", .5, 5)}
  <g filter="url(#focus)"><g class="name">{text(600, 244, "Kisnner Obando", 112, "url(#name)", 700, "middle", spacing=-5)}</g></g>
  {roles}
  <g mask="url(#fade)" fill="{WHITE}">{"".join(bars)}</g>"""
    style = """.name{animation:rise 1.4s cubic-bezier(.2,.8,.2,1) backwards}
      @keyframes rise{from{opacity:0;transform:translateY(26px) scale(.97)}to{opacity:1;transform:none}}
      .glow{animation:glow 6s ease-in-out infinite alternate}
      @keyframes glow{from{opacity:.55}to{opacity:1}}
      .bar{transform-box:fill-box;transform-origin:center;animation:eq 1.6s ease-in-out infinite;transform:scaleY(.25)}
      @keyframes eq{0%,100%{transform:scaleY(.22)}50%{transform:scaleY(1)}}
      .role{opacity:0;animation:role 12.8s infinite}
      @keyframes role{0%{opacity:0;transform:translateY(14px)}4%{opacity:1;transform:none}22%{opacity:1;transform:none}26%{opacity:0;transform:translateY(-14px)}100%{opacity:0}}
      @media (prefers-reduced-motion:reduce){.role{opacity:0}.role.first{opacity:1}.bar{transform:scaleY(.6)}}"""
    return svg(1200, 640, "Kisnner Obando", "Apps nativas para Apple, backend transaccional, ingeniería inversa y open source. Managua, Nicaragua.", body, style, defs)


def tile_visual(index):
    if index == 0:  # un círculo que se cierra y se confirma: el inicio de sesión
        return f"""  <g transform="translate(192 272)">
    <circle r="46" fill="none" stroke="{WHITE}" stroke-opacity=".14" stroke-width="2"/>
    <circle class="ring" r="46" fill="none" stroke="{WHITE}" stroke-width="3" stroke-linecap="round" transform="rotate(-90)"/>
    <path class="tick" d="M-14 2 -4 12 15 -10" fill="none" stroke="{WHITE}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
  </g>""", """.ring{stroke-dasharray:290;animation:ring 5s cubic-bezier(.4,0,.2,1) infinite}
      @keyframes ring{0%{stroke-dashoffset:290}42%{stroke-dashoffset:0}88%{stroke-dashoffset:0;opacity:1}100%{stroke-dashoffset:0;opacity:0}}
      .tick{stroke-dasharray:50;animation:tick 5s ease-out infinite}
      @keyframes tick{0%,40%{stroke-dashoffset:50;opacity:1}58%{stroke-dashoffset:0}88%{stroke-dashoffset:0;opacity:1}100%{opacity:0}}"""
    if index == 1:  # carriles con trabajos que avanzan a distinta velocidad
        lanes, dots = "", ""
        for lane, (y, duration) in enumerate(((246, 2.3), (264, 3.1), (282, 2.0), (300, 3.7))):
            lanes += f'<rect x="56" y="{y}" width="300" height="2" rx="1" fill="{WHITE}" fill-opacity=".14"/>'
            for k in range(2):
                dots += (f'<circle class="job" cx="62" cy="{y + 1}" r="4.5" fill="{WHITE}" '
                         f'style="animation-duration:{duration}s;animation-delay:-{k * duration / 2:.2f}s"/>')
        return f"""  {lanes}
  <rect x="34" y="236" width="8" height="76" rx="4" fill="{WHITE}"/>
  {dots}""", ".job{animation:job 2.5s linear infinite}\n      @keyframes job{from{transform:translateX(0);opacity:0}12%{opacity:1}88%{opacity:1}to{transform:translateX(284px);opacity:0}}"
    # tres versos y el que suena, resaltado
    lines = ""
    for i, (y, w) in enumerate(((246, 262), (270, 196), (294, 232))):
        lines += f'<rect class="verse" x="34" y="{y}" width="{w}" height="12" rx="6" fill="{WHITE}" style="animation-delay:{i * 2}s"/>'
    return f"  {lines}", ".verse{opacity:.2;animation:verse 6s ease-in-out infinite}\n      @keyframes verse{0%,4%{opacity:.2}10%,30%{opacity:1}36%,100%{opacity:.2}}"


def tile(index, label, headline, sub, meta, downloads):
    if index == 0 and downloads:
        meta = f"{downloads} descargas · PR abierto"
    visual, style = tile_visual(index)
    body = f"""  <rect width="384" height="360" rx="28" fill="{INK}"/>
  <rect x=".5" y=".5" width="383" height="359" rx="27.5" fill="none" stroke="{WHITE}" stroke-opacity=".12"/>
  <g class="in" style="animation-delay:{index * .12}s">
    {text(32, 52, label, 13, WHITE, 600, spacing=2.4, opacity=.5)}
    {text(32, 100, headline[0], 34, WHITE, 700, spacing=-1)}
    {text(32, 138, headline[1], 34, WHITE, 700, spacing=-1)}
    {text(32, 180, sub[0], 15.5, WHITE, 400, opacity=.6)}
    {text(32, 202, sub[1], 15.5, WHITE, 400, opacity=.6)}
  </g>
{visual}
  {text(32, 340, meta, 12.5, WHITE, 400, opacity=.45, kind="mono")}"""
    style = f""".in{{animation:rise .9s cubic-bezier(.2,.8,.2,1) backwards}}
      @keyframes rise{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
      {style}"""
    return svg(384, 360, label.title(), " ".join(headline) + " " + " ".join(sub) + " " + meta, body, style)


def strip(d):
    names = " · ".join(d["projects"])
    body = f"""  <rect width="1200" height="84" rx="22" fill="{INK}"/>
  <rect x=".5" y=".5" width="1199" height="83" rx="21.5" fill="none" stroke="{WHITE}" stroke-opacity=".12"/>
  {text(40, 54, str(d["merged"]), 40, WHITE, 700, spacing=-1.5)}
  {text(40 + 26 * len(str(d["merged"])) + 18, 53, "pull requests mergeados", 21, WHITE, 500, opacity=.9)}
  {text(1160, 51, names, 14, WHITE, 400, "end", .45, kind="mono")}"""
    return svg(1200, 84, "Open source", f"{d['merged']} pull requests mergeados en proyectos ajenos: {', '.join(d['projects'])}", body)


def pill(label, width, primary):
    fill, stroke, ink = (WHITE, WHITE, BLACK) if primary else (BLACK, WHITE, WHITE)
    body = f"""  <rect x="1" y="1" width="{width - 2}" height="46" rx="23" fill="{fill}" stroke="{stroke}" stroke-opacity="{1 if primary else .35}" stroke-width="1.5"/>
  {text(width / 2 - 8, 30, label, 17, ink, 600, "middle")}
  <path class="go" d="M{width - 36} 24h11m-5-5 5 5-5 5" fill="none" stroke="{ink}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>"""
    style = ".go{animation:go 2.2s ease-in-out infinite}\n      @keyframes go{50%{transform:translateX(3px)}}"
    return svg(width, 48, label, f"enlace: {label}", body, style)


# ---------------------------------------------------------------- orquestación
def write(name, content):
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / name).write_text(content, encoding="utf-8")


def main():
    previous = json.loads(SNAPSHOT.read_text(encoding="utf-8")) if SNAPSHOT.exists() else {}
    if "--offline" in sys.argv:
        data = previous
    else:
        data = collect()
        if data["downloads"] is None:
            data["downloads"] = previous.get("downloads")
        SNAPSHOT.parent.mkdir(exist_ok=True)
        SNAPSHOT.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    write("hero.svg", hero())
    for index, (label, headline, sub, meta) in enumerate(TILES):
        write(f"tile-{label.lower()}.svg", tile(index, label, headline, sub, meta, data.get("downloads")))
    write("strip.svg", strip(data))
    for label, width, primary in (("Portafolio", 172, True), ("LinkedIn", 150, False), ("GitHub", 140, False), ("Correo", 134, False)):
        write(f"link-{label.lower()}.svg", pill(label, width, primary))
    print("listo:", len(list(ASSETS.glob("*.svg"))), "svg")


if __name__ == "__main__":
    main()
