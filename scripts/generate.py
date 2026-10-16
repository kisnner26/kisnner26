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

MANAGUA = (12.13, -86.25)
ROLES = ["Apps nativas para Apple.", "Backend transaccional.", "Ingeniería inversa.", "Open source."]

# (etiqueta, titular, subtítulo, meta)
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


def graphql(query, variables):
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request = urllib.request.Request("https://api.github.com/graphql",
                                         data=json.dumps({"query": query, "variables": variables}).encode(),
                                         headers={"Authorization": f"bearer {token}", "User-Agent": "profile-generator"})
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
    else:
        arguments = ["gh", "api", "graphql", "-f", f"query={query}"]
        for key, value in variables.items():
            arguments += ["-f", f"{key}={value}"]
        result = json.loads(subprocess.run(arguments, check=True, capture_output=True, text=True).stdout)
    if "errors" in result:
        raise RuntimeError(result["errors"])
    return result["data"]


CALENDAR = """query($login:String!){ user(login:$login){ contributionsCollection{ contributionCalendar{
 totalContributions weeks{ contributionDays{ date contributionCount } } } } } }"""


def collect():
    merged = rest(f"search/issues?q=author:{LOGIN}+type:pr+is:merged+-user:{LOGIN}&per_page=100")["items"]
    projects = sorted({item["repository_url"].rsplit("/", 1)[-1] for item in merged})
    downloads = None
    try:
        releases = rest(f"repos/{LOGIN}/AltStore/releases")
        downloads = sum(asset["download_count"] for release in releases[:1] for asset in release["assets"][:1])
    except Exception:  # el número es un adorno: si falla, se conserva el anterior
        pass
    calendar = graphql(CALENDAR, {"login": LOGIN})["user"]["contributionsCollection"]["contributionCalendar"]
    days = [day["contributionCount"] for week in calendar["weeks"] for day in week["contributionDays"]]
    weeks = [sum(day["contributionCount"] for day in week["contributionDays"]) for week in calendar["weeks"]]
    first = calendar["weeks"][0]["contributionDays"][0]["date"]
    streak = best = 0
    for count in days:
        streak = streak + 1 if count else 0
        best = max(best, streak)
    return dict(generated=datetime.now(timezone.utc).strftime("%Y-%m-%d"), merged=len(merged), projects=projects, downloads=downloads,
                total=calendar["totalContributions"], weeks=weeks, first=first, streak=best, best_day=max(days or [0]))


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


def rnd(i, salt):
    return (math.sin(i * 12.9898 + salt * 78.233) * 43758.5453) % 1


