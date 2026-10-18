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

# frutiger aero: cielo, vidrio, burbujas y verde lima
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
                   f'fill="none" stroke="{WHITE}" stroke-opacity="{.55 if lat == 0 else .3}" stroke-width="1"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{WHITE}" stroke-opacity="0" stroke-width="1.2"/>')

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


# ---------------------------------------------------------------- frutiger aero
DEEP, MID, LIME = "#064a73", "#2b7ea6", "#b8ff6a"
AERO = "font-family=\"Frutiger,'Segoe UI','SF Pro Rounded','Helvetica Neue',Arial,sans-serif\""

STYLE = """.bub{animation:float 12s ease-in-out infinite alternate}
      @keyframes float{from{transform:translateY(0)}to{transform:translateY(-26px)}}
      .sheen{animation:sheen 9s cubic-bezier(.4,0,.2,1) infinite}
      @keyframes sheen{0%{transform:translateX(0)}38%,100%{transform:translateX(1500px)}}
      @media (prefers-reduced-motion:reduce){*{animation:none!important}}"""

COMMON = f"""    <linearGradient id="ink" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0b78b8"/><stop offset="1" stop-color="{DEEP}"/></linearGradient>
    <filter id="emboss" x="-5%" y="-10%" width="110%" height="130%"><feDropShadow dx="0" dy="1.5" stdDeviation="0" flood-color="#ffffff" flood-opacity=".9"/></filter>
    <radialGradient id="bub" cx=".35" cy=".3" r=".75"><stop offset="0" stop-color="#fff" stop-opacity=".9"/><stop offset=".3" stop-color="#fff" stop-opacity=".18"/><stop offset="1" stop-color="#fff" stop-opacity=".02"/></radialGradient>
    <linearGradient id="sheen"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".5"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>"""


