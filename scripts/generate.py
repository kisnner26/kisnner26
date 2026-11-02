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
ROLES = ["Parece que estás viendo mi perfil.",
         "¿Quieres ayuda con tu próximo pull request?",
         "Apps nativas para Apple, backend e ingeniería inversa."]


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
    <g class="pad" style="transform-origin:0px -40px;transform:rotate(-4deg)">
      <rect x="-54" y="-156" width="108" height="168" rx="6" fill="{PAD_YELLOW}" stroke="#c9ad3f" stroke-width="2"/>
      {"".join(f'<line x1="-44" y1="{y}" x2="44" y2="{y}" stroke="#d8c268" stroke-width="1.5"/>' for y in range(-134, 2, 14))}
    </g>
    <g class="wire" fill="none" stroke-linecap="round" style="transform-origin:0px -40px">
      <rect x="-46" y="-140" width="52" height="134" rx="26" stroke="#7d828e" stroke-width="10"/>
      <rect x="-46" y="-140" width="52" height="134" rx="26" stroke="#dfe2e8" stroke-width="3" opacity=".7"/>
      <rect x="-20" y="-118" width="34" height="140" rx="17" stroke="#7d828e" stroke-width="9"/>
      <rect x="-20" y="-118" width="34" height="140" rx="17" stroke="#dfe2e8" stroke-width="3" opacity=".7"/>
    </g>
    <g class="eyes">
      <ellipse cx="-19" cy="-116" rx="9.5" ry="12" fill="{WHITE}" stroke="#20242c" stroke-width="2.2" class="eye eye-l" style="animation-delay:{blink_delay}s"/>
      <ellipse cx="4" cy="-118" rx="9.5" ry="12" fill="{WHITE}" stroke="#20242c" stroke-width="2.2" class="eye eye-r" style="animation-delay:{blink_delay + .08}s"/>
      <g class="pupils">
        <circle cx="-16" cy="-113" r="3.8" fill="#15171c" class="pupil"/>
        <circle cx="7" cy="-115" r="3.8" fill="#15171c" class="pupil"/>
        <circle cx="-18.5" cy="-116.5" r="1.2" fill="{WHITE}"/>
        <circle cx="5.5" cy="-118.5" r="1.2" fill="{WHITE}"/>
      </g>
    </g>
    <g stroke="#15171c" stroke-width="2.8" stroke-linecap="round">
      <path class="brow-l" d="M-30 -134 q11 -8 21 -3" style="transform-origin:-20px -136px"/>
      <path class="brow-r" d="M-6 -138 q11 -6 21 1" style="transform-origin:4px -140px"/>
    </g>
  </g>"""


CLIPPY_STYLE = """.eye{transform-box:fill-box;transform-origin:center;animation:blink 4.6s ease-in-out infinite}
      @keyframes blink{0%,88%,100%{transform:scaleY(1)}91%{transform:scaleY(.08)}}
      .pupils{animation:look 9s ease-in-out infinite}
      @keyframes look{
        0%{transform:translate(0,0)}
        4%{transform:translate(4px,-2.5px)}
        10%{transform:translate(4px,-2.5px)}
        16%{transform:translate(0,0)}
        40%{transform:translate(0,0)}
        46%{transform:translate(-4.5px,2px)}
        53%{transform:translate(-4.5px,2px)}
        60%{transform:translate(0,0)}
        82%{transform:translate(0,0)}
        88%{transform:translate(2.5px,-3px)}
        94%{transform:translate(2.5px,-3px)}
        100%{transform:translate(0,0)}
      }
      .brow-l{animation:browl 5.4s ease-in-out infinite}
      .brow-r{animation:browr 5.4s ease-in-out infinite}
      @keyframes browl{0%,100%{transform:translateY(0) rotate(0)}22%{transform:translateY(-3px) rotate(-6deg)}50%{transform:translateY(0) rotate(0)}76%{transform:translateY(-1.5px) rotate(2deg)}}
      @keyframes browr{0%,100%{transform:translateY(0) rotate(0)}22%{transform:translateY(-1px) rotate(2deg)}50%{transform:translateY(0) rotate(0)}76%{transform:translateY(-3.5px) rotate(-7deg)}}
      .wire{animation:wire 6s ease-in-out infinite}
      @keyframes wire{0%,100%{transform:rotate(0) scale(1)}50%{transform:rotate(-1.6deg) scale(1.015)}}
      .pad{animation:pad 6s ease-in-out infinite}
      @keyframes pad{0%,100%{transform:rotate(-4deg)}50%{transform:rotate(-2deg)}}"""


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

EDITORIAL_BG = "#d9dfe3"
EDITORIAL_GRID = "#7f8991"
EDITORIAL_BLUE = "#1741c7"
EDITORIAL_DARK = "#101828"
EDITORIAL_DEFS = f"""    <pattern id="editorialgrid" width="56" height="56" patternUnits="userSpaceOnUse">
      <path d="M56 0H0V56" fill="none" stroke="{EDITORIAL_GRID}" stroke-width="1" stroke-dasharray="5 6" opacity=".45"/>
    </pattern>
    <linearGradient id="editorialblue" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#2358ec"/><stop offset="1" stop-color="#0b2a9a"/>
    </linearGradient>"""


def editorial_bg(w, h):
    pixels = "".join(
        f'<rect x="{x}" y="{y}" width="10" height="10" fill="{EDITORIAL_DARK}" opacity="{op}"/>'
        for x, y, op in ((42, 38, .18), (52, 48, .1), (1080, 74, .16), (1090, 64, .08),
                         (1014, 444, .14), (1024, 454, .08), (314, 474, .12), (324, 464, .07)))
    return f"""<rect width="{w}" height="{h}" fill="{EDITORIAL_BG}"/>
  <rect width="{w}" height="{h}" fill="url(#editorialgrid)"/>
  <circle cx="{w * .16:.0f}" cy="{h * .55:.0f}" r="{h * .22:.0f}" fill="none" stroke="{EDITORIAL_BLUE}" stroke-width="1.5" stroke-dasharray="7 7" opacity=".55"/>
  <circle cx="{w * .84:.0f}" cy="{h * .3:.0f}" r="{h * .13:.0f}" fill="none" stroke="{EDITORIAL_GRID}" stroke-width="1.5" stroke-dasharray="5 6" opacity=".7"/>
  {pixels}"""


# --------------------------------------------------- cromo "editor de niveles" (estilo Geometry Dash)
GD_LAVENDER_A, GD_LAVENDER_B = "#8f94d9", "#5a5fae"
GD_PANEL = "#b9bce3"
PALETTE = ["#f5903a", "#cfe23a", "#36cf3a", "#17c97a", "#2f9fe0", "#7b4fe4", "#e034a0", "#171a33", "#8686a0", "#ffffff"]
GD_DEFS = f'<linearGradient id="gdbar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{GD_LAVENDER_A}"/><stop offset="1" stop-color="{GD_LAVENDER_B}"/></linearGradient>'


def gd_window(w, h, title, inner, title_h=42):
    return f"""<g>
  <rect width="{w}" height="{h}" rx="9" fill="{GD_PANEL}" stroke="{GD_LAVENDER_B}" stroke-width="1.5"/>
  {gd_titlebar(w, title, title_h)}
  <g transform="translate(0,{title_h})">{inner}</g>
  </g>"""


def gd_titlebar(w, title, h=42):
    return f"""<rect width="{w}" height="{h}" rx="7" fill="url(#gdbar)"/>
  <rect x="10" y="{h / 2 - 11:.0f}" width="22" height="22" rx="4" fill="{WHITE}" fill-opacity=".85"/>
  <rect x="14" y="{h / 2 - 7:.0f}" width="6" height="6" fill="{GD_LAVENDER_B}"/>
  <rect x="22" y="{h / 2 - 7:.0f}" width="6" height="6" fill="{GD_LAVENDER_B}"/>
  <rect x="14" y="{h / 2 + 1:.0f}" width="6" height="6" fill="{GD_LAVENDER_B}"/>
  <rect x="22" y="{h / 2 + 1:.0f}" width="6" height="6" fill="{GD_LAVENDER_B}"/>
  {text(44, h / 2 + 6, title, 15, WHITE, 700, spacing=1, kind="mono")}
  <g transform="translate({w - 62},{h / 2 - 11:.0f})">
    <rect width="22" height="22" rx="4" fill="{WHITE}" fill-opacity=".85"/>
    <rect x="6" y="10" width="10" height="3" fill="{GD_LAVENDER_B}"/>
    <rect x="30" width="22" height="22" rx="4" fill="url(#closegrad)"/>
    <path d="M36 6l10 10m0-10l-10 10" stroke="{WHITE}" stroke-width="2" stroke-linecap="round"/>
  </g>"""


def gd_xboxes(x, y, w, rows=7):
    out = []
    bs, gap = (w - 10) / 2, 8
    for r in range(rows):
        for c in range(2):
            bx, by = x + c * (bs + gap), y + r * (bs + gap)
            out.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bs:.1f}" height="{bs:.1f}" rx="4" fill="{INK}" fill-opacity=".18"/>'
                        f'<path d="M{bx + 6:.1f} {by + 6:.1f}l{bs - 12:.1f} {bs - 12:.1f}m0-{bs - 12:.1f}l-{bs - 12:.1f} {bs - 12:.1f}" '
                        f'stroke="{INK}" stroke-opacity=".32" stroke-width="2" stroke-linecap="round"/>')
    return "".join(out)


def color_palette(x, y, w, h):
    n = len(PALETTE)
    gap, bs = 10, min(44, (w - 10 * (n - 1)) / n)
    out = [f'<rect x="{x - 14}" y="{y - 10}" width="{w + 28}" height="{h + 20}" rx="10" fill="{INK}" fill-opacity=".12"/>']
    for i, c in enumerate(PALETTE):
        bx = x + i * (bs + gap)
        out.append(f'<rect x="{bx:.1f}" y="{y}" width="{bs:.1f}" height="{bs:.1f}" rx="6" fill="{c}" stroke="#00000030" stroke-width="1.5"/>')
    return "".join(out)


# ---------------------------------------------------------------- stack: lo que uso de verdad, con sus logos
# vectores oficiales de simple icons 13.21.0 (cc0), viewBox 24x24
ICONOS = {
    "swift": "M7.508 0c-.287 0-.573 0-.86.002-.241.002-.483.003-.724.01-.132.003-.263.009-.395.015A9.154 9.154 0 0 0 4.348.15 5.492 5.492 0 0 0 2.85.645 5.04 5.04 0 0 0 .645 2.848c-.245.48-.4.972-.495 1.5-.093.52-.122 1.05-.136 1.576a35.2 35.2 0 0 0-.012.724C0 6.935 0 7.221 0 7.508v8.984c0 .287 0 .575.002.862.002.24.005.481.012.722.014.526.043 1.057.136 1.576.095.528.25 1.02.495 1.5a5.03 5.03 0 0 0 2.205 2.203c.48.244.97.4 1.498.495.52.093 1.05.124 1.576.138.241.007.483.009.724.01.287.002.573.002.86.002h8.984c.287 0 .573 0 .86-.002.241-.001.483-.003.724-.01a10.523 10.523 0 0 0 1.578-.138 5.322 5.322 0 0 0 1.498-.495 5.035 5.035 0 0 0 2.203-2.203c.245-.48.4-.972.495-1.5.093-.52.124-1.05.138-1.576.007-.241.009-.481.01-.722.002-.287.002-.575.002-.862V7.508c0-.287 0-.573-.002-.86a33.662 33.662 0 0 0-.01-.724 10.5 10.5 0 0 0-.138-1.576 5.328 5.328 0 0 0-.495-1.5A5.039 5.039 0 0 0 21.152.645 5.32 5.32 0 0 0 19.654.15a10.493 10.493 0 0 0-1.578-.138 34.98 34.98 0 0 0-.722-.01C17.067 0 16.779 0 16.492 0H7.508zm6.035 3.41c4.114 2.47 6.545 7.162 5.549 11.131-.024.093-.05.181-.076.272l.002.001c2.062 2.538 1.5 5.258 1.236 4.745-1.072-2.086-3.066-1.568-4.088-1.043a6.803 6.803 0 0 1-.281.158l-.02.012-.002.002c-2.115 1.123-4.957 1.205-7.812-.022a12.568 12.568 0 0 1-5.64-4.838c.649.48 1.35.902 2.097 1.252 3.019 1.414 6.051 1.311 8.197-.002C9.651 12.73 7.101 9.67 5.146 7.191a10.628 10.628 0 0 1-1.005-1.384c2.34 2.142 6.038 4.83 7.365 5.576C8.69 8.408 6.208 4.743 6.324 4.86c4.436 4.47 8.528 6.996 8.528 6.996.154.085.27.154.36.213.085-.215.16-.437.224-.668.708-2.588-.09-5.548-1.893-7.992z",
    "javascript": "M0 0h24v24H0V0zm22.034 18.276c-.175-1.095-.888-2.015-3.003-2.873-.736-.345-1.554-.585-1.797-1.14-.091-.33-.105-.51-.046-.705.15-.646.915-.84 1.515-.66.39.12.75.42.976.9 1.034-.676 1.034-.676 1.755-1.125-.27-.42-.404-.601-.586-.78-.63-.705-1.469-1.065-2.834-1.034l-.705.089c-.676.165-1.32.525-1.71 1.005-1.14 1.291-.811 3.541.569 4.471 1.365 1.02 3.361 1.244 3.616 2.205.24 1.17-.87 1.545-1.966 1.41-.811-.18-1.26-.586-1.755-1.336l-1.83 1.051c.21.48.45.689.81 1.109 1.74 1.756 6.09 1.666 6.871-1.004.029-.09.24-.705.074-1.65l.046.067zm-8.983-7.245h-2.248c0 1.938-.009 3.864-.009 5.805 0 1.232.063 2.363-.138 2.711-.33.689-1.18.601-1.566.48-.396-.196-.597-.466-.83-.855-.063-.105-.11-.196-.127-.196l-1.825 1.125c.305.63.75 1.172 1.324 1.517.855.51 2.004.675 3.207.405.783-.226 1.458-.691 1.811-1.411.51-.93.402-2.07.397-3.346.012-2.054 0-4.109 0-6.179l.004-.056z",
    "typescript": "M1.125 0C.502 0 0 .502 0 1.125v21.75C0 23.498.502 24 1.125 24h21.75c.623 0 1.125-.502 1.125-1.125V1.125C24 .502 23.498 0 22.875 0zm17.363 9.75c.612 0 1.154.037 1.627.111a6.38 6.38 0 0 1 1.306.34v2.458a3.95 3.95 0 0 0-.643-.361 5.093 5.093 0 0 0-.717-.26 5.453 5.453 0 0 0-1.426-.2c-.3 0-.573.028-.819.086a2.1 2.1 0 0 0-.623.242c-.17.104-.3.229-.393.374a.888.888 0 0 0-.14.49c0 .196.053.373.156.529.104.156.252.304.443.444s.423.276.696.41c.273.135.582.274.926.416.47.197.892.407 1.266.628.374.222.695.473.963.753.268.279.472.598.614.957.142.359.214.776.214 1.253 0 .657-.125 1.21-.373 1.656a3.033 3.033 0 0 1-1.012 1.085 4.38 4.38 0 0 1-1.487.596c-.566.12-1.163.18-1.79.18a9.916 9.916 0 0 1-1.84-.164 5.544 5.544 0 0 1-1.512-.493v-2.63a5.033 5.033 0 0 0 3.237 1.2c.333 0 .624-.03.872-.09.249-.06.456-.144.623-.25.166-.108.29-.234.373-.38a1.023 1.023 0 0 0-.074-1.089 2.12 2.12 0 0 0-.537-.5 5.597 5.597 0 0 0-.807-.444 27.72 27.72 0 0 0-1.007-.436c-.918-.383-1.602-.852-2.053-1.405-.45-.553-.676-1.222-.676-2.005 0-.614.123-1.141.369-1.582.246-.441.58-.804 1.004-1.089a4.494 4.494 0 0 1 1.47-.629 7.536 7.536 0 0 1 1.77-.201zm-15.113.188h9.563v2.166H9.506v9.646H6.789v-9.646H3.375z",
    "python": "M14.25.18l.9.2.73.26.59.3.45.32.34.34.25.34.16.33.1.3.04.26.02.2-.01.13V8.5l-.05.63-.13.55-.21.46-.26.38-.3.31-.33.25-.35.19-.35.14-.33.1-.3.07-.26.04-.21.02H8.77l-.69.05-.59.14-.5.22-.41.27-.33.32-.27.35-.2.36-.15.37-.1.35-.07.32-.04.27-.02.21v3.06H3.17l-.21-.03-.28-.07-.32-.12-.35-.18-.36-.26-.36-.36-.35-.46-.32-.59-.28-.73-.21-.88-.14-1.05-.05-1.23.06-1.22.16-1.04.24-.87.32-.71.36-.57.4-.44.42-.33.42-.24.4-.16.36-.1.32-.05.24-.01h.16l.06.01h8.16v-.83H6.18l-.01-2.75-.02-.37.05-.34.11-.31.17-.28.25-.26.31-.23.38-.2.44-.18.51-.15.58-.12.64-.1.71-.06.77-.04.84-.02 1.27.05zm-6.3 1.98l-.23.33-.08.41.08.41.23.34.33.22.41.09.41-.09.33-.22.23-.34.08-.41-.08-.41-.23-.33-.33-.22-.41-.09-.41.09zm13.09 3.95l.28.06.32.12.35.18.36.27.36.35.35.47.32.59.28.73.21.88.14 1.04.05 1.23-.06 1.23-.16 1.04-.24.86-.32.71-.36.57-.4.45-.42.33-.42.24-.4.16-.36.09-.32.05-.24.02-.16-.01h-8.22v.82h5.84l.01 2.76.02.36-.05.34-.11.31-.17.29-.25.25-.31.24-.38.2-.44.17-.51.15-.58.13-.64.09-.71.07-.77.04-.84.01-1.27-.04-1.07-.14-.9-.2-.73-.25-.59-.3-.45-.33-.34-.34-.25-.34-.16-.33-.1-.3-.04-.25-.02-.2.01-.13v-5.34l.05-.64.13-.54.21-.46.26-.38.3-.32.33-.24.35-.2.35-.14.33-.1.3-.06.26-.04.21-.02.13-.01h5.84l.69-.05.59-.14.5-.21.41-.28.33-.32.27-.35.2-.36.15-.36.1-.35.07-.32.04-.28.02-.21V6.07h2.09l.14.01zm-6.47 14.25l-.23.33-.08.41.08.41.23.33.33.23.41.08.41-.08.33-.23.23-.33.08-.41-.08-.41-.23-.33-.33-.23-.41-.08-.41.08z",
    "php": "M7.01 10.207h-.944l-.515 2.648h.838c.556 0 .97-.105 1.242-.314.272-.21.455-.559.55-1.049.092-.47.05-.802-.124-.995-.175-.193-.523-.29-1.047-.29zM12 5.688C5.373 5.688 0 8.514 0 12s5.373 6.313 12 6.313S24 15.486 24 12c0-3.486-5.373-6.312-12-6.312zm-3.26 7.451c-.261.25-.575.438-.917.551-.336.108-.765.164-1.285.164H5.357l-.327 1.681H3.652l1.23-6.326h2.65c.797 0 1.378.209 1.744.628.366.418.476 1.002.33 1.752a2.836 2.836 0 0 1-.305.847c-.143.255-.33.49-.561.703zm4.024.715l.543-2.799c.063-.318.039-.536-.068-.651-.107-.116-.336-.174-.687-.174H11.46l-.704 3.625H9.388l1.23-6.327h1.367l-.327 1.682h1.218c.767 0 1.295.134 1.586.401s.378.7.263 1.299l-.572 2.944h-1.389zm7.597-2.265a2.782 2.782 0 0 1-.305.847c-.143.255-.33.49-.561.703a2.44 2.44 0 0 1-.917.551c-.336.108-.765.164-1.286.164h-1.18l-.327 1.682h-1.378l1.23-6.326h2.649c.797 0 1.378.209 1.744.628.366.417.477 1.001.331 1.751zM17.766 10.207h-.943l-.516 2.648h.838c.557 0 .971-.105 1.242-.314.272-.21.455-.559.551-1.049.092-.47.049-.802-.125-.995s-.524-.29-1.047-.29z",
    "mysql": "M16.405 5.501c-.115 0-.193.014-.274.033v.013h.014c.054.104.146.18.214.273.054.107.1.214.154.32l.014-.015c.094-.066.14-.172.14-.333-.04-.047-.046-.094-.08-.14-.04-.067-.126-.1-.18-.153zM5.77 18.695h-.927a50.854 50.854 0 00-.27-4.41h-.008l-1.41 4.41H2.45l-1.4-4.41h-.01a72.892 72.892 0 00-.195 4.41H0c.055-1.966.192-3.81.41-5.53h1.15l1.335 4.064h.008l1.347-4.064h1.095c.242 2.015.384 3.86.428 5.53zm4.017-4.08c-.378 2.045-.876 3.533-1.492 4.46-.482.716-1.01 1.073-1.583 1.073-.153 0-.34-.046-.566-.138v-.494c.11.017.24.026.386.026.268 0 .483-.075.647-.222.197-.18.295-.382.295-.605 0-.155-.077-.47-.23-.944L6.23 14.615h.91l.727 2.36c.164.536.233.91.205 1.123.4-1.064.678-2.227.835-3.483zm12.325 4.08h-2.63v-5.53h.885v4.85h1.745zm-3.32.135l-1.016-.5c.09-.076.177-.158.255-.25.433-.506.648-1.258.648-2.253 0-1.83-.718-2.746-2.155-2.746-.704 0-1.254.232-1.65.697-.43.508-.646 1.256-.646 2.245 0 .972.19 1.686.574 2.14.35.41.877.615 1.583.615.264 0 .506-.033.725-.098l1.325.772.36-.622zM15.5 17.588c-.225-.36-.337-.94-.337-1.736 0-1.393.424-2.09 1.27-2.09.443 0 .77.167.977.5.224.362.336.936.336 1.723 0 1.404-.424 2.108-1.27 2.108-.445 0-.77-.167-.978-.5zm-1.658-.425c0 .47-.172.856-.516 1.156-.344.3-.803.45-1.384.45-.543 0-1.064-.172-1.573-.515l.237-.476c.438.22.833.328 1.19.328.332 0 .593-.073.783-.22a.754.754 0 00.3-.615c0-.33-.23-.61-.648-.845-.388-.213-1.163-.657-1.163-.657-.422-.307-.632-.636-.632-1.177 0-.45.157-.81.47-1.085.315-.278.72-.415 1.22-.415.512 0 .98.136 1.4.41l-.213.476a2.726 2.726 0 00-1.064-.23c-.283 0-.502.068-.654.206a.685.685 0 00-.248.524c0 .328.234.61.666.85.393.215 1.187.67 1.187.67.433.305.648.63.648 1.168zm9.382-5.852c-.535-.014-.95.04-1.297.188-.1.04-.26.04-.274.167.055.053.063.14.11.214.08.134.218.313.346.407.14.11.28.216.427.31.26.16.555.255.81.416.145.094.293.213.44.313.073.05.12.14.214.172v-.02c-.046-.06-.06-.147-.105-.214-.067-.067-.134-.127-.2-.193a3.223 3.223 0 00-.695-.675c-.214-.146-.682-.35-.77-.595l-.013-.014c.146-.013.32-.066.46-.106.227-.06.435-.047.67-.106.106-.027.213-.06.32-.094v-.06c-.12-.12-.21-.283-.334-.395a8.867 8.867 0 00-1.104-.823c-.21-.134-.476-.22-.697-.334-.08-.04-.214-.06-.26-.127-.12-.146-.19-.34-.275-.514a17.69 17.69 0 01-.547-1.163c-.12-.262-.193-.523-.34-.763-.69-1.137-1.437-1.826-2.586-2.5-.247-.14-.543-.2-.856-.274-.167-.008-.334-.02-.5-.027-.11-.047-.216-.174-.31-.235-.38-.24-1.364-.76-1.644-.072-.18.434.267.862.422 1.082.115.153.26.328.34.5.047.116.06.235.107.356.106.294.207.622.347.897.073.14.153.287.247.413.054.073.146.107.167.227-.094.136-.1.334-.154.5-.24.757-.146 1.693.194 2.25.107.166.362.534.703.393.3-.12.234-.5.32-.835.02-.08.007-.133.048-.187v.015c.094.188.188.367.274.555.206.328.566.668.867.895.16.12.287.328.487.402v-.02h-.015c-.043-.058-.1-.086-.154-.133a3.445 3.445 0 01-.35-.4 8.76 8.76 0 01-.747-1.218c-.11-.21-.202-.436-.29-.643-.04-.08-.04-.2-.107-.24-.1.146-.247.273-.32.453-.127.288-.14.642-.188 1.01-.027.007-.014 0-.027.014-.214-.052-.287-.274-.367-.46-.2-.475-.233-1.238-.06-1.785.047-.14.247-.582.167-.716-.042-.127-.174-.2-.247-.303a2.478 2.478 0 01-.24-.427c-.16-.374-.24-.788-.414-1.162-.08-.173-.22-.354-.334-.513-.127-.18-.267-.307-.368-.52-.033-.073-.08-.194-.027-.274.014-.054.042-.075.094-.09.088-.072.335.022.422.062.247.1.455.194.662.334.094.066.195.193.315.226h.14c.214.047.455.014.655.073.355.114.675.28.962.46a5.953 5.953 0 012.085 2.286c.08.154.115.295.188.455.14.33.313.663.455.982.14.315.275.636.476.897.1.14.502.213.682.286.133.06.34.115.46.188.23.14.454.3.67.454.11.076.443.243.463.378z",
    "html5": "M1.5 0h21l-1.91 21.563L11.977 24l-8.564-2.438L1.5 0zm7.031 9.75l-.232-2.718 10.059.003.23-2.622L5.412 4.41l.698 8.01h9.126l-.326 3.426-2.91.804-2.955-.81-.188-2.11H6.248l.33 4.171L12 19.351l5.379-1.443.744-8.157H8.531z",
    "css3": "M1.5 0h21l-1.91 21.563L11.977 24l-8.565-2.438L1.5 0zm17.09 4.413L5.41 4.41l.213 2.622 10.125.002-.255 2.716h-6.64l.24 2.573h6.182l-.366 3.523-2.91.804-2.956-.81-.188-2.11h-2.61l.29 3.855L12 19.288l5.373-1.53L18.59 4.414z",
    "gnubash": "M21.038,4.9l-7.577-4.498C13.009,0.134,12.505,0,12,0c-0.505,0-1.009,0.134-1.462,0.403L2.961,4.9 C2.057,5.437,1.5,6.429,1.5,7.503v8.995c0,1.073,0.557,2.066,1.462,2.603l7.577,4.497C10.991,23.866,11.495,24,12,24 c0.505,0,1.009-0.134,1.461-0.402l7.577-4.497c0.904-0.537,1.462-1.529,1.462-2.603V7.503C22.5,6.429,21.943,5.437,21.038,4.9z M15.17,18.946l0.013,0.646c0.001,0.078-0.05,0.167-0.111,0.198l-0.383,0.22c-0.061,0.031-0.111-0.007-0.112-0.085L14.57,19.29 c-0.328,0.136-0.66,0.169-0.872,0.084c-0.04-0.016-0.057-0.075-0.041-0.142l0.139-0.584c0.011-0.046,0.036-0.092,0.069-0.121 c0.012-0.011,0.024-0.02,0.036-0.026c0.022-0.011,0.043-0.014,0.062-0.006c0.229,0.077,0.521,0.041,0.802-0.101 c0.357-0.181,0.596-0.545,0.592-0.907c-0.003-0.328-0.181-0.465-0.613-0.468c-0.55,0.001-1.064-0.107-1.072-0.917 c-0.007-0.667,0.34-1.361,0.889-1.8l-0.007-0.652c-0.001-0.08,0.048-0.168,0.111-0.2l0.37-0.236 c0.061-0.031,0.111,0.007,0.112,0.087l0.006,0.653c0.273-0.109,0.511-0.138,0.726-0.088c0.047,0.012,0.067,0.076,0.048,0.151 l-0.144,0.578c-0.011,0.044-0.036,0.088-0.065,0.116c-0.012,0.012-0.025,0.021-0.038,0.028c-0.019,0.01-0.038,0.013-0.057,0.009 c-0.098-0.022-0.332-0.073-0.699,0.113c-0.385,0.195-0.52,0.53-0.517,0.778c0.003,0.297,0.155,0.387,0.681,0.396 c0.7,0.012,1.003,0.318,1.01,1.023C16.105,17.747,15.736,18.491,15.17,18.946z M19.143,17.859c0,0.06-0.008,0.116-0.058,0.145 l-1.916,1.164c-0.05,0.029-0.09,0.004-0.09-0.056v-0.494c0-0.06,0.037-0.093,0.087-0.122l1.887-1.129 c0.05-0.029,0.09-0.004,0.09,0.056V17.859z M20.459,6.797l-7.168,4.427c-0.894,0.523-1.553,1.109-1.553,2.187v8.833 c0,0.645,0.26,1.063,0.66,1.184c-0.131,0.023-0.264,0.039-0.398,0.039c-0.42,0-0.833-0.114-1.197-0.33L3.226,18.64 c-0.741-0.44-1.201-1.261-1.201-2.142V7.503c0-0.881,0.46-1.702,1.201-2.142l7.577-4.498c0.363-0.216,0.777-0.33,1.197-0.33 c0.419,0,0.833,0.114,1.197,0.33l7.577,4.498c0.624,0.371,1.046,1.013,1.164,1.732C21.686,6.557,21.12,6.411,20.459,6.797z",
}


def ficha(s, uid, fondo, trazo, k=.62, rx=.2, relleno="", extra=""):
    """logo sobre una ficha redondeada; k es la fracción de la ficha que ocupa el glifo."""
    esc = s * k / 24
    off = (s - s * k) / 2
    return f"""<clipPath id="clip-{uid}"><rect width="{s}" height="{s}" rx="{s * rx:.1f}"/></clipPath>
  <g clip-path="url(#clip-{uid})"><rect width="{s}" height="{s}" fill="{fondo}"/>{relleno}
  <path transform="translate({off:.2f},{off:.2f}) scale({esc:.4f})" d="{ICONOS[uid]}" fill="{trazo}"{extra}/></g>"""


def logo_swift(s):
    return ficha(s, "swift", WHITE, "#f05138", k=1)


def logo_js(s):
    return ficha(s, "javascript", "#1b1b1b", "#f7df1e", k=1)


def logo_ts(s):
    return ficha(s, "typescript", WHITE, "#3178c6", k=1)


def logo_python(s):
    # dos serpientes de dos colores: la mitad de arriba azul y la de abajo amarilla
    esc, off = s * .66 / 24, s * .17
    g = f'transform="translate({off:.2f},{off:.2f}) scale({esc:.4f})"'
    return f"""<clipPath id="clip-python"><rect width="{s}" height="{s}" rx="{s * .2:.1f}"/></clipPath>
  <clipPath id="py-arriba"><rect width="24" height="11.9"/></clipPath><clipPath id="py-abajo"><rect y="11.9" width="24" height="12.1"/></clipPath>
  <g clip-path="url(#clip-python)"><rect width="{s}" height="{s}" fill="{WHITE}"/>
  <g {g}><path d="{ICONOS['python']}" fill="#3776ab" clip-path="url(#py-arriba)"/><path d="{ICONOS['python']}" fill="#f5b800" clip-path="url(#py-abajo)"/></g></g>"""


def logo_php(s):
    return ficha(s, "php", WHITE, "#777bb4", k=.92)


def logo_mysql(s):
    return ficha(s, "mysql", WHITE, "#00758f", k=.84)


def logo_html(s):
    return ficha(s, "html5", WHITE, "#e34f26", k=.7)


def logo_css(s):
    return ficha(s, "css3", WHITE, "#1572b6", k=.7)


def logo_shell(s):
    return ficha(s, "gnubash", "#1b1b1b", "#4eaa25", k=.68)


STACK = [("Swift", logo_swift), ("JavaScript", logo_js), ("TypeScript", logo_ts), ("Python", logo_python),
         ("PHP", logo_php), ("MySQL", logo_mysql), ("HTML5", logo_html), ("CSS3", logo_css), ("Shell", logo_shell)]
SWIFT_DEFS = '<linearGradient id="swiftgrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fa7343"/><stop offset="1" stop-color="#f6416c"/></linearGradient>'


def stack():
    W, H = 1200, 242
    size, gap = 76, 42
    total = size * len(STACK) + gap * (len(STACK) - 1)
    cx0 = (W - total) / 2
    items = []
    for i, (label, logo) in enumerate(STACK):
        x = cx0 + i * (size + gap)
        tilt = (-2, 1, -1, 2, 0)[i % 5]
        items.append(f"""<g transform="translate({x:.1f},76)">
      <g class="tool-card" style="animation-delay:{.08 * i:.2f}s;transform:rotate({tilt}deg)">
        <rect x="-10" y="-10" width="{size + 20}" height="{size + 52}" fill="#f4f5f2" stroke="{EDITORIAL_DARK}" stroke-width="1.5"/>
        <rect x="-10" y="-10" width="{size + 20}" height="15" fill="{EDITORIAL_BLUE}"/>
        <g transform="translate(0,7)">{logo(size)}</g>
        {text(size / 2, size + 27, label.upper(), 11.5, EDITORIAL_DARK, 700, "middle", 1, .9, "mono")}
      </g>
    </g>""")
    body = f"""  <g clip-path="url(#stackcard)">
  {editorial_bg(W, H)}
  <rect x="0" y="0" width="{W}" height="44" fill="{EDITORIAL_DARK}"/>
  {text(34, 29, "KISNNER26 / TOOL DIRECTORY", 13, WHITE, 700, spacing=1.5, kind="mono")}
  {text(W - 34, 29, "09 ITEMS · ACTIVE", 12, "#a8bfff", 600, "end", spacing=1, kind="mono")}
  <path d="M0 218H1200" stroke="{EDITORIAL_BLUE}" stroke-width="10"/>
  {"".join(items)}
  </g>"""
    defs = EDITORIAL_DEFS + SWIFT_DEFS + f'\n    <clipPath id="stackcard"><rect width="{W}" height="{H}" rx="10"/></clipPath>'
    style = """.tool-card{transform-box:fill-box;transform-origin:center;animation:tool-in .65s cubic-bezier(.2,.9,.25,1.15) both}
      @keyframes tool-in{from{opacity:0;transform:translateY(28px) rotate(0deg) scale(.88)}to{opacity:1;transform:translateY(0) scale(1)}}
      .tool-card:nth-child(odd){animation-name:tool-in-alt}
      @keyframes tool-in-alt{from{opacity:0;transform:translateY(-20px) scale(.9)}to{opacity:1;transform:translateY(0) scale(1)}}"""
    return svg(W, H, "Tecnologías", "Swift, JavaScript, TypeScript, Python, PHP, MySQL, HTML5, CSS3 y Shell.", body, style, defs)


# ---------------------------------------------------------------- hero: editorial técnico inspirado en software de escritorio
def hero():
    W, H = 1200, 560
    body = f"""  <g clip-path="url(#card)">
  <g class="intro-scene">
    <rect width="{W}" height="{H}" fill="#cdd7dc"/>
    <rect y="524" width="{W}" height="36" fill="url(#tbar)"/>
    <rect x="12" y="529" width="72" height="25" fill="#34a33a" stroke="#1d6e24"/>
    {text(48, 547, "start", 12, WHITE, 700, "middle", kind="mono")}
    <g transform="translate(74,74)">
      <rect width="30" height="36" fill="#efe4a2" stroke="#7d7353"/>
      <path d="M0 8h30" stroke="#7d7353"/>
      {text(15, 53, "work", 10, EDITORIAL_DARK, 600, "middle", kind="mono")}
    </g>
    <g transform="translate(1080,62)">
      <rect width="29" height="34" fill="{EDITORIAL_BLUE}" stroke="{EDITORIAL_DARK}"/>
      <rect x="6" y="7" width="7" height="7" fill="#ff6b7a"/><rect x="16" y="7" width="7" height="7" fill="#78dbff"/>
      <rect x="6" y="18" width="7" height="7" fill="#b3f16d"/><rect x="16" y="18" width="7" height="7" fill="#ffe36b"/>
      {text(14, 50, "profile", 10, EDITORIAL_DARK, 600, "middle", kind="mono")}
    </g>
    <g class="desktop-click"><circle cx="1094" cy="79" r="24" fill="none" stroke="{EDITORIAL_BLUE}" stroke-width="3"/></g>
    <g class="desktop-cursor">
      <path d="M0 0L0 24L6 18L12 31L18 28L12 16L22 16Z" fill="#f7f7f4" stroke="{EDITORIAL_DARK}" stroke-width="2"/>
    </g>
    <g transform="translate(412,118)">
      <g class="boot-window">
        <rect x="-10" y="12" width="396" height="280" fill="{EDITORIAL_BLUE}" opacity=".2"/>
        <rect width="376" height="280" fill="#f2f3ef" stroke="{EDITORIAL_DARK}" stroke-width="2"/>
        {xp_titlebar(376, "profile.exe", h=32)}
        <rect x="14" y="48" width="348" height="214" fill="url(#editorialgrid)"/>
        <circle cx="174" cy="150" r="72" fill="none" stroke="{EDITORIAL_BLUE}" stroke-width="1.5" stroke-dasharray="6 7"/>
        {text(174, 142, "KISNNER26", 30, EDITORIAL_BLUE, 800, "middle", spacing=-1)}
        {text(174, 173, "loading profile...", 12, EDITORIAL_DARK, 600, "middle", spacing=1, kind="mono")}
      </g>
    </g>
  </g>

  <g class="type-scene">
    {editorial_bg(W, H)}
    <rect x="34" y="30" width="1132" height="500" fill="none" stroke="{EDITORIAL_DARK}" stroke-width="1.5"/>
    <g transform="translate(104,106)"><g class="type-left">
      <rect width="360" height="78" fill="{EDITORIAL_BLUE}"/>
      {text(180, 56, "BUILD SYSTEMS", 39, WHITE, 800, "middle", spacing=-1)}
      {text(0, 126, "NO. 01", 12, EDITORIAL_DARK, 700, spacing=1.3, kind="mono")}
      {text(0, 155, "Think about it.", 17, EDITORIAL_DARK, 400)}
    </g></g>
    <g transform="translate(678,126)"><g class="type-right">
      <rect width="390" height="82" fill="#f3f4f1" stroke="{EDITORIAL_DARK}" stroke-width="1.5"/>
      {text(195, 57, "DIG DEEPER", 44, EDITORIAL_BLUE, 800, "middle", spacing=-1)}
      {text(390, 126, "NO. 02", 12, EDITORIAL_DARK, 700, "end", spacing=1.3, kind="mono")}
    </g></g>
    <g transform="translate(196,316)"><g class="word-columns">
      {text(0, 0, "swift", 58, EDITORIAL_BLUE, 800, spacing=-2)}
      {text(278, 0, "backend", 58, EDITORIAL_DARK, 800, spacing=-2)}
      {text(620, 0, "web", 58, EDITORIAL_BLUE, 800, spacing=-2)}
      <path d="M0 38H820" stroke="{EDITORIAL_DARK}" stroke-width="2"/>
      {text(0, 72, "DESIGNER · DEVELOPER · STUDENT", 13, EDITORIAL_DARK, 700, spacing=2, kind="mono")}
    </g></g>
  </g>

  <g class="tunnel-scene">
    <rect width="{W}" height="{H}" fill="{EDITORIAL_BLUE}"/>
    <g transform="translate(600,280)"><g class="tunnel-rings">
      <circle r="330" fill="none" stroke="#d9dfe3" stroke-width="80" opacity=".35"/>
      <circle r="238" fill="none" stroke="{EDITORIAL_DARK}" stroke-width="3"/>
      <circle r="158" fill="#d9dfe3" stroke="{EDITORIAL_DARK}" stroke-width="3"/>
      <path d="M0 -240L180 150H-180Z" fill="#8ba4db" opacity=".9"/>
      <g transform="translate(-110,-100)"><g class="tunnel-window">
        <rect width="220" height="188" fill="#f3f4f1" stroke="{EDITORIAL_DARK}" stroke-width="3"/>
        {xp_titlebar(220, "enter.exe", h=26)}
        <rect x="12" y="40" width="196" height="132" fill="url(#editorialblue)"/>
        <g transform="translate(98,156)">{clippy(0, 0, .72)}</g>
      </g></g>
    </g></g>
    {text(54, 62, "NO. 03 / GO THROUGH", 13, WHITE, 700, spacing=1.8, kind="mono")}
    {text(1146, 510, "READ THE SYSTEM", 13, WHITE, 700, "end", spacing=1.8, kind="mono")}
  </g>

  <g class="float-scene">
    {editorial_bg(W, H)}
    <rect x="24" y="20" width="1152" height="520" fill="none" stroke="{EDITORIAL_DARK}" stroke-width="1.5"/>
    {text(48, 52, "NO. 04 / OPEN WINDOWS", 12, EDITORIAL_DARK, 700, spacing=1.6, kind="mono")}
    {text(1150, 52, "LEARN FROM THEM.", 12, EDITORIAL_DARK, 700, "end", spacing=1.6, kind="mono")}
    <circle cx="600" cy="286" r="190" fill="none" stroke="{EDITORIAL_BLUE}" stroke-width="2" stroke-dasharray="8 9"/>
    <circle cx="600" cy="286" r="128" fill="{EDITORIAL_BLUE}" opacity=".12"/>
    <g transform="translate(92,128)"><g class="float-window float-window-a">
      <rect width="300" height="196" fill="{EDITORIAL_DARK}" stroke="{EDITORIAL_BLUE}" stroke-width="3"/>
      {xp_titlebar(300, "reverse.exe", h=28)}
      <rect x="18" y="48" width="264" height="122" fill="#080d18"/>
      {text(34, 76, "00000000  55 48 89 E5", 12, "#8ba4ff", 500, spacing=.5, kind="mono")}
      {text(34, 101, "00000004  48 83 EC 20", 12, "#8ba4ff", 500, spacing=.5, kind="mono")}
      {text(34, 126, "00000008  E8 ?? ?? ??", 12, "#ffffff", 600, spacing=.5, kind="mono")}
      {text(34, 151, "inspect · understand · patch", 11, "#8ba4ff", 500, spacing=.6, kind="mono")}
    </g></g>
    <g transform="translate(808,92)"><g class="float-window float-window-b">
      <rect width="286" height="180" fill="#f3f4f1" stroke="{EDITORIAL_DARK}" stroke-width="2"/>
      {xp_titlebar(286, "build.app", h=28)}
      <rect x="20" y="48" width="246" height="108" fill="url(#editorialgrid)"/>
      {text(143, 92, "SWIFT", 38, EDITORIAL_BLUE, 800, "middle", spacing=-1)}
      {text(143, 123, "native by design", 12, EDITORIAL_DARK, 700, "middle", spacing=1, kind="mono")}
    </g></g>
    <g transform="translate(422,174)"><g class="float-window float-window-main">
      <rect x="-12" y="12" width="380" height="280" fill="{EDITORIAL_BLUE}" opacity=".18"/>
      <rect width="356" height="274" fill="#f3f4f1" stroke="{EDITORIAL_DARK}" stroke-width="3"/>
      {xp_titlebar(356, "kisnner26.exe", h=30)}
      <rect x="14" y="44" width="328" height="214" fill="url(#editorialblue)"/>
      <circle cx="164" cy="116" r="84" fill="none" stroke="#ffffff" stroke-width="1.5" stroke-dasharray="7 8" opacity=".75"/>
      <g transform="translate(164,210)">{clippy(0, 0, 1.02)}</g>
      {text(24, 68, "BUILD", 11, WHITE, 700, spacing=1.6, kind="mono")}
      {text(318, 238, "NO.04", 11, WHITE, 700, "end", spacing=1.3, kind="mono")}
    </g></g>
    <g transform="translate(870,352)"><g class="float-window float-window-c">
      <rect width="246" height="124" fill="{EDITORIAL_BLUE}" stroke="{EDITORIAL_DARK}" stroke-width="2"/>
      {text(123, 51, "SHIP", 34, WHITE, 800, "middle", spacing=-1)}
      {text(123, 82, "useful software", 11, WHITE, 600, "middle", spacing=1, kind="mono")}
    </g></g>
  </g>

  <g class="final-scene">
  {editorial_bg(W, H)}
  <rect x="26" y="22" width="1148" height="516" fill="none" stroke="{EDITORIAL_DARK}" stroke-width="1.5"/>
  <path d="M26 66H1174M82 22V538M1118 22V538" fill="none" stroke="{EDITORIAL_DARK}" stroke-width="1" opacity=".55"/>
  {text(48, 51, "KISNNER26 / SYSTEM PROFILE", 13, EDITORIAL_DARK, 700, spacing=1.5, kind="mono")}
  {text(1150, 51, "12.13 N · 86.25 W", 12, EDITORIAL_DARK, 600, "end", spacing=1, kind="mono")}

  <g transform="translate(82,104)">
    <g class="headline headline-one">
      {text(0, 82, "KISNNER", 78, EDITORIAL_DARK, 800, spacing=-2)}
    </g>
    <g class="headline headline-two">
      {text(0, 163, "OBANDO", 92, EDITORIAL_BLUE, 800, spacing=-3)}
    </g>
    <rect x="2" y="190" width="410" height="2" fill="{EDITORIAL_DARK}"/>
    {text(2, 224, "APPLE APPS / BACKEND / WEB TOOLS", 14, EDITORIAL_DARK, 700, spacing=1.1, kind="mono")}
    {text(2, 254, "software útil, sistemas sólidos y curiosidad", 15, EDITORIAL_DARK, 400)}
    {text(2, 276, "por lo que ocurre debajo de la interfaz.", 15, EDITORIAL_DARK, 400)}
    <g transform="translate(0,320)">
      <rect width="146" height="34" fill="{EDITORIAL_BLUE}"/>
      {text(73, 23, "MANAGUA / NI", 11.5, WHITE, 700, "middle", 1, 1, "mono")}
      <rect x="156" width="164" height="34" fill="none" stroke="{EDITORIAL_DARK}" stroke-width="1.5"/>
      {text(238, 23, "AVAILABLE FOR WORK", 11, EDITORIAL_DARK, 700, "middle", 1, .7, "mono")}
    </g>
  </g>

  <g transform="translate(638,90)">
    <g class="window-enter">
      <rect x="-18" y="16" width="458" height="374" fill="{EDITORIAL_BLUE}" opacity=".18"/>
      <rect width="440" height="374" rx="4" fill="#f3f4f1" stroke="{EDITORIAL_DARK}" stroke-width="2"/>
      {xp_titlebar(440, "profile.exe", h=32)}
      <g transform="translate(12,46)">
        <rect width="416" height="314" fill="url(#editorialblue)"/>
        <rect width="416" height="314" fill="url(#editorialgrid)" opacity=".32"/>
        <circle class="orbit orbit-a" cx="208" cy="156" r="122" fill="none" stroke="#dfe7ff" stroke-width="1.4" stroke-dasharray="9 8" opacity=".8"/>
        <circle class="orbit orbit-b" cx="208" cy="156" r="88" fill="none" stroke="#ffffff" stroke-width="1.2" stroke-dasharray="3 9" opacity=".55"/>
        <g transform="translate(208,264)"><g class="float">{clippy(0, 0, 1.42)}</g></g>
        {text(20, 28, "NO.01", 11.5, WHITE, 700, spacing=1.5, kind="mono")}
        {text(396, 292, "K.O.", 11.5, WHITE, 700, "end", spacing=1.5, kind="mono")}
      </g>
    </g>
  </g>
  <g class="side-note" transform="translate(1090,164) rotate(90)">
    {text(0, 0, "DESIGNER · DEVELOPER · STUDENT", 11.5, EDITORIAL_DARK, 700, spacing=1.6, kind="mono")}
  </g>
  <g transform="translate(48,512)">
    {text(0, 0, "NO. 02", 11, EDITORIAL_DARK, 700, spacing=1, kind="mono")}
    {text(1030, 0, "READ THE SYSTEM. BUILD THE NEXT ONE.", 11, EDITORIAL_DARK, 700, "end", spacing=1, kind="mono")}
  </g>
  </g>
  <rect class="scene-wipe" width="{W}" height="{H}" fill="#f3f4f1"/>
  </g>"""
    defs = XP_DEFS + EDITORIAL_DEFS + f'\n    <clipPath id="card"><rect width="{W}" height="{H}" rx="10"/></clipPath>'
    style = CLIPPY_STYLE + """
      .intro-scene,.type-scene,.tunnel-scene,.float-scene,.scene-wipe{opacity:0}
      .final-scene{opacity:1}
      .intro-scene{animation:intro-scene 18s ease-in-out 1 both}
      @keyframes intro-scene{0%,15%{opacity:1}20%,100%{opacity:0}}
      .boot-window{transform-box:fill-box;transform-origin:center;animation:boot-window 18s ease-in-out 1 both}
      @keyframes boot-window{0%,2%{opacity:0;transform:scale(.2) translateY(80px)}6%,12%{opacity:1;transform:scale(1) translateY(0)}18%{opacity:0;transform:scale(2.2) translateY(-38px)}100%{opacity:0}}
      .desktop-cursor{animation:desktop-cursor 18s ease-in-out 1 both}
      @keyframes desktop-cursor{0%{opacity:1;transform:translate(530px,330px)}4%,14%{opacity:1;transform:translate(1090px,84px)}18%,100%{opacity:0;transform:translate(1090px,84px)}}
      .desktop-click{transform-box:fill-box;transform-origin:center;animation:desktop-click 18s ease-out 1 both}
      @keyframes desktop-click{0%,3%{opacity:0;transform:scale(.3)}5%{opacity:1;transform:scale(1)}7%,100%{opacity:0;transform:scale(1.8)}}
      .type-scene{animation:type-scene 18s ease-in-out 1 both}
      @keyframes type-scene{0%,16%{opacity:0}21%,37%{opacity:1}42%,100%{opacity:0}}
      .type-left{transform-box:fill-box;transform-origin:center;animation:type-left 18s ease-in-out 1 both}
      @keyframes type-left{0%,17%{transform:translateX(-180px);opacity:0}22%,35%{transform:translateX(0);opacity:1}40%,100%{transform:translateX(-40px);opacity:0}}
      .type-right{transform-box:fill-box;transform-origin:center;animation:type-right 18s ease-in-out 1 both}
      @keyframes type-right{0%,18%{transform:translateX(180px);opacity:0}23%,36%{transform:translateX(0);opacity:1}41%,100%{transform:translateX(40px);opacity:0}}
      .word-columns{transform-box:fill-box;transform-origin:center;animation:word-columns 18s ease-in-out 1 both}
      @keyframes word-columns{0%,24%{transform:scaleX(.15);opacity:0}29%,37%{transform:scaleX(1);opacity:1}41%,100%{transform:scaleX(1.18);opacity:0}}
      .tunnel-scene{animation:tunnel-scene 18s ease-in-out 1 both}
      @keyframes tunnel-scene{0%,36%{opacity:0}40%,51%{opacity:1}56%,100%{opacity:0}}
      .tunnel-rings{transform-box:fill-box;transform-origin:center;animation:tunnel-rings 18s ease-in-out 1 both}
      @keyframes tunnel-rings{0%,36%{transform:scale(.28) rotate(-8deg)}43%{transform:scale(1) rotate(0)}54%,100%{transform:scale(2.7) rotate(7deg)}}
      .tunnel-window{transform-box:fill-box;transform-origin:center;animation:tunnel-window 18s ease-in-out 1 both}
      @keyframes tunnel-window{0%,38%{transform:scale(.25);opacity:0}43%{transform:scale(1);opacity:1}54%,100%{transform:scale(1.9);opacity:0}}
      .float-scene{animation:float-scene 18s ease-in-out 1 both}
      @keyframes float-scene{0%,52%{opacity:0}57%,72%{opacity:1}77%,100%{opacity:0}}
      .float-window{transform-box:fill-box;transform-origin:center;animation-duration:18s;animation-timing-function:ease-in-out;animation-iteration-count:1;animation-fill-mode:both}
      .float-window-a{animation-name:float-window-a}
      @keyframes float-window-a{0%,52%{opacity:0;transform:translate(-120px,30px) rotate(-8deg) scale(.72)}58%,72%{opacity:.92;transform:translate(0) rotate(-3deg) scale(1)}77%,100%{opacity:0;transform:translate(-40px,-15px) rotate(-5deg) scale(.92)}}
      .float-window-b{animation-name:float-window-b}
      @keyframes float-window-b{0%,53%{opacity:0;transform:translate(120px,-35px) rotate(9deg) scale(.7)}59%,72%{opacity:.95;transform:translate(0) rotate(3deg) scale(1)}77%,100%{opacity:0;transform:translate(35px,20px) rotate(5deg) scale(.94)}}
      .float-window-main{animation-name:float-window-main}
      @keyframes float-window-main{0%,54%{opacity:0;transform:scale(.34)}61%,72%{opacity:1;transform:scale(1)}77%,100%{opacity:0;transform:scale(1.34)}}
      .float-window-c{animation-name:float-window-c}
      @keyframes float-window-c{0%,56%{opacity:0;transform:translate(90px,60px) rotate(7deg)}62%,72%{opacity:.92;transform:translate(0) rotate(2deg)}77%,100%{opacity:0;transform:translate(45px,15px) rotate(4deg)}}
      .final-scene{animation:final-scene 18s ease-in-out 1 both}
      @keyframes final-scene{0%,73%{opacity:0}78%,100%{opacity:1}}
      .headline{animation:final-left 18s ease-in-out 1 both}
      .headline-two{animation-delay:.12s}
      @keyframes final-left{0%,74%{opacity:0;transform:translateX(-70px)}79%,100%{opacity:1;transform:translateX(0)}}
      .window-enter{transform-box:fill-box;transform-origin:center;animation:final-window 18s ease-in-out 1 both}
      @keyframes final-window{0%,73%{opacity:0;transform:scale(.65) rotate(4deg)}78%,100%{opacity:1;transform:scale(1) rotate(0)}}
      .float{animation:float 4.8s ease-in-out infinite}
      @keyframes float{0%,100%{transform:translateY(0) rotate(-.4deg)}50%{transform:translateY(-12px) rotate(1deg)}}
      .orbit{transform-box:fill-box;transform-origin:center;animation:orbit 16s linear infinite}
      .orbit-b{animation-direction:reverse;animation-duration:11s}
      @keyframes orbit{to{transform:rotate(360deg)}}
      .scene-wipe{transform-box:fill-box;transform-origin:left center;animation:scene-wipe 18s ease-in-out 1 both}
      @keyframes scene-wipe{0%,16%{opacity:0;transform:scaleX(0)}18%{opacity:1;transform:scaleX(1)}20%{opacity:0;transform:scaleX(1)}36%{opacity:0;transform:scaleX(0)}38%{opacity:1;transform:scaleX(1)}40%{opacity:0;transform:scaleX(1)}52%{opacity:0;transform:scaleX(0)}54%{opacity:1;transform:scaleX(1)}57%{opacity:0;transform:scaleX(1)}72%{opacity:0;transform:scaleX(0)}74%{opacity:1;transform:scaleX(1)}78%,100%{opacity:0;transform:scaleX(1)}}
      @media (prefers-reduced-motion:reduce){.intro-scene,.type-scene,.tunnel-scene,.float-scene,.scene-wipe{display:none}.final-scene{display:inline;opacity:1}}"""
    return svg(W, H, "Kisnner Obando", "Apps nativas para Apple, backend transaccional, ingeniería inversa y open source. Managua, Nicaragua. Portafolio: kisnner26.github.io", body, style, defs)


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
    last_x = last_y = last_h = 0
    for i, count in enumerate(weeks):
        h = max(4, (base - top) * (count / peak) ** .5)
        last = i == len(weeks) - 1
        if last:
            last_x, last_y, last_h = left + i * gap, base - h, h
        bars += (f'<rect x="{left + i * gap:.1f}" y="{base - h:.1f}" width="{gap * .62:.1f}" height="{h:.1f}" rx="{gap * .18:.1f}" '
                 f'class="contribution-bar{" final-bar" if last else ""}" fill="{"#ffffff" if last else "#7898ff"}" fill-opacity="{1 if last else .58}" '
                 f'style="animation-delay:{1.1 + i * .085:.2f}s"/>')
    months = ""
    for i in range(len(weeks)):
        dt = first.timestamp() + i * 7 * 86400
        m = datetime.fromtimestamp(dt, timezone.utc)
        if m.day <= 7:
            months += text(left + i * gap, base + 22, MESES[m.month - 1], 11, "#8fb8ff", 400, kind="mono")
    stats = f"racha más larga {d['streak']} días   ·   {d['merged']} pull requests mergeados en proyectos ajenos"
    steps = [0] + [round(d["total"] * factor) for factor in (.08, .23, .48, .73)] + [d["total"]]
    steps = list(dict.fromkeys(steps))
    counter = ""
    for i, value in enumerate(steps):
        final = " counter-final" if i == len(steps) - 1 else ""
        counter += text(64, y0, f"{value:,}", 64, WHITE, 700,
                        extra=f'class="counter-step counter-step-{i}{final}" font-variant-numeric="tabular-nums"')
    counter_rules = []
    interval = 68 / len(steps)
    for i in range(len(steps)):
        start = 7 + i * interval
        end = 7 + (i + 1) * interval
        counter_rules.append(f".counter-step-{i}{{animation:count-step-{i} 8s ease-in-out 1 both}}")
        if i == 0:
            frames = (f"0%,{start - .1:.1f}%{{opacity:0;transform:translateY(18px) scale(.82)}}"
                      f"{start:.1f}%,{end - .1:.1f}%{{opacity:1;transform:translateY(0) scale(1)}}"
                      f"{end:.1f}%,100%{{opacity:0;transform:translateY(-18px) scale(1.08)}}")
        elif i == len(steps) - 1:
            frames = (f"0%,{start - .1:.1f}%{{opacity:0;transform:translateY(18px) scale(.84)}}"
                      f"{start:.1f}%,{end:.1f}%{{opacity:1;transform:translateY(0) scale(1.12)}}"
                      f"88%,100%{{opacity:1;transform:translateY(0) scale(1)}}")
        else:
            frames = (f"0%,{start - .1:.1f}%{{opacity:0;transform:translateY(16px) scale(.86)}}"
                      f"{start:.1f}%,{end - .1:.1f}%{{opacity:1;transform:translateY(0) scale(1)}}"
                      f"{end:.1f}%,100%{{opacity:0;transform:translateY(-16px) scale(1.1)}}")
        counter_rules.append(f"@keyframes count-step-{i}{{{frames}}}")
    counter_style = "\n      ".join(counter_rules)
    style = f""".counter-step{{opacity:0;transform-box:fill-box;transform-origin:left center}}.counter-final{{opacity:1}}
      {counter_style}
      .contribution-bar{{transform-box:fill-box;transform-origin:center bottom;animation:grow-bar .72s ease-out 1 both}}
      @keyframes grow-bar{{from{{transform:scaleY(0);opacity:0}}70%{{transform:scaleY(1.08);opacity:1}}to{{transform:scaleY(1);opacity:1}}}}
      .sync-label{{opacity:1;animation:sync-label 8s ease-in-out 1 both}}
      @keyframes sync-label{{0%,47%{{opacity:1;transform:translateY(0)}}56%,100%{{opacity:0;transform:translateY(-8px)}}}}
      .ready-label{{opacity:0;animation:ready-label 8s ease-out 1 both}}
      @keyframes ready-label{{0%,53%{{opacity:0;transform:translateY(8px)}}63%,100%{{opacity:1;transform:translateY(0)}}}}
      .sync-progress{{transform-box:fill-box;transform-origin:left center;animation:sync-progress 8s ease-in-out 1 both}}
      @keyframes sync-progress{{0%{{transform:scaleX(0);opacity:.3}}72%{{transform:scaleX(1);opacity:1}}100%{{transform:scaleX(1);opacity:.42}}}}
      .chart-scan{{opacity:0;transform-box:fill-box;transform-origin:center;animation:chart-scan 8s ease-in-out 1 both}}
      @keyframes chart-scan{{0%,38%{{opacity:0;transform:translateX(0)}}45%{{opacity:.85}}73%{{opacity:.85;transform:translateX(570px)}}78%,100%{{opacity:0;transform:translateX(570px)}}}}
      .counter-echo{{transform-box:fill-box;transform-origin:left center;animation:counter-echo 8s ease-out 1 both}}
      @keyframes counter-echo{{0%,68%{{opacity:0;transform:scale(.8)}}76%{{opacity:.34;transform:scale(1.18)}}86%,100%{{opacity:0;transform:scale(1.28)}}}}
      .final-halo{{transform-box:fill-box;transform-origin:center;animation:final-halo 8s ease-out 1 both}}
      @keyframes final-halo{{0%,69%{{opacity:0;transform:scale(.45)}}78%{{opacity:1;transform:scale(1)}}90%,100%{{opacity:.28;transform:scale(1.18)}}}}
      .burst{{opacity:0;transform-box:fill-box;transform-origin:center;animation-duration:8s;animation-timing-function:ease-out;animation-iteration-count:1;animation-fill-mode:both}}
      .burst-a{{animation-name:burst-a}}@keyframes burst-a{{0%,71%{{opacity:0;transform:translate(0,0) scale(.3)}}79%{{opacity:1}}91%,100%{{opacity:0;transform:translate(-28px,-34px) scale(1)}}}}
      .burst-b{{animation-name:burst-b}}@keyframes burst-b{{0%,72%{{opacity:0;transform:translate(0,0) scale(.3)}}80%{{opacity:1}}92%,100%{{opacity:0;transform:translate(30px,-22px) scale(.9)}}}}
      .burst-c{{animation-name:burst-c}}@keyframes burst-c{{0%,73%{{opacity:0;transform:translate(0,0) scale(.3)}}81%{{opacity:1}}93%,100%{{opacity:0;transform:translate(-18px,30px) scale(.75)}}}}
      @media (prefers-reduced-motion:reduce){{.counter-step{{display:none}}.counter-final{{display:inline;transform:none}}.sync-label,.chart-scan,.counter-echo,.burst{{display:none}}.ready-label,.sync-progress,.final-halo{{animation:none;opacity:1;transform:none}}}}"""
    inner = f"""  <rect width="1200" height="240" fill="{EDITORIAL_DARK}"/>
  <rect width="1200" height="240" fill="url(#editorialgrid)" opacity=".14"/>
  {text(64, 40, "CONTRIBUCIONES · ÚLTIMO AÑO", 12.5, "#a8bfff", 700, spacing=2.2, kind="mono")}
  <g class="sync-label">{text(1136, 40, "SYNCING ACTIVITY...", 11.5, "#a8bfff", 700, "end", spacing=1.4, kind="mono")}</g>
  <g class="ready-label">{text(1136, 40, "SNAPSHOT VERIFICADO", 11.5, WHITE, 700, "end", spacing=1.4, kind="mono")}</g>
  <rect class="sync-progress" x="64" y="51" width="1072" height="2" fill="#7898ff"/>
  {text(64, y0, f"{d['total']:,}", 64, "none", 700, extra='class="counter-echo" stroke="#7898ff" stroke-width="1.2" font-variant-numeric="tabular-nums"')}
  {counter}
  {text(66, y0 + 26, "commits, pull requests, issues y revisiones", 14.5, "#dfe7ff", 400)}
  {bars}
  <g transform="translate({left:.1f},{top:.1f})"><rect class="chart-scan" width="3" height="{base - top:.1f}" fill="#ffffff"/></g>
  <rect class="final-halo" x="{last_x - 7:.1f}" y="{last_y - 7:.1f}" width="{gap * .62 + 14:.1f}" height="{last_h + 14:.1f}" rx="8" fill="none" stroke="#ffffff" stroke-width="2"/>
  <rect class="burst burst-a" x="{last_x + 3:.1f}" y="{last_y + 8:.1f}" width="7" height="7" fill="#ffffff"/>
  <rect class="burst burst-b" x="{last_x + 7:.1f}" y="{last_y + 14:.1f}" width="6" height="6" fill="#7898ff"/>
  <rect class="burst burst-c" x="{last_x + 2:.1f}" y="{last_y + 20:.1f}" width="5" height="5" fill="#ffffff"/>
  {months}
  <line x1="64" y1="204" x2="1136" y2="204" stroke="{WHITE}" stroke-opacity=".12"/>
  {text(64, 222, stats, 12.5, "#a8bfff", 500, kind="mono")}"""
    body = xp_window(1200, 272, "KISNNER26 / contributions.exe", inner, theme_fill=EDITORIAL_BG, title_h=32)
    return svg(1200, 272, "Contribuciones", f"{d['total']} contribuciones en el último año. Racha más larga: {d['streak']} días. {d['merged']} pull requests mergeados en proyectos ajenos.", body, style, XP_DEFS + EDITORIAL_DEFS)


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
    for old in glob_old():
        old.unlink(missing_ok=True)
    write("hero.svg", hero())
    write("stack.svg", stack())
    write("contributions-motion.svg", contributions(data))
    for label, width, primary in (("Portafolio", 172, True), ("LinkedIn", 150, False), ("GitHub", 140, False), ("Correo", 134, False)):
        write(f"link-{label.lower()}.svg", pill(label, width, primary))
    print("listo:", len(list(ASSETS.glob("*.svg"))), "svg")


def glob_old():
    return list(ASSETS.glob("tile-*.svg"))


if __name__ == "__main__":
    main()