# ---------------------------------------------------------------- el globo
def globe(cx, cy, radius, period=30, frames=36, points=380, tilt=-0.38):
    """un globo de puntos que gira. cada punto se anima con smil entre posiciones precalculadas;
    los de atrás se apagan y achican para que se lea la profundidad."""

    def project(lat, lon, angle):
        la, lo = math.radians(lat), math.radians(lon) + angle
        x, y, z = math.cos(la) * math.sin(lo), math.sin(la), math.cos(la) * math.cos(lo)
        y, z = y * math.cos(tilt) - z * math.sin(tilt), y * math.sin(tilt) + z * math.cos(tilt)
        return cx + radius * x, cy - radius * y, z

    angles = [2 * math.pi * f / frames for f in range(frames + 1)]
    out = []
    # paralelos: girar sobre el eje no los cambia, así que son elipses quietas
    for lat in (-60, -30, 0, 30, 60):
        la = math.radians(lat)
        ry = radius * math.cos(la) * abs(math.sin(tilt))
        out.append(f'<ellipse cx="{cx}" cy="{cy - radius * math.sin(la) * math.cos(tilt):.1f}" rx="{radius * math.cos(la):.1f}" ry="{ry:.1f}" '
                   f'fill="none" stroke="{WHITE}" stroke-opacity="{.16 if lat == 0 else .07}" stroke-width="1"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{WHITE}" stroke-opacity=".22" stroke-width="1.2"/>')

    golden = math.pi * (3 - math.sqrt(5))
    for i in range(points):
        y = 1 - 2 * (i + .5) / points
        lat = math.degrees(math.asin(y))
        lon = math.degrees((i * golden) % (2 * math.pi))
        xs, ys, os_ = [], [], []
        for a in angles:
            px, py, z = project(lat, lon, a)
            xs.append(f"{px:.1f}")
            ys.append(f"{py:.1f}")
            os_.append(f"{max(.06, ((z + 1) / 2) ** 2.2):.2f}")
        size = 1.4 + 1.4 * rnd(i, 3)
        out.append(f'<circle r="{size:.1f}" fill="{WHITE}">'
                   f'<animate attributeName="cx" values="{";".join(xs)}" dur="{period}s" repeatCount="indefinite"/>'
                   f'<animate attributeName="cy" values="{";".join(ys)}" dur="{period}s" repeatCount="indefinite"/>'
                   f'<animate attributeName="opacity" values="{";".join(os_)}" dur="{period}s" repeatCount="indefinite"/></circle>')

    # managua: un punto con un anillo que late y su coordenada, visibles solo de frente
    xs, ys, os_ = [], [], []
    for a in angles:
        px, py, z = project(*MANAGUA, a)
        xs.append(f"{px:.1f}")
        ys.append(f"{py:.1f}")
        os_.append("1" if z > .15 else f"{max(0, z + .15) * 4:.2f}" if z > -.1 else "0")
    motion = (f'<animate attributeName="cx" values="{";".join(xs)}" dur="{period}s" repeatCount="indefinite"/>'
              f'<animate attributeName="cy" values="{";".join(ys)}" dur="{period}s" repeatCount="indefinite"/>')
    fade = f'<animate attributeName="opacity" values="{";".join(os_)}" dur="{period}s" repeatCount="indefinite"/>'
    ring = (f'<circle r="6" fill="none" stroke="{WHITE}" stroke-width="1.6">{motion}'
            f'<animate attributeName="r" values="6;30" dur="2.2s" repeatCount="indefinite"/>'
            f'<animate attributeName="stroke-opacity" values=".9;0" dur="2.2s" repeatCount="indefinite"/></circle>')
    dot = f'<circle r="5.5" fill="{WHITE}">{motion}</circle>'
    label_x = ";".join(f"{float(x) + 14:.1f}" for x in xs)
    label_y = ";".join(f"{float(y) - 12:.1f}" for y in ys)
    label = (f'<text {MONO} font-size="13" font-weight="600" fill="{WHITE}" letter-spacing="1">MANAGUA'
             f'<animate attributeName="x" values="{label_x}" dur="{period}s" repeatCount="indefinite"/>'
             f'<animate attributeName="y" values="{label_y}" dur="{period}s" repeatCount="indefinite"/></text>')
    out.append(f'<g>{fade}{ring}{dot}{label}</g>')
    return "\n  ".join(out)