def svg(width, height, title, desc, body, extra_style="", defs=""):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="t d">
  <title id="t">{escape(title)}</title>
  <desc id="d">{escape(desc)}</desc>
  <defs>
{COMMON}
{defs}
    <style>
      {extra_style}
      {STYLE}
    </style>
  </defs>
{body}
</svg>
"""


def text(x, y, s, size, fill=DEEP, weight=400, anchor="start", opacity=1, spacing=0, kind="sans", extra=""):
    family = AERO if kind == "sans" else MONO
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    op = f' opacity="{opacity}"' if opacity != 1 else ""
    return f'<text x="{x}" y="{y}" {family} font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{ls}{op} {extra}>{escape(str(s))}</text>'


def emboss(*args, **kwargs):
    return text(*args, extra='filter="url(#emboss)"', **kwargs)


def sky(w, h, rx, top, mid, bottom, sun):
    """cielo con degradado, resplandor de sol y borde redondeado. devuelve (defs, apertura del grupo recortado)."""
    defs = (f'<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/><stop offset=".55" stop-color="{mid}"/><stop offset="1" stop-color="{bottom}"/></linearGradient>'
            f'<radialGradient id="sun" cx="{sun[0]}" cy="{sun[1]}" r="{sun[2]}" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#fff" stop-opacity=".95"/><stop offset=".25" stop-color="#fff" stop-opacity=".45"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
            f'<clipPath id="card"><rect width="{w}" height="{h}" rx="{rx}"/></clipPath>')
    opening = (f'<g clip-path="url(#card)"><rect width="{w}" height="{h}" fill="url(#sky)"/><rect width="{w}" height="{h}" fill="url(#sun)" class="breathe"/>')
    return defs, opening


def rim(w, h, rx):
    return f'<rect x=".75" y=".75" width="{w - 1.5}" height="{h - 1.5}" rx="{rx - .75}" fill="none" stroke="#fff" stroke-opacity=".9" stroke-width="1.5"/>'


def bubbles(w, h, n, salt, lo=9, hi=44, area=None):
    x0, y0, x1, y1 = area or (20, 20, w - 20, h - 20)
    out = []
    for i in range(n):
        r = lo + (hi - lo) * rnd(i, salt) ** 2
        x, y = x0 + rnd(i, salt + 1) * (x1 - x0), y0 + rnd(i, salt + 2) * (y1 - y0)
        dur = 9 + rnd(i, salt + 3) * 10
        out.append(f'<g class="bub" style="animation-duration:{dur:.1f}s;animation-delay:-{rnd(i, salt + 4) * dur:.1f}s">'
                   f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.0f}" fill="url(#bub)" stroke="#fff" stroke-opacity=".6" stroke-width="1.2"/>'
                   f'<ellipse cx="{x - r * .3:.0f}" cy="{y - r * .45:.0f}" rx="{r * .35:.0f}" ry="{r * .18:.0f}" fill="#fff" fill-opacity=".75"/></g>')
    return "".join(out)


def glass(uid, x, y, w, h, r, alpha=.26, tint="#ffffff"):
    """un panel de vidrio: relleno translúcido, brillo curvo arriba, destello que cruza y doble borde.
    devuelve (defs, cuerpo)."""
    defs = (f'<linearGradient id="g{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{tint}" stop-opacity="{alpha + .14:.2f}"/><stop offset="1" stop-color="{tint}" stop-opacity="{alpha - .08:.2f}"/></linearGradient>'
            f'<linearGradient id="h{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".72"/><stop offset="1" stop-color="#fff" stop-opacity=".05"/></linearGradient>'
            f'<clipPath id="c{uid}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}"/></clipPath>'
            f'<filter id="d{uid}" x="-10%" y="-10%" width="120%" height="135%"><feOffset in="SourceAlpha" dy="8" result="o"/><feGaussianBlur in="o" stdDeviation="10" result="b"/>'
            f'<feComposite in="b" in2="SourceAlpha" operator="out" result="s"/><feFlood flood-color="#04507f" flood-opacity=".3"/><feComposite in2="s" operator="in" result="sh"/>'
            f'<feMerge><feMergeNode in="sh"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    body = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="url(#g{uid})" filter="url(#d{uid})"/>'
            f'<g clip-path="url(#c{uid})"><ellipse cx="{x + w / 2}" cy="{y - h * .2:.0f}" rx="{w * .8:.0f}" ry="{h * .62:.0f}" fill="url(#h{uid})"/>'
            f'<g class="sheen"><rect x="{x - w * .35:.0f}" y="{y - 20}" width="{w * .16:.0f}" height="{h + 40}" fill="url(#sheen)" transform="skewX(-20)"/></g></g>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="none" stroke="#fff" stroke-opacity=".95" stroke-width="1.6"/>'
            f'<rect x="{x + 3}" y="{y + 3}" width="{w - 6}" height="{h - 6}" rx="{r - 3}" fill="none" stroke="#fff" stroke-opacity=".35"/>')
    return defs, body


HILLS = """<linearGradient id="hill1" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b6f06a"/><stop offset="1" stop-color="#2f9f45"/></linearGradient>
    <linearGradient id="hill2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8fe08a"/><stop offset="1" stop-color="#1f8a5a"/></linearGradient>"""


def hero():
    gdefs, gbody = glass("p", 56, 64, 690, 424, 40)
    orb = dict(cx=960, cy=290, r=178)
    cx, cy, r = orb["cx"], orb["cy"], orb["r"]
    defs = HILLS + f"""
    <radialGradient id="orb" cx=".5" cy=".82" r=".85"><stop offset="0" stop-color="#8fe9ff"/><stop offset=".5" stop-color="#2ba9ee"/><stop offset="1" stop-color="#0a5fa5"/></radialGradient>
    <linearGradient id="spec" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".9"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
    <radialGradient id="under" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{LIME}" stop-opacity=".75"/><stop offset="1" stop-color="{LIME}" stop-opacity="0"/></radialGradient>
    <radialGradient id="shade" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#05502a" stop-opacity=".35"/><stop offset="1" stop-color="#05502a" stop-opacity="0"/></radialGradient>
    <clipPath id="orbclip"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>
    <clipPath id="wipe"><rect x="0" y="100" width="0" height="260"><animate attributeName="width" from="0" to="740" dur="1.4s" begin=".2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".25 .8 .25 1"/></rect></clipPath>"""
    sdefs, opening = sky(1200, 600, 36, "#27a4ee", "#8bdcff", "#e4fbff", (1060, 40, 520))
    rays = "".join(f'<polygon points="1060,40 {x},600 {x + 90},600" fill="#fff" fill-opacity=".07"/>' for x in (300, 560, 820, 1000))
    roles = "".join(f'<g class="role{" first" if i == 0 else ""}" style="animation-delay:{i * 3.2}s">'
                    f'{emboss(92, 424, role, 30, MID, 500, spacing=-.3)}</g>' for i, role in enumerate(ROLES))
    body = f"""  {opening}
  {rays}
  {bubbles(1200, 600, 16, 11, 8, 40, (30, 40, 1170, 470))}
  <path d="M0 505 C200 450 400 455 580 495 S980 540 1200 470 V600 H0Z" fill="url(#hill2)"/>
  <path d="M0 505 C200 450 400 455 580 495 S980 540 1200 470" fill="none" stroke="#fff" stroke-opacity=".55" stroke-width="1.5"/>
  <path d="M0 555 C260 510 520 535 760 555 S1060 580 1200 535 V600 H0Z" fill="url(#hill1)"/>
  <path d="M0 555 C260 510 520 535 760 555 S1060 580 1200 535" fill="none" stroke="#fff" stroke-opacity=".7" stroke-width="1.5"/>
  <ellipse cx="{cx}" cy="{cy + r + 24}" rx="{r * .85:.0f}" ry="16" fill="url(#shade)"/>
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#orb)"/>
  <ellipse cx="{cx}" cy="{cy + r * .74:.0f}" rx="{r * .62:.0f}" ry="{r * .2:.0f}" fill="url(#under)" clip-path="url(#orbclip)"/>
  <g clip-path="url(#orbclip)">{globe(cx, cy, r - 10, points=300, frames=30)}</g>
  <ellipse cx="{cx - r * .12:.0f}" cy="{cy - r * .6:.0f}" rx="{r * .55:.0f}" ry="{r * .22:.0f}" fill="url(#spec)" opacity=".6"/>
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#fff" stroke-opacity=".85" stroke-width="2"/>
  {gbody}
  {text(92, 118, "MANAGUA, NICARAGUA · 12.13°N 86.25°W", 14, MID, 500, spacing=2.2, kind="mono")}
  <g clip-path="url(#wipe)">
    {emboss(88, 236, "Kisnner", 118, "url(#ink)", 600, spacing=-4)}
    {emboss(88, 344, "Obando.", 118, "url(#ink)", 600, spacing=-4)}
  </g>
  {roles}
  {text(92, 462, "kisnner26", 14, MID, 500, spacing=2, kind="mono", opacity=.75)}
  </g>
  {rim(1200, 600, 36)}"""
    style = """.breathe{animation:breathe 7s ease-in-out infinite alternate}
      @keyframes breathe{from{opacity:.65}to{opacity:1}}
      .role{opacity:0;animation:role 12.8s infinite}
      @keyframes role{0%{opacity:0;transform:translateY(14px)}4%{opacity:1;transform:none}22%{opacity:1;transform:none}26%{opacity:0;transform:translateY(-14px)}100%{opacity:0}}
      @media (prefers-reduced-motion:reduce){.role{opacity:0}.role.first{opacity:1}}"""
    return svg(1200, 600, "Kisnner Obando", "Apps nativas para Apple, backend transaccional, ingeniería inversa y open source. Managua, Nicaragua.",
               body, style, sdefs + gdefs + defs)


