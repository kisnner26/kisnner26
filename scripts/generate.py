"""genera los svg animados del perfil. solo biblioteca estándar.

estética: Windows XP / Clippy, con el glitch azul de FIBERGLASS (Geometry Dash) de fondo.

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

# paleta Windows XP / Luna
INK = "#0a1d3a"
WHITE = "#ffffff"
XP_TITLE_A, XP_TITLE_B, XP_TITLE_C = "#0a246a", "#3b7ce0", "#0a246a"   # titlebar activa
XP_PANEL = "#ece9d8"                                                   # cuerpo clásico (ventanas de diálogo)
XP_FACE = "#d4d0c8"                                                     # bordes grises 3D
XP_GLITCH_A, XP_GLITCH_B = "#050b2e", "#1452d6"                        # fondo fiberglass
XP_GLITCH_LINE = "#8fb8ff"
CLOSE_A, CLOSE_B = "#f3938a", "#d6341f"
START_A, START_B = "#52c24b", "#1f7a1f"
PAD_YELLOW = "#f6e79c"
FONT = "font-family=\"Tahoma,'Segoe UI','SF Pro Display','Helvetica Neue',Helvetica,Arial,sans-serif\""
MONO = "font-family=\"'SF Mono',Menlo,Consolas,monospace\""

MANAGUA = (12.13, -86.25)
ROLES = ["Parece que estás escribiendo apps nativas para Apple.",
         "Parece que estás armando un backend transaccional.",
         "Parece que estás haciendo ingeniería inversa.",
         "Parece que estás abriendo un pull request open source."]

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


# ---------------------------------------------------------------- cromo de ventana XP
def xp_titlebar(w, title, buttons=True, h=30, grad_id="tbar"):
    btns = ""
    if buttons:
        by = h / 2 - 8
        btns = f"""
    <g transform="translate({w - 80},{by})">
      <rect x="0" y="0" width="18" height="16" rx="2" fill="#2b5bb0" stroke="#dbe9ff" stroke-width="1"/>
      <rect x="6" y="11" width="7" height="2" fill="{WHITE}"/>
      <rect x="24" y="0" width="18" height="16" rx="2" fill="#2b5bb0" stroke="#dbe9ff" stroke-width="1"/>
      <rect x="29" y="3" width="8" height="8" fill="none" stroke="{WHITE}" stroke-width="1.4"/>
      <rect x="48" y="0" width="20" height="16" rx="2" fill="url(#closegrad)" stroke="#8c1a10" stroke-width="1"/>
      <path d="M53 4l10 8m0-8l-10 8" stroke="{WHITE}" stroke-width="1.8" stroke-linecap="round"/>
    </g>"""
    return f"""<rect width="{w}" height="{h}" rx="8" fill="url(#{grad_id})"/>
  <rect y="{h - 8}" width="{w}" height="8" fill="url(#{grad_id})"/>
  <rect x="6" y="{h / 2 - 7:.0f}" width="14" height="14" rx="3" fill="{WHITE}" fill-opacity=".85"/>
  {text(26, h / 2 + 5, title, 13, WHITE, 700, spacing=.2)}{btns}"""


XP_DEFS = f"""    <linearGradient id="tbar" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{XP_TITLE_B}"/><stop offset=".5" stop-color="{XP_TITLE_A}"/><stop offset="1" stop-color="{XP_TITLE_C}"/>
    </linearGradient>
    <linearGradient id="closegrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{CLOSE_A}"/><stop offset="1" stop-color="{CLOSE_B}"/>
    </linearGradient>
    <linearGradient id="startgrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{START_A}"/><stop offset="1" stop-color="{START_B}"/>
    </linearGradient>"""


def xp_window(w, h, title, inner, theme_fill=XP_PANEL, title_h=30):
    return f"""<g>
  <rect width="{w}" height="{h}" rx="9" fill="{theme_fill}" stroke="#0a246a" stroke-width="1.5"/>
  {xp_titlebar(w, title, h=title_h)}
  <g transform="translate(0,{title_h})">{inner}</g>
  </g>"""


# ---------------------------------------------------------------- Clippy
def clippy(cx, cy, scale=1.0, blink_delay=0):
    """un clippy esquemático: libreta amarilla detrás, dos aros de clip plateados, ojos que parpadean."""
    s = scale
    return f"""<g transform="translate({cx},{cy}) scale({s})">
    <g transform="rotate(-5)">
      <rect x="-50" y="-96" width="100" height="150" rx="6" fill="{PAD_YELLOW}" stroke="#c9ad3f" stroke-width="2"/>
      {"".join(f'<line x1="-40" y1="{y}" x2="40" y2="{y}" stroke="#d8c268" stroke-width="1.5"/>' for y in range(-74, 44, 14))}
    </g>
    <g fill="none" stroke-linecap="round">
      <ellipse cx="0" cy="-42" rx="25" ry="34" stroke="#9aa0ae" stroke-width="11"/>
      <ellipse cx="0" cy="-42" rx="25" ry="34" stroke="#d8dbe2" stroke-width="3.5" opacity=".8"/>
      <ellipse cx="0" cy="-2" rx="14" ry="22" stroke="#9aa0ae" stroke-width="10"/>
      <ellipse cx="0" cy="-2" rx="14" ry="22" stroke="#d8dbe2" stroke-width="3" opacity=".8"/>
    </g>
    <g class="eyes">
      <ellipse cx="-10" cy="-48" rx="8" ry="10.5" fill="{WHITE}" stroke="#20242c" stroke-width="2" class="eye" style="animation-delay:{blink_delay}s"/>
      <ellipse cx="11" cy="-48" rx="8" ry="10.5" fill="{WHITE}" stroke="#20242c" stroke-width="2" class="eye" style="animation-delay:{blink_delay + .08}s"/>
      <circle cx="-8" cy="-45" r="3.4" fill="#15171c" class="pupil"/>
      <circle cx="13" cy="-45" r="3.4" fill="#15171c" class="pupil"/>
    </g>
    <g stroke="#15171c" stroke-width="2.4" stroke-linecap="round" class="brows">
      <path d="M-19 -63 q9 -6 17 -1"/>
      <path d="M2 -64 q9 -5 17 1"/>
    </g>
  </g>"""


CLIPPY_STYLE = """.eye{animation:blink 4.6s ease-in-out infinite}
      @keyframes blink{0%,92%,100%{ry:12}95%{ry:1}}
      .pupil{animation:look 7s ease-in-out infinite}
      @keyframes look{0%,100%{transform:translate(0,0)}30%{transform:translate(2px,-1px)}60%{transform:translate(-2px,1px)}}
      .brows{animation:brow 5.4s ease-in-out infinite}
      @keyframes brow{0%,100%{transform:translateY(0)}50%{transform:translateY(-1.5px)}}"""


def speech_bubble(x, y, w, h, lines_html, pointer_x):
    path = (f"M4 0 H{w - 4} Q{w} 0 {w} 4 V{h - 14} Q{w} {h - 10} {w - 4} {h - 10} H{pointer_x + 14} "
            f"L{pointer_x} {h} L{pointer_x - 2} {h - 10} H4 Q0 {h - 10} 0 {h - 14} V4 Q0 0 4 0 Z")
    return f"""<g transform="translate({x},{y})">
    <path d="{path}" fill="{WHITE}" stroke="#20242c" stroke-width="1.6"/>
    {lines_html}
  </g>"""


# ---------------------------------------------------------------- fondo "fiberglass"
def fiberglass_bg(w, h, seed=0):
    """ventanas xp difuminadas flotando sobre un degradado azul, con líneas de escaneo: el look de FIBERGLASS."""
    wins = ""
    for i in range(10):
        rw, rh = 90 + rnd(i + seed, 11) * 160, 50 + rnd(i + seed, 12) * 90
        x, y = rnd(i + seed, 13) * (w - rw), rnd(i + seed, 14) * (h - rh)
        op = .07 + rnd(i + seed, 15) * .1
        rot = (rnd(i + seed, 16) - .5) * 10
        wins += (f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})" opacity="{op:.2f}">'
                 f'<rect width="{rw:.0f}" height="{rh:.0f}" rx="5" fill="none" stroke="{WHITE}" stroke-width="2"/>'
                 f'<rect width="{rw:.0f}" height="14" rx="5" fill="{WHITE}"/></g>')
    scan = "".join(f'<rect y="{y}" width="{w}" height="1" fill="{XP_GLITCH_LINE}" opacity="{.05 + rnd(y, 9) * .1:.2f}"/>' for y in range(0, h, 6))
    return f"""<rect width="{w}" height="{h}" fill="url(#glitchgrad)"/>
  {scan}
  {wins}"""


FIBERGLASS_DEFS = f"""    <linearGradient id="glitchgrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{XP_GLITCH_A}"/><stop offset="1" stop-color="{XP_GLITCH_B}"/>
    </linearGradient>"""


# ---------------------------------------------------------------- hero
def hero():
    role_lines = "".join(
        f'<g class="role{" first" if i == 0 else ""}" style="animation-delay:{i * 3.4}s">{text(0, 20 + k * 19, line, 15.5, "#1b1b1b", 400)}</g>'
        for i, role in enumerate(ROLES) for k, line in enumerate([role])
    )
    bubble = speech_bubble(290, 170, 460, 70, role_lines, 50)
    clip = clippy(165, 400, 1.5)
    taskbar = f"""<rect y="{640 - 40}" width="1200" height="40" fill="url(#tbar)"/>
    <rect x="10" y="{640 - 34}" width="118" height="28" rx="5" fill="url(#startgrad)" stroke="#145314" stroke-width="1"/>
    {text(26, 640 - 15, "inicio", 14, WHITE, 700)}
    {text(1190, 640 - 15, "MANAGUA · 12.13°N 86.25°W", 12.5, WHITE, 500, "end", .85, 1, "mono")}"""
    body = f"""  <g clip-path="url(#card)">
  {fiberglass_bg(1200, 640)}
  <g transform="translate(40,40)">
    {xp_window(1120, 540, "Propiedades de Kisnner Obando.exe", "")}
  </g>
  <g transform="translate(40,70)">
    <rect width="1120" height="510" fill="{XP_PANEL}"/>
    {text(56, 86, "Kisnner Obando.", 58, INK, 700, spacing=-1)}
    {text(56, 122, "apps nativas para Apple · backend transaccional · ingeniería inversa · open source", 15, "#3a3a3a", 500)}
    {clip}
    {bubble}
    {text(56, 470, "kisnner26 · Managua, Nicaragua", 13.5, "#555", 500, opacity=.9, kind="mono")}
  </g>
  {taskbar}
  </g>"""
    defs = XP_DEFS + FIBERGLASS_DEFS + '\n    <clipPath id="card"><rect width="1200" height="640" rx="14"/></clipPath>'
    style = CLIPPY_STYLE + """
      .role{opacity:0;animation:role 13.6s infinite}
      @keyframes role{0%{opacity:0;transform:translateY(10px)}4%{opacity:1;transform:none}22%{opacity:1;transform:none}26%{opacity:0;transform:translateY(-10px)}100%{opacity:0}}
      @media (prefers-reduced-motion:reduce){.role{opacity:0}.role.first{opacity:1}}"""
    return svg(1200, 640, "Kisnner Obando", "Apps nativas para Apple, backend transaccional, ingeniería inversa y open source. Managua, Nicaragua.", body, style, defs)


# ---------------------------------------------------------------- tarjetas
def reveal(cid, x, y, w, h, times, values):
    return (f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="0" height="{h}">'
            f'<animate attributeName="width" values="{values}" keyTimes="{times}" dur="8s" repeatCount="indefinite"/></rect></clipPath>')


def tile_visual(index):
    if index == 0:  # una terminal estilo s.cmd: primero el 503, tachado; después el 200
        defs = (reveal("l1", 0, 16, 320, 22, "0;.12;.92;1", "0;320;320;0")
                + reveal("l2", 0, 42, 320, 22, "0;.16;.28;.92;1", "0;0;320;320;0")
                + reveal("l3", 0, 68, 320, 22, "0;.36;.46;.92;1", "0;0;320;320;0"))
        body = f"""  <g transform="translate(22,186)">
  <rect width="340" height="96" rx="4" fill="#0a0a0a" stroke="{XP_TITLE_A}" stroke-width="1.5"/>
  {xp_titlebar(340, "s.cmd", buttons=False, h=18, grad_id="tbar")}
  <g transform="translate(0,18)">
  <g clip-path="url(#l1)">{text(14, 32, "$ altserver --sign-in", 13, "#6cff6c", 500, kind="mono")}</g>
  <g clip-path="url(#l2)">{text(14, 58, "← 503  Service Unavailable", 13, "#ff6c6c", 400, kind="mono")}</g>
  <path d="M14 54h214" stroke="#ff6c6c" stroke-width="1.5" stroke-dasharray="214"><animate attributeName="stroke-dashoffset" values="214;214;0;0;214" keyTimes="0;.3;.34;.92;1" dur="8s" repeatCount="indefinite"/></path>
  <g clip-path="url(#l3)">{text(14, 84, "← 200  OK · signed in", 13, "#6cff6c", 700, kind="mono")}<rect x="190" y="73" width="8" height="14" fill="#6cff6c" class="caret"/></g>
  </g>
  </g>"""
        return defs, body, ".caret{animation:caret 1s steps(1) infinite}\n      @keyframes caret{50%{opacity:0}}"
    if index == 1:  # carriles con trabajos que avanzan, cada uno con su estela
        lanes, jobs = "", ""
        for lane, (y, duration) in enumerate(((210, 2.3), (230, 3.1), (250, 2.0), (270, 3.7))):
            lanes += f'<rect x="56" y="{y}" width="300" height="2" rx="1" fill="{INK}" fill-opacity=".18"/>'
            for k in range(2):
                jobs += (f'<g class="job" style="animation-duration:{duration}s;animation-delay:-{k * duration / 2:.2f}s">'
                         f'<rect x="28" y="{y - 1.5}" width="34" height="5" rx="2.5" fill="url(#tail)"/>'
                         f'<circle cx="62" cy="{y + .7}" r="5" fill="{XP_TITLE_A}"/></g>')
        defs = f'<linearGradient id="tail"><stop offset="0" stop-color="{XP_TITLE_A}" stop-opacity="0"/><stop offset="1" stop-color="{XP_TITLE_A}" stop-opacity=".7"/></linearGradient>'
        body = f"""  {lanes}
  <rect x="34" y="200" width="7" height="80" rx="3.5" fill="{XP_TITLE_A}" class="beat"/>
  {jobs}"""
        style = (".job{animation:job 2.5s linear infinite}\n      @keyframes job{from{transform:translateX(0);opacity:0}10%{opacity:1}88%{opacity:1}to{transform:translateX(286px);opacity:0}}"
                 "\n      .beat{transform-box:fill-box;transform-origin:center;animation:beat 1.2s ease-in-out infinite}\n      @keyframes beat{50%{transform:scaleY(.82)}}")
        return defs, body, style
    # karaoke: cada verso se llena de azul mientras "suena"
    defs, body = "", ""
    for i, (y, w) in enumerate(((210, 280), (236, 210), (262, 248))):
        start, end = .02 + i * .3, .02 + i * .3 + .26
        defs += (f'<clipPath id="v{i}"><rect x="32" y="{y}" width="0" height="12">'
                 f'<animate attributeName="width" values="0;0;{w};{w};0" keyTimes="0;{start:.2f};{end:.2f};.94;1" dur="8s" repeatCount="indefinite"/></rect></clipPath>')
        body += (f'<rect x="32" y="{y}" width="{w}" height="12" rx="6" fill="{INK}" fill-opacity=".14"/>'
                 f'<rect x="32" y="{y}" width="{w}" height="12" rx="6" fill="{XP_TITLE_A}" clip-path="url(#v{i})"/>')
    return defs, "  " + body, ""


def tile(index, label, headline, sub, meta, downloads):
    if index == 0 and downloads:
        meta = f"{downloads} descargas · PR abierto"
    defs, visual, style = tile_visual(index)
    inner = f"""  <rect width="384" height="326" fill="{XP_PANEL}"/>
  <g class="in" style="animation-delay:{index * .12}s">
    {text(32, 42, label, 12.5, "#5a5a5a", 700, spacing=2)}
    {text(32, 86, headline[0], 30, INK, 700, spacing=-.6)}
    {text(32, 120, headline[1], 30, INK, 700, spacing=-.6)}
    {text(32, 154, sub[0], 14.5, "#3a3a3a", 400)}
    {text(32, 174, sub[1], 14.5, "#3a3a3a", 400)}
  </g>
{visual}
  {text(32, 308, meta, 12, "#555", 500, kind="mono")}"""
    full_defs = defs + XP_DEFS
    body = xp_window(384, 356, label.title(), inner)
    style = f""".in{{animation:rise .9s cubic-bezier(.2,.8,.2,1) backwards}}
      @keyframes rise{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
      {style}"""
    return svg(384, 356, label.title(), " ".join(headline) + " " + " ".join(sub) + " " + meta, body, style, full_defs)


MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def odometer(x, y, number, size, fill=INK):
    digits, out, cx, step = f"{number:,}", [], x, size * 1.0
    width = size * .6
    for i, ch in enumerate(digits):
        if not ch.isdigit():
            out.append(text(cx, y, ch, size, fill, 700))
            cx += size * .3
            continue
        d = int(ch)
        column = "".join(text(cx, y + k * step, k, size, fill, 700, extra='style="font-variant-numeric:tabular-nums"') for k in range(10))
        out.append(f'<g clip-path="url(#window)"><g class="roll" style="transform:translateY(-{d * step:.0f}px);animation-delay:{.15 + i * .12:.2f}s">{column}</g></g>')
        cx += width
    return "".join(out), cx


def contributions(d):
    size, y0 = 100, 170
    digits, end_x = odometer(64, y0, d["total"], size, fill="#6cff6c")
    # desde junio de 2026, cuando empezaron mis contribuciones reales; antes casi todo es cero
    first = datetime.strptime(d["first"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    skip = max(0, int((datetime(2026, 5, 31, tzinfo=timezone.utc) - first).days // 7))
    weeks = d["weeks"][skip:]
    first = datetime.fromtimestamp(first.timestamp() + skip * 7 * 86400, timezone.utc)
    peak = max(weeks) or 1
    left, right, base, top = 560, 1150, 232, 60
    gap = (right - left) / len(weeks)
    bars = ""
    for i, count in enumerate(weeks):
        h = max(4, (base - top) * (count / peak) ** .5)
        last = i == len(weeks) - 1
        bars += (f'<rect class="grow" x="{left + i * gap:.1f}" y="{base - h:.1f}" width="{gap * .62:.1f}" height="{h:.1f}" rx="{gap * .18:.1f}" '
                 f'fill="#6cff6c" fill-opacity="{1 if last else .4}" style="animation-delay:{.4 + i * .025:.2f}s"/>')
    lx = left + (len(weeks) - 1) * gap + gap * .31
    months = ""
    for i in range(len(weeks)):
        dt = first.timestamp() + i * 7 * 86400
        m = datetime.fromtimestamp(dt, timezone.utc)
        if m.day <= 7:
            months += text(left + i * gap, base + 24, MESES[m.month - 1], 11, "#8fb8ff", 400, kind="mono")
    stats = f"racha más larga {d['streak']} días   ·   {d['merged']} pull requests mergeados en proyectos ajenos"
    defs = f'<clipPath id="window"><rect x="0" y="{y0 - size * .82:.0f}" width="1200" height="{size * 1.05:.0f}"/></clipPath>' + XP_DEFS
    inner = f"""  <rect width="1200" height="300" fill="#05070d"/>
  {text(64, 48, "CONTRIBUCIONES · ÚLTIMO AÑO", 12.5, "#8fb8ff", 700, spacing=2.2, kind="mono")}
  {digits}
  {text(66, 220, "commits, pull requests, issues y revisiones", 15.5, "#cfe3ff", 400)}
  {bars}
  <circle cx="{lx:.1f}" cy="{base - max(4, (base - top) * (weeks[-1] / peak) ** .5) - 12:.1f}" r="4" fill="#6cff6c" class="now"/>
  {months}
  <line x1="64" y1="256" x2="1136" y2="256" stroke="{WHITE}" stroke-opacity=".12"/>
  {text(64, 282, stats, 13, "#8fb8ff", 500, kind="mono")}"""
    body = xp_window(1200, 330, "contribuciones.exe", inner)
    style = """.roll{animation:roll 1.8s cubic-bezier(.16,.84,.24,1) backwards}
      @keyframes roll{from{transform:translateY(0)}}
      .grow{transform-box:fill-box;transform-origin:bottom;animation:grow .9s cubic-bezier(.2,.8,.2,1) backwards}
      @keyframes grow{from{transform:scaleY(0)}}
      .now{animation:now 1.6s ease-in-out infinite}
      @keyframes now{50%{opacity:.2}}"""
    return svg(1200, 330, "Contribuciones", f"{d['total']} contribuciones en el último año. Racha más larga: {d['streak']} días. {d['merged']} pull requests mergeados en proyectos ajenos.", body, style, defs)


def pill(label, width, primary):
    h = 46
    fill = "url(#startgrad)" if primary else "#ece9d8"
    stroke = "#145314" if primary else XP_TITLE_A
    ink = WHITE if primary else INK
    body = f"""  <rect x="1" y="1" width="{width - 2}" height="{h}" rx="7" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>
  <rect x="3" y="3" width="{width - 6}" height="{h / 2 - 2:.0f}" rx="5" fill="{WHITE}" fill-opacity=".25"/>
  {text(width / 2 - 8, h / 2 + 6, label, 16, ink, 700, "middle")}
  <path class="go" d="M{width - 36} {h / 2 - 1:.0f}h11m-5-5 5 5-5 5" fill="none" stroke="{ink}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>"""
    defs = XP_DEFS
    style = ".go{animation:go 2.2s ease-in-out infinite}\n      @keyframes go{50%{transform:translateX(3px)}}"
    return svg(width, h + 2, label, f"enlace: {label}", body, style, defs)


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