def hero():
    stars = "".join(
        f'<circle cx="{40 + rnd(i, 1) * 1120:.0f}" cy="{30 + rnd(i, 2) * 580:.0f}" r="{.6 + rnd(i, 4) * .9:.1f}" fill="{WHITE}" class="star" '
        f'style="animation-duration:{2.5 + rnd(i, 5) * 4:.1f}s;animation-delay:-{rnd(i, 6) * 6:.1f}s"/>' for i in range(46))
    roles = "".join(f'<g class="role{" first" if i == 0 else ""}" style="animation-delay:{i * 3.2}s">'
                    f'{text(76, 470, role, 34, WHITE, 500, spacing=-.6, opacity=.82)}</g>' for i, role in enumerate(ROLES))
    defs = """    <linearGradient id="silver" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="1400" y2="0" spreadMethod="reflect">
      <stop offset="0" stop-color="#8e8e93"/><stop offset=".42" stop-color="#d8d8dc"/><stop offset=".5" stop-color="#ffffff"/><stop offset=".58" stop-color="#d8d8dc"/><stop offset="1" stop-color="#8e8e93"/>
      <animateTransform attributeName="gradientTransform" type="translate" values="-700 0;700 0" dur="6s" repeatCount="indefinite"/>
    </linearGradient>
    <radialGradient id="halo" cx="880" cy="320" r="360" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#fff" stop-opacity=".13"/><stop offset=".55" stop-color="#fff" stop-opacity=".03"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
    <clipPath id="wipe"><rect x="0" y="120" width="0" height="300"><animate attributeName="width" from="0" to="760" dur="1.6s" begin=".2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".25 .8 .25 1"/></rect></clipPath>
    <clipPath id="card"><rect width="1200" height="640" rx="32"/></clipPath>"""
    body = f"""  <g clip-path="url(#card)">
  <rect width="1200" height="640" fill="{BLACK}"/>
  {stars}
  <rect width="1200" height="640" fill="url(#halo)" class="breathe"/>
  <g transform="rotate(-16 880 320)"><path d="M570 320 A310 74 0 0 1 1190 320" fill="none" stroke="{WHITE}" stroke-opacity=".10" stroke-width="1.2"/></g>
  {globe(880, 320, 236)}
  <g transform="rotate(-16 880 320)">
    <path d="M1190 320 A310 74 0 0 1 570 320" fill="none" stroke="{WHITE}" stroke-opacity=".28" stroke-width="1.2"/>
    <circle r="5" fill="{WHITE}"><animateMotion dur="9s" repeatCount="indefinite" path="M570 320 A310 74 0 0 1 1190 320 A310 74 0 0 1 570 320"/><animate attributeName="opacity" values=".18;1" keyTimes="0;.5" calcMode="discrete" dur="9s" repeatCount="indefinite"/></circle>
  </g>
  {text(76, 150, "MANAGUA, NICARAGUA · 12.13°N 86.25°W", 14, WHITE, 500, opacity=.5, spacing=2.4, kind="mono")}
  <g clip-path="url(#wipe)">
    {text(70, 284, "Kisnner", 132, "url(#silver)", 700, spacing=-6)}
    {text(70, 404, "Obando.", 132, "url(#silver)", 700, spacing=-6)}
  </g>
  {roles}
  {text(76, 560, "kisnner26", 14, WHITE, 500, opacity=.35, spacing=2, kind="mono")}
  </g>"""
    style = """.star{animation:twinkle 4s ease-in-out infinite}
      @keyframes twinkle{0%,100%{opacity:.08}50%{opacity:.55}}
      .breathe{animation:breathe 7s ease-in-out infinite alternate}
      @keyframes breathe{from{opacity:.6}to{opacity:1}}
      .role{opacity:0;animation:role 12.8s infinite}
      @keyframes role{0%{opacity:0;transform:translateY(16px)}4%{opacity:1;transform:none}22%{opacity:1;transform:none}26%{opacity:0;transform:translateY(-16px)}100%{opacity:0}}
      @media (prefers-reduced-motion:reduce){.role{opacity:0}.role.first{opacity:1}}"""
    return svg(1200, 640, "Kisnner Obando", "Apps nativas para Apple, backend transaccional, ingeniería inversa y open source. Managua, Nicaragua.", body, style, defs)


# ---------------------------------------------------------------- tarjetas
def reveal(cid, x, y, w, h, times, values):
    return (f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="0" height="{h}">'
            f'<animate attributeName="width" values="{values}" keyTimes="{times}" dur="8s" repeatCount="indefinite"/></rect></clipPath>')