# ---------------------------------------------------------------- tarjetas
PALETTES = [("#27a4ee", "#8bdcff", "#e4fbff"), ("#16b4c4", "#7fe6d8", "#e4fff2"), ("#4a7ff0", "#a3c3ff", "#eaf2ff")]


def reveal(cid, x, y, w, h, times, values):
    return (f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="0" height="{h}">'
            f'<animate attributeName="width" values="{values}" keyTimes="{times}" dur="8s" repeatCount="indefinite"/></rect></clipPath>')


ORB_DEFS = ('<radialGradient id="jorb" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#f4ffe0"/><stop offset=".45" stop-color="#7fdc45"/><stop offset="1" stop-color="#2a8f2a"/></radialGradient>'
            '<linearGradient id="cyl" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#1479c8"/><stop offset=".35" stop-color="#8fe0ff"/><stop offset="1" stop-color="#1479c8"/></linearGradient>'
            '<linearGradient id="fill" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#4cc8ff"/><stop offset="1" stop-color="#8be34f"/></linearGradient>')


def tile_visual(index):
    if index == 0:  # una terminal de vidrio oscuro: primero el 503, tachado; después el 200
        defs = (reveal("l1", 34, 222, 316, 22, "0;.12;.92;1", "0;316;316;0")
                + reveal("l2", 34, 248, 316, 22, "0;.16;.28;.92;1", "0;0;316;316;0")
                + reveal("l3", 34, 274, 316, 22, "0;.36;.46;.92;1", "0;0;316;316;0"))
        body = f"""  <rect x="34" y="212" width="316" height="96" rx="14" fill="#06324f" fill-opacity=".66" stroke="#fff" stroke-opacity=".55"/>
  <rect x="35" y="213" width="314" height="30" rx="13" fill="#fff" fill-opacity=".1"/>
  <g clip-path="url(#l1)">{text(50, 240, "$ altserver --sign-in", 13, "#fff", 500, opacity=.9, kind="mono")}</g>
  <g clip-path="url(#l2)">{text(50, 266, "← 503  Service Unavailable", 13, "#bfe6ff", 400, opacity=.65, kind="mono")}</g>
  <path d="M50 262h214" stroke="#bfe6ff" stroke-opacity=".8" stroke-width="1.5" stroke-dasharray="214"><animate attributeName="stroke-dashoffset" values="214;214;0;0;214" keyTimes="0;.3;.34;.92;1" dur="8s" repeatCount="indefinite"/></path>
  <g clip-path="url(#l3)">{text(50, 292, "← 200  OK · signed in", 13, LIME, 700, kind="mono")}<rect x="226" y="281" width="8" height="14" fill="{LIME}" class="caret"/></g>"""
        return defs, body, ".caret{animation:caret 1s steps(1) infinite}\n      @keyframes caret{50%{opacity:0}}"
    if index == 1:  # tubos de vidrio con trabajos que avanzan como burbujas verdes
        lanes, jobs = "", ""
        for y, duration in ((228, 2.3), (250, 3.1), (272, 2.0), (294, 3.7)):
            lanes += f'<rect x="50" y="{y - 7}" width="300" height="14" rx="7" fill="#fff" fill-opacity=".34" stroke="#fff" stroke-opacity=".85"/><rect x="56" y="{y - 5}" width="288" height="4" rx="2" fill="#fff" fill-opacity=".55"/>'
            for k in range(2):
                jobs += (f'<g class="job" style="animation-duration:{duration}s;animation-delay:-{k * duration / 2:.2f}s">'
                         f'<circle cx="62" cy="{y}" r="6" fill="url(#jorb)"/><ellipse cx="60" cy="{y - 2.5}" rx="2.4" ry="1.4" fill="#fff" fill-opacity=".9"/></g>')
        body = f"""  <rect x="32" y="216" width="18" height="90" rx="9" fill="url(#cyl)" stroke="#fff" stroke-opacity=".85" class="beat"/>
  {lanes}
  {jobs}"""
        style = (".job{animation:job 2.5s linear infinite}\n      @keyframes job{from{transform:translateX(0);opacity:0}10%{opacity:1}88%{opacity:1}to{transform:translateX(276px);opacity:0}}"
                 "\n      .beat{transform-box:fill-box;transform-origin:center;animation:beat 1.2s ease-in-out infinite}\n      @keyframes beat{50%{transform:scaleY(.9)}}")
        return ORB_DEFS, body, style
    # karaoke: cada verso se llena como una barra de vidrio mientras "suena"
    defs, body = ORB_DEFS, ""
    for i, (y, w) in enumerate(((222, 300), (252, 224), (282, 262))):
        start, end = .02 + i * .3, .02 + i * .3 + .26
        defs += (f'<clipPath id="v{i}"><rect x="34" y="{y}" width="0" height="18">'
                 f'<animate attributeName="width" values="0;0;{w};{w};0" keyTimes="0;{start:.2f};{end:.2f};.94;1" dur="8s" repeatCount="indefinite"/></rect></clipPath>')
        body += (f'<rect x="34" y="{y}" width="{w}" height="18" rx="9" fill="#fff" fill-opacity=".38" stroke="#fff" stroke-opacity=".85"/>'
                 f'<g clip-path="url(#v{i})"><rect x="34" y="{y}" width="{w}" height="18" rx="9" fill="url(#fill)"/>'
                 f'<rect x="38" y="{y + 2}" width="{w - 8}" height="6" rx="3" fill="#fff" fill-opacity=".5"/></g>')
    return defs, "  " + body, ""


