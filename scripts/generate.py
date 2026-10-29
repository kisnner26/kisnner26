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


CLIPPY_STYLE = """.eye{animation:blink 4.6s ease-in-out infinite}
      @keyframes blink{0%,88%,100%{ry:12}91%{ry:1}}
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


# ---------------------------------------------------------------- stack: lo que uso de verdad
STACK = [
    ("Swift", "#f05138"), ("JavaScript", "#f1e05a"), ("TypeScript", "#3178c6"),
    ("Python", "#3572a5"), ("PHP", "#4f5d95"), ("MySQL", "#00618a"),
    ("HTML · CSS", "#e34c26"), ("Shell", "#89e051"),
]


def tech_chip(x, y, label, color):
    w = len(label) * 8.6 + 48
    chip = (f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="34" rx="17" fill="{WHITE}" fill-opacity=".94" stroke="{GD_LAVENDER_B}" stroke-width="1.3"/>'
            f'<circle cx="{x + 20:.1f}" cy="{y + 17}" r="6" fill="{color}" stroke="#00000025" stroke-width="1"/>'
            f'{text(x + 35, y + 22, label, 13.5, INK, 700, kind="mono")}')
    return chip, w


def stack():
    W, H, gap = 1200, 108, 14
    widths = [tech_chip(0, 0, label, color)[1] for label, color in STACK]
    total = sum(widths) + gap * (len(STACK) - 1)
    chips, cx = [], (W - total) / 2
    for (label, color), w in zip(STACK, widths):
        chip, _ = tech_chip(cx, 37, label, color)
        chips.append(chip)
        cx += w + gap
    inner = f"""  <rect width="{W}" height="{H - 42}" fill="{GD_PANEL}"/>
  {"".join(chips)}"""
    body = gd_window(W, H, "KISNNER26 / STACK.GMD", inner)
    return svg(W, H, "Tecnologías", "Swift, JavaScript, TypeScript, Python, PHP, MySQL, HTML, CSS y Shell.", body, "", XP_DEFS + GD_DEFS)


# ---------------------------------------------------------------- hero: un Clippy grande y animado
def hero():
    W, H = 1200, 560
    top_h, side_w, pal_h = 42, 96, 70
    view_x, view_w = side_w, W - side_w * 2 - 18
    view_y, view_h = top_h, H - top_h - pal_h
    body = f"""  <g clip-path="url(#card)">
  <rect width="{W}" height="{H}" fill="{GD_PANEL}"/>
  {gd_titlebar(W, "KISNNER26 / PERFIL.GMD", top_h)}
  <g transform="translate(10,{top_h + 14})">{gd_xboxes(0, 0, side_w - 20)}</g>
  <g transform="translate({W - side_w + 10},{top_h + 14})">{gd_xboxes(0, 0, side_w - 20, rows=7)}</g>
  <g clip-path="url(#viewport)">
    <g transform="translate({view_x},{view_y})">
      {fiberglass_bg(view_w, view_h)}
      <g transform="translate({view_w / 2:.0f},{view_h - 96:.0f})"><g class="float">{clippy(0, 0, 1.9)}</g></g>
      {text(view_w / 2, view_h - 16, "kisnner26 · Managua, Nicaragua", 13, WHITE, 500, "middle", .6, 1, "mono")}
    </g>
  </g>
  {color_palette(view_x + 20, H - pal_h / 2 - 18, view_w - 40, 36)}
  </g>"""
    defs = (XP_DEFS + FIBERGLASS_DEFS + GD_DEFS
            + f'\n    <clipPath id="card"><rect width="{W}" height="{H}" rx="14"/></clipPath>'
            + f'\n    <clipPath id="viewport"><rect x="{view_x}" y="{view_y}" width="{view_w}" height="{view_h}" rx="6"/></clipPath>')
    style = CLIPPY_STYLE + """
      .float{animation:float 4.5s ease-in-out infinite}
      @keyframes float{0%,100%{transform:translateY(0) rotate(0deg)}50%{transform:translateY(-14px) rotate(1.2deg)}}"""
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
    body = gd_window(1200, 272, "KISNNER26 / CONTRIBUCIONES.GMD", inner)
    return svg(1200, 272, "Contribuciones", f"{d['total']} contribuciones en el último año. Racha más larga: {d['streak']} días. {d['merged']} pull requests mergeados en proyectos ajenos.", body, "", XP_DEFS + GD_DEFS)


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
    write("contributions.svg", contributions(data))
    for label, width, primary in (("Portafolio", 172, True), ("LinkedIn", 150, False), ("GitHub", 140, False), ("Correo", 134, False)):
        write(f"link-{label.lower()}.svg", pill(label, width, primary))
    print("listo:", len(list(ASSETS.glob("*.svg"))), "svg")


def glob_old():
    return list(ASSETS.glob("tile-*.svg"))


if __name__ == "__main__":
    main()