def tile_visual(index):
    if index == 0:  # una terminal: primero el 503, tachado; después el 200
        defs = (reveal("l1", 32, 228, 320, 22, "0;.12;.92;1", "0;320;320;0")
                + reveal("l2", 32, 254, 320, 22, "0;.16;.28;.92;1", "0;0;320;320;0")
                + reveal("l3", 32, 280, 320, 22, "0;.36;.46;.92;1", "0;0;320;320;0"))
        body = f"""  <rect x="22" y="216" width="340" height="96" rx="14" fill="{WHITE}" fill-opacity=".04" stroke="{WHITE}" stroke-opacity=".08"/>
  <g clip-path="url(#l1)">{text(36, 244, "$ altserver --sign-in", 13, WHITE, 500, opacity=.75, kind="mono")}</g>
  <g clip-path="url(#l2)">{text(36, 270, "← 503  Service Unavailable", 13, WHITE, 400, opacity=.4, kind="mono")}</g>
  <path d="M36 266h214" stroke="{WHITE}" stroke-opacity=".55" stroke-width="1.5" stroke-dasharray="214"><animate attributeName="stroke-dashoffset" values="214;214;0;0;214" keyTimes="0;.3;.34;.92;1" dur="8s" repeatCount="indefinite"/></path>
  <g clip-path="url(#l3)">{text(36, 296, "← 200  OK · signed in", 13, WHITE, 700, kind="mono")}<rect x="212" y="285" width="8" height="14" fill="{WHITE}" class="caret"/></g>"""
        return defs, body, ".caret{animation:caret 1s steps(1) infinite}\n      @keyframes caret{50%{opacity:0}}"
    if index == 1:  # carriles con trabajos que avanzan, cada uno con su estela
        lanes, jobs = "", ""
        for lane, (y, duration) in enumerate(((240, 2.3), (260, 3.1), (280, 2.0), (300, 3.7))):
            lanes += f'<rect x="56" y="{y}" width="300" height="1.5" rx="1" fill="{WHITE}" fill-opacity=".12"/>'
            for k in range(2):
                jobs += (f'<g class="job" style="animation-duration:{duration}s;animation-delay:-{k * duration / 2:.2f}s">'
                         f'<rect x="28" y="{y - 1.5}" width="34" height="4.5" rx="2.2" fill="url(#tail)"/>'
                         f'<circle cx="62" cy="{y + .7}" r="4.5" fill="{WHITE}"/></g>')
        defs = '<linearGradient id="tail"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff" stop-opacity=".7"/></linearGradient>'
        body = f"""  {lanes}
  <rect x="34" y="230" width="7" height="80" rx="3.5" fill="{WHITE}" class="beat"/>
  {jobs}"""
        style = (".job{animation:job 2.5s linear infinite}\n      @keyframes job{from{transform:translateX(0);opacity:0}10%{opacity:1}88%{opacity:1}to{transform:translateX(286px);opacity:0}}"
                 "\n      .beat{transform-box:fill-box;transform-origin:center;animation:beat 1.2s ease-in-out infinite}\n      @keyframes beat{50%{transform:scaleY(.82)}}")
        return defs, body, style
    # karaoke: cada verso se llena de blanco mientras "suena"
    defs, body = "", ""
    for i, (y, w) in enumerate(((240, 280), (266, 210), (292, 248))):
        start, end = .02 + i * .3, .02 + i * .3 + .26
        defs += (f'<clipPath id="v{i}"><rect x="32" y="{y}" width="0" height="12">'
                 f'<animate attributeName="width" values="0;0;{w};{w};0" keyTimes="0;{start:.2f};{end:.2f};.94;1" dur="8s" repeatCount="indefinite"/></rect></clipPath>')
        body += (f'<rect x="32" y="{y}" width="{w}" height="12" rx="6" fill="{WHITE}" fill-opacity=".14"/>'
                 f'<rect x="32" y="{y}" width="{w}" height="12" rx="6" fill="{WHITE}" clip-path="url(#v{i})"/>')
    return defs, "  " + body, ""


def tile(index, label, headline, sub, meta, downloads):
    if index == 0 and downloads:
        meta = f"{downloads} descargas · PR abierto"
    defs, visual, style = tile_visual(index)
    body = f"""  <rect width="384" height="360" rx="28" fill="{INK}"/>
  <rect width="384" height="360" rx="28" fill="url(#lift)"/>
  <rect x=".5" y=".5" width="383" height="359" rx="27.5" fill="none" stroke="{WHITE}" stroke-opacity=".12"/>
  <g class="in" style="animation-delay:{index * .12}s">
    {text(32, 52, label, 13, WHITE, 600, spacing=2.4, opacity=.5)}
    {text(32, 100, headline[0], 34, WHITE, 700, spacing=-1)}
    {text(32, 138, headline[1], 34, WHITE, 700, spacing=-1)}
    {text(32, 178, sub[0], 15.5, WHITE, 400, opacity=.6)}
    {text(32, 199, sub[1], 15.5, WHITE, 400, opacity=.6)}
  </g>
{visual}
  {text(32, 340, meta, 12.5, WHITE, 400, opacity=.45, kind="mono")}"""
    defs += '<radialGradient id="lift" cx=".2" cy="0" r="1"><stop offset="0" stop-color="#fff" stop-opacity=".07"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
    style = f""".in{{animation:rise .9s cubic-bezier(.2,.8,.2,1) backwards}}
      @keyframes rise{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
      {style}"""
    return svg(384, 360, label.title(), " ".join(headline) + " " + " ".join(sub) + " " + meta, body, style, defs)


MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def odometer(x, y, number, size):
    """cada cifra es una columna 0-9 que rueda hasta su valor; la animación solo define el inicio,
    así que sin movimiento queda directamente en el número correcto."""
    digits, out, cx, step = f"{number:,}", [], x, size * 1.0
    width = size * .6
    for i, ch in enumerate(digits):
        if not ch.isdigit():
            out.append(text(cx, y, ch, size, WHITE, 700))
            cx += size * .3
            continue
        d = int(ch)
        column = "".join(text(cx, y + k * step, k, size, WHITE, 700, extra='style="font-variant-numeric:tabular-nums"') for k in range(10))
        out.append(f'<g clip-path="url(#window)"><g class="roll" style="transform:translateY(-{d * step:.0f}px);animation-delay:{.15 + i * .12:.2f}s">{column}</g></g>')
        cx += width
    return "".join(out), cx