def tile(index, label, headline, sub, meta, downloads):
    if index == 0 and downloads:
        meta = f"{downloads} descargas · PR abierto"
    vdefs, visual, style = tile_visual(index)
    sdefs, opening = sky(384, 360, 28, *PALETTES[index], (index * 150 + 60, -10, 360))
    gdefs, gbody = glass("t", 14, 14, 356, 332, 22)
    body = f"""  {opening}
  {bubbles(384, 360, 7, 20 + index * 7, 8, 30)}
  {gbody}
  <g class="in" style="animation-delay:{index * .12}s">
    {text(36, 54, label, 13, MID, 600, spacing=2.4)}
    {emboss(36, 100, headline[0], 33, "url(#ink)", 600, spacing=-.8)}
    {emboss(36, 136, headline[1], 33, "url(#ink)", 600, spacing=-.8)}
    {text(36, 170, sub[0], 15, MID, 400)}
    {text(36, 190, sub[1], 15, MID, 400)}
  </g>
{visual}
  {text(36, 332, meta, 12.5, MID, 400, kind="mono", opacity=.85)}
  </g>
  {rim(384, 360, 28)}"""
    style = f""".in{{animation:rise .9s cubic-bezier(.2,.8,.2,1) backwards}}
      @keyframes rise{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
      .breathe{{animation:breathe 7s ease-in-out infinite alternate}}
      @keyframes breathe{{from{{opacity:.65}}to{{opacity:1}}}}
      {style}"""
    return svg(384, 360, label.title(), " ".join(headline) + " " + " ".join(sub) + " " + meta, body, style, sdefs + gdefs + vdefs)


MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def odometer(x, y, number, size):
    """cada cifra es una columna 0-9 que rueda hasta su valor; la animación solo define el inicio,
    así que sin movimiento queda directamente en el número correcto."""
    digits, out, cx, step = f"{number:,}", [], x, size * 1.0
    width = size * .6
    for i, ch in enumerate(digits):
        if not ch.isdigit():
            out.append(text(cx, y, ch, size, "url(#ink)", 600))
            cx += size * .3
            continue
        d = int(ch)
        column = "".join(text(cx, y + k * step, k, size, "url(#ink)", 600, extra='style="font-variant-numeric:tabular-nums"') for k in range(10))
        out.append(f'<g clip-path="url(#window)"><g class="roll" style="transform:translateY(-{d * step:.0f}px);animation-delay:{.15 + i * .12:.2f}s">{column}</g></g>')
        cx += width
    return "".join(out), cx


def contributions(d):
    size, y0 = 108, 192
    digits, end_x = odometer(64, y0, d["total"], size)
    # desde junio de 2026, cuando empezaron mis contribuciones reales; antes casi todo es cero
    first = datetime.strptime(d["first"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    skip = max(0, int((datetime(2026, 5, 31, tzinfo=timezone.utc) - first).days // 7))
    weeks = d["weeks"][skip:]
    first = datetime.fromtimestamp(first.timestamp() + skip * 7 * 86400, timezone.utc)
    peak = max(weeks) or 1
    left, right, base, top = 560, 1150, 246, 66
    gap = (right - left) / len(weeks)
    bars = ""
    for i, count in enumerate(weeks):
        h = max(5, (base - top) * (count / peak) ** .5)
        last = i == len(weeks) - 1
        bars += (f'<rect class="grow" x="{left + i * gap:.1f}" y="{base - h:.1f}" width="{gap * .62:.1f}" height="{h:.1f}" rx="{gap * .31:.1f}" '
                 f'fill="url(#{"barnow" if last else "bar"})" stroke="#fff" stroke-opacity=".9" stroke-width="1" style="animation-delay:{.4 + i * .025:.2f}s"/>')
    lx = left + (len(weeks) - 1) * gap + gap * .31
    months = ""
    for i in range(len(weeks)):
        m = datetime.fromtimestamp(first.timestamp() + i * 7 * 86400, timezone.utc)
        if m.day <= 7:
            months += text(left + i * gap, base + 22, MESES[m.month - 1], 12, MID, 400, opacity=.8, kind="mono")
    stats = f"racha más larga {d['streak']} días   ·   {d['merged']} pull requests mergeados en proyectos ajenos"
    sdefs, opening = sky(1200, 330, 32, "#27a4ee", "#8bdcff", "#e4fbff", (1090, 0, 520))
    gdefs, gbody = glass("c", 14, 12, 1172, 306, 26)
    defs = (f'<clipPath id="window"><rect x="0" y="{y0 - size * .82:.0f}" width="1200" height="{size * 1.05:.0f}"/></clipPath>'
            '<linearGradient id="bar" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#d6f6ff"/><stop offset=".4" stop-color="#5cc8ff"/><stop offset="1" stop-color="#1b8fd9"/></linearGradient>'
            '<linearGradient id="barnow" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#eaffc9"/><stop offset=".4" stop-color="#9be85a"/><stop offset="1" stop-color="#3aa83a"/></linearGradient>')
    body = f"""  {opening}
  {bubbles(1200, 330, 9, 41, 8, 30)}
  {gbody}
  {text(64, 62, "CONTRIBUCIONES · ÚLTIMO AÑO", 13, MID, 600, spacing=2.4)}
  {digits}
  {text(66, 238, "commits, pull requests, issues y revisiones", 17, MID, 400)}
  {bars}
  <circle cx="{lx:.1f}" cy="{base - max(5, (base - top) * (weeks[-1] / peak) ** .5) - 14:.1f}" r="4.5" fill="{LIME}" stroke="#fff" class="now"/>
  {months}
  <line x1="64" y1="272" x2="1136" y2="272" stroke="#fff" stroke-opacity=".7"/>
  {text(64, 298, stats, 13.5, DEEP, 400, kind="mono", opacity=.8)}
  </g>
  {rim(1200, 330, 32)}"""
    style = """.roll{animation:roll 1.8s cubic-bezier(.16,.84,.24,1) backwards}
      @keyframes roll{from{transform:translateY(0)}}
      .grow{transform-box:fill-box;transform-origin:bottom;animation:grow .9s cubic-bezier(.2,.8,.2,1) backwards}
      @keyframes grow{from{transform:scaleY(0)}}
      .now{animation:now 1.6s ease-in-out infinite}
      @keyframes now{50%{opacity:.3}}
      .breathe{animation:breathe 7s ease-in-out infinite alternate}
      @keyframes breathe{from{opacity:.65}to{opacity:1}}"""
    return svg(1200, 330, "Contribuciones", f"{d['total']} contribuciones en el último año. Racha más larga: {d['streak']} días. {d['merged']} pull requests mergeados en proyectos ajenos.",
               body, style, sdefs + gdefs + defs)


def pill(label, width, primary):
    top, bottom, edge = ("#aef26b", "#2c9d3a", "#1f7a2e") if primary else ("#6fd4ff", "#1479c8", "#0b5f94")
    defs = (f'<linearGradient id="b" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/><stop offset=".5" stop-color="{bottom}"/><stop offset="1" stop-color="{bottom}"/></linearGradient>'
            '<linearGradient id="hl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".8"/><stop offset="1" stop-color="#fff" stop-opacity=".12"/></linearGradient>'
            '<filter id="ts" x="-5%" y="-10%" width="110%" height="140%"><feDropShadow dx="0" dy="1" stdDeviation=".6" flood-color="#04283f" flood-opacity=".6"/></filter>')
    body = f"""  <rect x="1" y="1" width="{width - 2}" height="46" rx="23" fill="url(#b)" stroke="{edge}" stroke-width="1.5"/>
  <rect x="5" y="4" width="{width - 10}" height="21" rx="10.5" fill="url(#hl)"/>
  <rect x="2.5" y="2.5" width="{width - 5}" height="43" rx="21.5" fill="none" stroke="#fff" stroke-opacity=".55"/>
  {text(width / 2 - 8, 30, label, 17, "#fff", 600, "middle", extra='filter="url(#ts)"')}
  <path class="go" d="M{width - 36} 24h11m-5-5 5 5-5 5" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" filter="url(#ts)"/>"""
    style = ".go{animation:go 2.2s ease-in-out infinite}\n      @keyframes go{50%{transform:translateX(3px)}}"
    return svg(width, 48, label, f"enlace: {label}", body, style, defs)


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
