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

# contribuciones más destacadas: PRs mergeados en proyectos ajenos de peso
# (repo, titular, subtítulo, meta, url)
TILES = [
    ("nodejs/node", ["Corrige tipos", "de QuicStream."], ["Documentación del core de Node.js,", "el runtime más usado del mundo."],
     "PR #66687 mergeado · oct 2026", "https://github.com/nodejs/node/pull/66687"),
    ("radareorg/radare2", ["Arregla referencias", "de memoria anidadas."], ["El framework de ingeniería inversa", "más usado por la comunidad RE."],
     "PR #26920 mergeado · oct 2026", "https://github.com/radareorg/radare2/pull/26920"),
    ("geode-sdk/bindings", ["6 direcciones de", "Windows corregidas."], ["El SDK de mods de Geometry Dash,", "usado por miles de creadores."],
     "PR #1396 mergeado · oct 2026", "https://github.com/geode-sdk/bindings/pull/1396"),
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
    """clippy: libreta amarilla detrás, dos aros de alambre anidados (como el clip real) y una
    carita que asoma por el hueco de arriba, ojos que parpadean y miran."""
    s = scale
    return f"""<g transform="translate({cx},{cy}) scale({s})">
    <g transform="rotate(-4)">
      <rect x="-54" y="-156" width="108" height="168" rx="6" fill="{PAD_YELLOW}" stroke="#c9ad3f" stroke-width="2"/>
      {"".join(f'<line x1="-44" y1="{y}" x2="44" y2="{y}" stroke="#d8c268" stroke-width="1.5"/>' for y in range(-134, 2, 14))}
    </g>
    <g fill="none" stroke-linecap="round">
      <rect x="-46" y="-140" width="52" height="134" rx="26" stroke="#7d828e" stroke-width="10"/>
      <rect x="-46" y="-140" width="52" height="134" rx="26" stroke="#dfe2e8" stroke-width="3" opacity=".7"/>
      <rect x="-20" y="-118" width="34" height="140" rx="17" stroke="#7d828e" stroke-width="9"/>
      <rect x="-20" y="-118" width="34" height="140" rx="17" stroke="#dfe2e8" stroke-width="3" opacity=".7"/>
    </g>
    <g class="eyes">
      <ellipse cx="-19" cy="-116" rx="9.5" ry="12" fill="{WHITE}" stroke="#20242c" stroke-width="2.2" class="eye" style="animation-delay:{blink_delay}s"/>
      <ellipse cx="4" cy="-118" rx="9.5" ry="12" fill="{WHITE}" stroke="#20242c" stroke-width="2.2" class="eye" style="animation-delay:{blink_delay + .08}s"/>
      <circle cx="-16" cy="-113" r="3.8" fill="#15171c" class="pupil"/>
      <circle cx="7" cy="-115" r="3.8" fill="#15171c" class="pupil"/>
      <circle cx="-18.5" cy="-116.5" r="1.2" fill="{WHITE}"/>
      <circle cx="5.5" cy="-118.5" r="1.2" fill="{WHITE}"/>
    </g>
    <g stroke="#15171c" stroke-width="2.8" stroke-linecap="round" class="brows">
      <path d="M-30 -134 q11 -8 21 -3"/>
      <path d="M-6 -138 q11 -6 21 1"/>
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
    tagline = text(0, 22, "Parece que estás viendo el perfil de Kisnner.", 16.5, "#1b1b1b", 500)
    bubble = speech_bubble(372, 150, 420, 56, tagline, 44)
    clip = clippy(150, 330, 1.18)
    taskbar = f"""<rect y="{440 - 36}" width="1200" height="36" fill="url(#tbar)"/>
    <rect x="10" y="{440 - 31}" width="104" height="26" rx="5" fill="url(#startgrad)" stroke="#145314" stroke-width="1"/>
    {text(24, 440 - 13, "inicio", 13.5, WHITE, 700)}
    {text(1190, 440 - 13, "kisnner26.github.io", 13, WHITE, 700, "end", 1, .4, "mono")}"""
    body = f"""  <g clip-path="url(#card)">
  {fiberglass_bg(1200, 440)}
  <g transform="translate(36,30)">
    {xp_window(1128, 374, "Propiedades de Kisnner Obando.exe", "")}
  </g>
  <g transform="translate(36,60)">
    <rect width="1128" height="344" fill="{XP_PANEL}"/>
    {text(260, 78, "Kisnner Obando.", 46, INK, 700, spacing=-1)}
    {text(260, 108, "apps nativas para Apple · backend transaccional · ingeniería inversa · open source", 14, "#3a3a3a", 500)}
    {clip}
    {bubble}
    {text(260, 300, "kisnner26 · Managua, Nicaragua", 13, "#555", 500, opacity=.9, kind="mono")}
  </g>
  {taskbar}
  </g>"""
    defs = XP_DEFS + FIBERGLASS_DEFS + '\n    <clipPath id="card"><rect width="1200" height="440" rx="14"/></clipPath>'
    return svg(1200, 440, "Kisnner Obando", "Apps nativas para Apple, backend transaccional, ingeniería inversa y open source. Managua, Nicaragua. Portafolio: kisnner26.github.io", body, CLIPPY_STYLE, defs)


# ---------------------------------------------------------------- tarjetas de contribuciones (estáticas)
MERGE_PURPLE = "#8250df"


def merged_badge(x, y):
    """la insignia morada de "merged" que usa GitHub en los pull requests."""
    return f"""<g transform="translate({x},{y})">
    <rect width="118" height="26" rx="13" fill="{MERGE_PURPLE}"/>
    <circle cx="16" cy="13" r="3" fill="{WHITE}"/>
    <path d="M16 10V6M26 20v-6a4 4 0 0 0-4-4h-2" fill="none" stroke="{WHITE}" stroke-width="1.8" stroke-linecap="round"/>
    <circle cx="26" cy="20" r="3" fill="none" stroke="{WHITE}" stroke-width="1.8"/>
    {text(40, 18, "MERGEADO", 10.5, WHITE, 700, spacing=1)}
  </g>"""


def tile(repo, headline, sub, meta, url):
    inner = f"""  <rect width="384" height="300" fill="{XP_PANEL}"/>
    {text(32, 40, repo, 13, "#5a5a5a", 700, spacing=.5, kind="mono")}
    {merged_badge(234, 26)}
    {text(32, 80, headline[0], 27, INK, 700, spacing=-.6)}
    {text(32, 111, headline[1], 27, INK, 700, spacing=-.6)}
    {text(32, 144, sub[0], 14, "#3a3a3a", 400)}
    {text(32, 163, sub[1], 14, "#3a3a3a", 400)}
  <line x1="32" y1="254" x2="352" y2="254" stroke="{INK}" stroke-opacity=".12"/>
  {text(32, 282, meta, 12, "#555", 500, kind="mono")}"""
    body = xp_window(384, 330, repo, inner)
    return svg(384, 330, repo, " ".join(headline) + " " + " ".join(sub) + " " + meta, body, "", XP_DEFS), url


MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def contributions(d):
    y0 = 140
    # desde junio de 2026, cuando empezaron mis contribuciones reales; antes casi todo es cero
    first = datetime.strptime(d["first"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    skip = max(0, int((datetime(2026, 5, 31, tzinfo=timezone.utc) - first).days // 7))
    weeks = d["weeks"][skip:]
    first = datetime.fromtimestamp(first.timestamp() + skip * 7 * 86400, timezone.utc)
    peak = max(weeks) or 1
    left, right, base, top = 560, 1150, 180, 50
    gap = (right - left) / len(weeks)
    bars = ""
    for i, count in enumerate(weeks):
        h = max(4, (base - top) * (count / peak) ** .5)
        last = i == len(weeks) - 1
        bars += (f'<rect x="{left + i * gap:.1f}" y="{base - h:.1f}" width="{gap * .62:.1f}" height="{h:.1f}" rx="{gap * .18:.1f}" '
                 f'fill="#6cff6c" fill-opacity="{1 if last else .4}"/>')
    months = ""
    for i in range(len(weeks)):
        dt = first.timestamp() + i * 7 * 86400
        m = datetime.fromtimestamp(dt, timezone.utc)
        if m.day <= 7:
            months += text(left + i * gap, base + 22, MESES[m.month - 1], 11, "#8fb8ff", 400, kind="mono")
    stats = f"racha más larga {d['streak']} días   ·   {d['merged']} pull requests mergeados en proyectos ajenos"
    inner = f"""  <rect width="1200" height="230" fill="#05070d"/>
  {text(64, 40, "CONTRIBUCIONES · ÚLTIMO AÑO", 12.5, "#8fb8ff", 700, spacing=2.2, kind="mono")}
  {text(64, y0, f"{d['total']:,}", 64, "#6cff6c", 700)}
  {text(66, y0 + 26, "commits, pull requests, issues y revisiones", 14.5, "#cfe3ff", 400)}
  {bars}
  {months}
  <line x1="64" y1="204" x2="1136" y2="204" stroke="{WHITE}" stroke-opacity=".12"/>
  {text(64, 222, stats, 12.5, "#8fb8ff", 500, kind="mono")}"""
    body = xp_window(1200, 260, "contribuciones.exe", inner)
    return svg(1200, 260, "Contribuciones", f"{d['total']} contribuciones en el último año. Racha más larga: {d['streak']} días. {d['merged']} pull requests mergeados en proyectos ajenos.", body, "", XP_DEFS)


def pill(label, width, primary):
    h = 46
    fill = "url(#startgrad)" if primary else "#ece9d8"
    stroke = "#145314" if primary else XP_TITLE_A
    ink = WHITE if primary else INK
    body = f"""  <rect x="1" y="1" width="{width - 2}" height="{h}" rx="7" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>
  <rect x="3" y="3" width="{width - 6}" height="{h / 2 - 2:.0f}" rx="5" fill="{WHITE}" fill-opacity=".25"/>
  {text(width / 2 - 8, h / 2 + 6, label, 16, ink, 700, "middle")}
  <path d="M{width - 36} {h / 2 - 1:.0f}h11m-5-5 5 5-5 5" fill="none" stroke="{ink}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>"""
    return svg(width, h + 2, label, f"enlace: {label}", body, "", XP_DEFS)


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
    for old in ("tile-altserver.svg", "tile-relevo.svg", "tile-lumora.svg"):
        (ASSETS / old).unlink(missing_ok=True)
    write("hero.svg", hero())
    tile_urls = []
    for repo, headline, sub, meta, url in TILES:
        slug = repo.split("/")[-1].lower()
        content, link = tile(repo, headline, sub, meta, url)
        write(f"tile-{slug}.svg", content)
        tile_urls.append((slug, link))
    write("contributions.svg", contributions(data))
    for label, width, primary in (("Portafolio", 172, True), ("LinkedIn", 150, False), ("GitHub", 140, False), ("Correo", 134, False)):
        write(f"link-{label.lower()}.svg", pill(label, width, primary))
    print("listo:", len(list(ASSETS.glob("*.svg"))), "svg")
    print("tiles:", tile_urls)


if __name__ == "__main__":
    main()
