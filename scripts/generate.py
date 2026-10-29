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
def logo_swift(s):
    return f"""<rect width="{s}" height="{s}" rx="{s * .22:.1f}" fill="url(#swiftgrad)"/>
  <path d="M{s * .22:.1f} {s * .24:.1f} C{s * .5:.1f} {s * .3:.1f} {s * .86:.1f} {s * .5:.1f} {s * .82:.1f} {s * .62:.1f}
    C{s * .78:.1f} {s * .74:.1f} {s * .6:.1f} {s * .78:.1f} {s * .4:.1f} {s * .72:.1f}
    C{s * .55:.1f} {s * .68:.1f} {s * .62:.1f} {s * .58:.1f} {s * .58:.1f} {s * .5:.1f}
    C{s * .48:.1f} {s * .58:.1f} {s * .3:.1f} {s * .6:.1f} {s * .18:.1f} {s * .5:.1f}
    C{s * .3:.1f} {s * .5:.1f} {s * .38:.1f} {s * .44:.1f} {s * .4:.1f} {s * .38:.1f}
    C{s * .32:.1f} {s * .36:.1f} {s * .24:.1f} {s * .3:.1f} {s * .22:.1f} {s * .24:.1f} Z" fill="{WHITE}"/>"""


def logo_js(s):
    return f"""<rect width="{s}" height="{s}" rx="{s * .16:.1f}" fill="#f0db4f"/>
  {text(s * .5, s * .72, "JS", s * .4, "#1b1b1b", 800, "middle")}"""


def logo_ts(s):
    return f"""<rect width="{s}" height="{s}" rx="{s * .16:.1f}" fill="#3178c6"/>
  {text(s * .5, s * .72, "TS", s * .4, WHITE, 800, "middle")}"""


def logo_python(s):
    c1, c2 = "#3776ab", "#ffd43b"
    return f"""<rect width="{s}" height="{s}" rx="{s * .22:.1f}" fill="{INK}"/>
  <g transform="translate({s * .5:.1f},{s * .5:.1f})">
    <path d="M-2 -24 C10 -24 16 -20 16 -14 V-2 H-10 V4 H22 V-16 C22 -28 12 -34 -2 -34 C-16 -34 -22 -28 -22 -18 H-8 C-8 -22 -6 -24 -2 -24 Z" fill="{c1}" transform="scale({s / 64:.3f})"/>
    <path d="M2 24 C-10 24 -16 20 -16 14 V2 H10 V-4 H-22 V16 C-22 28 -12 34 2 34 C16 34 22 28 22 18 H8 C8 22 6 24 2 24 Z" fill="{c2}" transform="scale({s / 64:.3f})"/>
    <circle cx="{-6 * s / 64:.1f}" cy="{-27 * s / 64:.1f}" r="{2.6 * s / 64:.1f}" fill="{WHITE}"/>
    <circle cx="{6 * s / 64:.1f}" cy="{27 * s / 64:.1f}" r="{2.6 * s / 64:.1f}" fill="{WHITE}"/>
  </g>"""


def logo_php(s):
    return f"""<rect width="{s}" height="{s}" rx="{s * .16:.1f}" fill="{WHITE}"/>
  <ellipse cx="{s / 2:.1f}" cy="{s / 2:.1f}" rx="{s * .46:.1f}" ry="{s * .3:.1f}" fill="#777bb4"/>
  {text(s / 2, s * .58, "php", s * .3, WHITE, 800, "middle", extra='font-style="italic"')}"""


def logo_mysql(s):
    return f"""<rect width="{s}" height="{s}" rx="{s * .16:.1f}" fill="{WHITE}" stroke="#d9d9e3" stroke-width="2"/>
  <path d="M{s * .22:.1f} {s * .72:.1f} C{s * .2:.1f} {s * .5:.1f} {s * .3:.1f} {s * .28:.1f} {s * .5:.1f} {s * .24:.1f}
    C{s * .7:.1f} {s * .2:.1f} {s * .84:.1f} {s * .34:.1f} {s * .78:.1f} {s * .5:.1f}
    C{s * .72:.1f} {s * .66:.1f} {s * .5:.1f} {s * .62:.1f} {s * .4:.1f} {s * .7:.1f}" fill="none" stroke="#00618a" stroke-width="{s * .07:.1f}" stroke-linecap="round"/>
  <path d="M{s * .62:.1f} {s * .4:.1f} l{s * .14:.1f} -{s * .1:.1f} l-{s * .02:.1f} {s * .14:.1f} Z" fill="#e97d30"/>"""


def logo_html(s):
    return f"""<path d="M{s * .5:.1f} 0 L{s} {s * .14:.1f} L{s} {s} L{s * .5:.1f} {s * 1.18:.1f} L0 {s} L0 {s * .14:.1f} Z" fill="#e34f26"/>
  {text(s * .5, s * .7, "5", s * .42, WHITE, 800, "middle")}"""


def logo_css(s):
    return f"""<path d="M{s * .5:.1f} 0 L{s} {s * .14:.1f} L{s} {s} L{s * .5:.1f} {s * 1.18:.1f} L0 {s} L0 {s * .14:.1f} Z" fill="#1572b6"/>
  {text(s * .5, s * .7, "3", s * .42, WHITE, 800, "middle")}"""


def logo_shell(s):
    return f"""<rect width="{s}" height="{s}" rx="{s * .16:.1f}" fill="#1b1b1b"/>
  {text(s * .16, s * .62, ">_", s * .34, "#6cff6c", 800, kind="mono")}"""


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
        {logo(size)}
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