def contributions(d):
    size, y0 = 112, 196
    digits, end_x = odometer(64, y0, d["total"], size)
    # desde junio de 2026, cuando empezaron mis contribuciones reales; antes casi todo es cero
    first = datetime.strptime(d["first"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    skip = max(0, int((datetime(2026, 5, 31, tzinfo=timezone.utc) - first).days // 7))
    weeks = d["weeks"][skip:]
    first = datetime.fromtimestamp(first.timestamp() + skip * 7 * 86400, timezone.utc)
    peak = max(weeks) or 1
    left, right, base, top = 560, 1150, 250, 70
    gap = (right - left) / len(weeks)
    bars = ""
    for i, count in enumerate(weeks):
        h = max(4, (base - top) * (count / peak) ** .5)
        last = i == len(weeks) - 1
        bars += (f'<rect class="grow" x="{left + i * gap:.1f}" y="{base - h:.1f}" width="{gap * .62:.1f}" height="{h:.1f}" rx="{gap * .31:.1f}" '
                 f'fill="{WHITE}" fill-opacity="{1 if last else .38}" style="animation-delay:{.4 + i * .025:.2f}s"/>')
    lx = left + (len(weeks) - 1) * gap + gap * .31
    months = ""
    for i in range(len(weeks)):
        dt = first.timestamp() + i * 7 * 86400
        m = datetime.fromtimestamp(dt, timezone.utc)
        if m.day <= 7 and i % 1 == 0:
            months += text(left + i * gap, base + 26, MESES[m.month - 1], 12, WHITE, 400, opacity=.4, kind="mono")
    stats = f"racha más larga {d['streak']} días   ·   {d['merged']} pull requests mergeados en proyectos ajenos"
    defs = f'<clipPath id="window"><rect x="0" y="{y0 - size * .82:.0f}" width="1200" height="{size * 1.05:.0f}"/></clipPath>'
    body = f"""  <rect width="1200" height="330" rx="28" fill="{INK}"/>
  <rect x=".5" y=".5" width="1199" height="329" rx="27.5" fill="none" stroke="{WHITE}" stroke-opacity=".12"/>
  {text(64, 66, "CONTRIBUCIONES · ÚLTIMO AÑO", 13, WHITE, 600, opacity=.5, spacing=2.4)}
  {digits}
  {text(66, 246, "commits, pull requests, issues y revisiones", 17, WHITE, 400, opacity=.55)}
  {bars}
  <circle cx="{lx:.1f}" cy="{base - max(4, (base - top) * (weeks[-1] / peak) ** .5) - 14:.1f}" r="4" fill="{WHITE}" class="now"/>
  {months}
  <line x1="64" y1="282" x2="1136" y2="282" stroke="{WHITE}" stroke-opacity=".1"/>
  {text(64, 310, stats, 13.5, WHITE, 400, opacity=.6, kind="mono")}"""
    style = """.roll{animation:roll 1.8s cubic-bezier(.16,.84,.24,1) backwards}
      @keyframes roll{from{transform:translateY(0)}}
      .grow{transform-box:fill-box;transform-origin:bottom;animation:grow .9s cubic-bezier(.2,.8,.2,1) backwards}
      @keyframes grow{from{transform:scaleY(0)}}
      .now{animation:now 1.6s ease-in-out infinite}
      @keyframes now{50%{opacity:.2}}"""
    return svg(1200, 330, "Contribuciones", f"{d['total']} contribuciones en el último año. Racha más larga: {d['streak']} días. {d['merged']} pull requests mergeados en proyectos ajenos.", body, style, defs)


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
    write("contributions.svg", contributions(data))
    for label, width, primary in (("Portafolio", 172, True), ("LinkedIn", 150, False), ("GitHub", 140, False), ("Correo", 134, False)):
        write(f"link-{label.lower()}.svg", pill(label, width, primary))
    print("listo:", len(list(ASSETS.glob("*.svg"))), "svg")


if __name__ == "__main__":
    main()
