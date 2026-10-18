"""genera los svg animados del perfil (agua, burbujas, vidrio) y el snapshot que lee la web. solo biblioteca estándar.

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
DOCS = ROOT / "docs"
SNAPSHOT = ROOT / "data" / "snapshot.json"
LOGIN = "kisnner26"


MANAGUA = (12.13, -86.25)
ROLES = ["Apps nativas para Apple.", "Backend transaccional.", "Ingeniería inversa.", "Open source."]



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




# ---------------------------------------------------------------- frutiger aero, versión agua
DEEP, MID, LIME = "#064a73", "#2b7ea6", "#b8ff6a"
AERO = "font-family=\"Frutiger,'Segoe UI','Nunito','SF Pro Rounded','Helvetica Neue',Arial,sans-serif\""
SITE = "https://kisnner26.github.io/kisnner26/"
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def rnd(i, salt):
    return (math.sin(i * 12.9898 + salt * 78.233) * 43758.5453) % 1


def svg(width, height, title, desc, body, style="", defs=""):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="t d">
  <title id="t">{escape(title)}</title>
  <desc id="d">{escape(desc)}</desc>
  <defs>
    <linearGradient id="ink" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0b78b8"/><stop offset="1" stop-color="{DEEP}"/></linearGradient>
    <filter id="emboss" x="-5%" y="-10%" width="110%" height="130%"><feDropShadow dx="0" dy="2" stdDeviation="0" flood-color="#ffffff" flood-opacity=".9"/></filter>
    <radialGradient id="bub" cx=".35" cy=".3" r=".75"><stop offset="0" stop-color="#fff" stop-opacity=".9"/><stop offset=".3" stop-color="#fff" stop-opacity=".18"/><stop offset="1" stop-color="#fff" stop-opacity=".02"/></radialGradient>
{defs}
    <style>
      {style}
      @media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
    </style>
  </defs>
{body}
</svg>
"""


def text(x, y, s, size, fill=DEEP, weight=400, anchor="start", opacity=1, spacing=0, kind="sans", extra=""):
    family = AERO if kind == "sans" else "font-family=\"'JetBrains Mono','SF Mono',Menlo,Consolas,monospace\""
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    op = f' opacity="{opacity}"' if opacity != 1 else ""
    return f'<text x="{x}" y="{y}" {family} font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{ls}{op} {extra}>{escape(str(s))}</text>'


def rising(w, h, n, salt, lo=6, hi=34):
    """burbujas que suben desde el fondo y se desvanecen, cada una a su ritmo."""
    out = []
    for i in range(n):
        r = lo + (hi - lo) * rnd(i, salt) ** 2
        x = 20 + rnd(i, salt + 1) * (w - 40)
        dur = 8 + rnd(i, salt + 2) * 9
        out.append(f'<g class="rise" style="animation-duration:{dur:.1f}s;animation-delay:-{rnd(i, salt + 3) * dur:.1f}s;--h:{h + 80}px">'
                   f'<circle cx="{x:.0f}" cy="{h + 40}" r="{r:.0f}" fill="url(#bub)" stroke="#fff" stroke-opacity=".7" stroke-width="1.3"/>'
                   f'<ellipse cx="{x - r * .3:.0f}" cy="{h + 40 - r * .45:.0f}" rx="{r * .35:.0f}" ry="{r * .18:.0f}" fill="#fff" fill-opacity=".8"/></g>')
    return "".join(out)


RISE_CSS = (".rise{animation:rise 10s linear infinite}\n"
            "      @keyframes rise{0%{transform:translateY(0);opacity:0}10%{opacity:1}85%{opacity:1}100%{transform:translateY(calc(var(--h) * -1));opacity:0}}")


# ---------------------------------------------------------------- la escena
def hero():
    W, H, HZ = 1200, 600, 318
    name = lambda y, extra="": text(600, y, "Kisnner Obando.", 132, "url(#ink)", 800, "middle", spacing=-5, extra=extra)
    defs = f"""    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1f9cf0"/><stop offset=".55" stop-color="#7fd6ff"/><stop offset="1" stop-color="#eefcff"/></linearGradient>
    <linearGradient id="sea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9cecf5"/><stop offset=".25" stop-color="#2cc6d6"/><stop offset="1" stop-color="#0a5fb0"/></linearGradient>
    <radialGradient id="sun" cx="900" cy="150" r="520" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#fff" stop-opacity="1"/><stop offset=".12" stop-color="#fff" stop-opacity=".7"/><stop offset=".4" stop-color="#fff" stop-opacity=".18"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
    <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".55"/><stop offset=".6" stop-color="#fff" stop-opacity="0"/></linearGradient>
    <mask id="reflect" maskUnits="userSpaceOnUse" x="0" y="{HZ}" width="{W}" height="200"><rect x="0" y="{HZ}" width="{W}" height="200" fill="url(#fade)"/></mask>
    <filter id="blur40" x="-50%" y="-300%" width="200%" height="700%"><feGaussianBlur stdDeviation="22"/></filter>
    <filter id="caustic" x="0" y="0" width="100%" height="100%">
      <feTurbulence type="fractalNoise" baseFrequency=".006 .045" numOctaves="2" seed="4" result="n"><animate attributeName="baseFrequency" values=".006 .045;.009 .05;.006 .045" dur="14s" repeatCount="indefinite"/></feTurbulence>
      <feColorMatrix in="n" type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  11 0 0 0 -6.1"/>
    </filter>
    <filter id="ripple" x="-5%" y="-5%" width="110%" height="110%">
      <feTurbulence type="turbulence" baseFrequency=".004 .09" numOctaves="1" seed="2" result="w"><animate attributeName="baseFrequency" values=".004 .09;.007 .12;.004 .09" dur="9s" repeatCount="indefinite"/></feTurbulence>
      <feDisplacementMap in="SourceGraphic" in2="w" scale="22" xChannelSelector="R" yChannelSelector="G"/>
    </filter>
    <radialGradient id="orb" cx=".5" cy=".85" r=".9"><stop offset="0" stop-color="#eaffc9"/><stop offset=".5" stop-color="#5cd34a"/><stop offset="1" stop-color="#1f8a35"/></radialGradient>
    <linearGradient id="hl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".92"/><stop offset="1" stop-color="#fff" stop-opacity=".08"/></linearGradient>
    <filter id="ts" x="-5%" y="-10%" width="110%" height="140%"><feDropShadow dx="0" dy="1.5" stdDeviation=".8" flood-color="#0a4a1f" flood-opacity=".7"/></filter>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="34"/></clipPath>
    <clipPath id="seaclip"><rect y="{HZ}" width="{W}" height="{H - HZ}"/></clipPath>"""
    clouds = "".join(
        f'<g class="cloud" style="animation-duration:{70 + i * 23}s;animation-delay:-{i * 29}s"><ellipse cx="{200 + i * 330}" cy="{70 + (i % 2) * 60}" rx="{150 + i * 20}" ry="{22 + i * 4}" fill="#fff" fill-opacity=".7" filter="url(#blur40)"/></g>'
        for i in range(4))
    rays = "".join(f'<polygon points="900,150 {x},{HZ} {x + 70},{HZ}" fill="#fff" fill-opacity=".07"/>' for x in (180, 380, 560, 760, 1010))
    flare = "".join(f'<circle cx="{900 - 150 * k:.0f}" cy="{150 + 55 * k:.0f}" r="{r}" fill="none" stroke="#fff" stroke-opacity=".45" stroke-width="{w}"/>'
                    for k, r, w in ((1, 18, 3), (1.9, 34, 2), (3.1, 12, 4), (4.2, 46, 1.5)))
    cta_y = 520
    ring = "".join(f'<circle cx="600" cy="{cta_y}" r="40" fill="none" stroke="#fff" stroke-width="2"><animate attributeName="r" values="40;100" dur="3s" begin="{d}s" repeatCount="indefinite"/>'
                   f'<animate attributeName="stroke-opacity" values=".8;0" dur="3s" begin="{d}s" repeatCount="indefinite"/></circle>' for d in (0, 1, 2))
    body = f"""  <g clip-path="url(#frame)">
  <rect width="{W}" height="{H}" fill="url(#sky)"/>
  <rect width="{W}" height="{HZ}" fill="url(#sun)"/>
  {clouds}
  {rays}
  {flare}
  <rect y="{HZ}" width="{W}" height="{H - HZ}" fill="url(#sea)"/>
  <g clip-path="url(#seaclip)"><rect y="{HZ}" width="{W}" height="{H - HZ}" fill="#fff" filter="url(#caustic)" opacity=".5" class="shimmer"/>
    <ellipse cx="900" cy="{HZ + 40}" rx="150" ry="14" fill="#fff" opacity=".7" class="glint"/>
    <ellipse cx="900" cy="{HZ + 90}" rx="90" ry="9" fill="#fff" opacity=".4" class="glint" style="animation-delay:-1.3s"/></g>
  <rect y="{HZ - 3}" width="{W}" height="6" fill="#fff" opacity=".7" filter="url(#blur40)"/>
  <g mask="url(#reflect)"><g transform="translate(0 {2 * HZ}) scale(1 -1)" filter="url(#ripple)" opacity=".9">{name(HZ - 28)}</g></g>
  {name(HZ - 28, 'filter="url(#emboss)"')}
  {text(600, HZ - 190, "MANAGUA, NICARAGUA · 12.13°N 86.25°W", 15, MID, 600, "middle", spacing=3.4, kind="mono")}
  {rising(W, H, 18, 7)}
  <g class="roles">
    <rect x="150" y="408" width="900" height="44" rx="22" fill="#0a5fa5" fill-opacity=".38" stroke="#fff" stroke-opacity=".7"/>
    {text(600, 437, "apps nativas para apple  ·  backend transaccional  ·  ingeniería inversa  ·  open source", 19, "#ffffff", 700, "middle", extra='filter="url(#ts)"')}
  </g>
  {ring}
  <g class="cta">
    <rect x="450" y="{cta_y - 30}" width="300" height="60" rx="30" fill="url(#orb)" stroke="#1f7a2e" stroke-width="2"/>
    <rect x="456" y="{cta_y - 26}" width="288" height="28" rx="14" fill="url(#hl)"/>
    <rect x="452.5" y="{cta_y - 27.5}" width="295" height="55" rx="27.5" fill="none" stroke="#fff" stroke-opacity=".6"/>
    <path d="M498 {cta_y - 9}v18h8l11 9V{cta_y - 18}l-11 9z" fill="#fff" filter="url(#ts)"/>
    <path d="M526 {cta_y - 8}a12 12 0 0 1 0 16M533 {cta_y - 15}a22 22 0 0 1 0 30" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" filter="url(#ts)"/>
    {text(642, cta_y + 8, "abrir con sonido", 22, "#fff", 800, "middle", extra='filter="url(#ts)"')}
  </g>
  </g>
  <rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="33" fill="none" stroke="#fff" stroke-opacity=".9" stroke-width="1.5"/>"""
    style = (RISE_CSS + "\n      .cloud{animation:drift 90s linear infinite}\n      @keyframes drift{from{transform:translateX(-200px)}to{transform:translateX(1300px)}}"
             "\n      .glint{animation:glint 3.6s ease-in-out infinite}\n      @keyframes glint{50%{opacity:.15;transform:scaleX(.8);transform-origin:900px 0}}"
             "\n      .cta{animation:cta 3.2s ease-in-out infinite;transform-box:fill-box;transform-origin:center}\n      @keyframes cta{50%{transform:scale(1.04)}}"
             "\n      .roles{animation:rise2 1.4s cubic-bezier(.2,.8,.2,1) backwards .3s}\n      @keyframes rise2{from{opacity:0;transform:translateY(14px)}}")
    return svg(W, H, "Kisnner Obando", "Apps nativas para Apple, backend transaccional, ingeniería inversa y open source. Managua, Nicaragua. Abre un escritorio de vidrio con sonido.",
               body, style, defs)


# ---------------------------------------------------------------- la marea
def tide(d):
    W, H = 1200, 260
    first = datetime.strptime(d["first"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    skip = max(0, int((datetime(2026, 5, 31, tzinfo=timezone.utc) - first).days // 7))
    weeks = d["weeks"][skip:]
    start = datetime.fromtimestamp(first.timestamp() + skip * 7 * 86400, timezone.utc)
    peak = max(weeks) or 1
    left, right, base, top = 700, 1150, 214, 40
    n = len(weeks)
    X = lambda i: left + (right - left) * i / (n - 1)
    Y = lambda i: base - (base - top) * (weeks[i] / peak) ** .5
    surface = f"M{X(0):.1f} {Y(0):.1f}"
    for i in range(1, n):
        mx = (X(i - 1) + X(i)) / 2
        surface += f" C{mx:.1f} {Y(i - 1):.1f} {mx:.1f} {Y(i):.1f} {X(i):.1f} {Y(i):.1f}"
    shape = f"M{X(0):.1f} {base} L" + surface[1:] + f" L{X(n - 1):.1f} {base} Z"
    wave = "M0 0 " + "".join(f"Q{x + 40} {-9} {x + 80} 0 T{x + 160} 0 " for x in range(0, 1760, 160))
    months = "".join(text(X(i) - 6, H - 16, MESES[m.month - 1], 12, MID, 500, kind="mono", opacity=.9)
                     for i in range(n) for m in [datetime.fromtimestamp(start.timestamp() + i * 7 * 86400, timezone.utc)] if m.day <= 7)
    defs = f"""    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#27a4ee"/><stop offset=".6" stop-color="#8bdcff"/><stop offset="1" stop-color="#e4fbff"/></linearGradient>
    <linearGradient id="water" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8ef0ff" stop-opacity=".95"/><stop offset=".5" stop-color="#2aa9ee" stop-opacity=".92"/><stop offset="1" stop-color="#0a5fa5"/></linearGradient>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="30"/></clipPath>
    <clipPath id="body"><path d="{shape}"/></clipPath>
    <clipPath id="odo"><rect x="40" y="86" width="280" height="96"/></clipPath>"""
    digits = f"{d['total']:,}"
    cx, odometer = 56, ""
    for k, ch in enumerate(digits):
        if not ch.isdigit():
            odometer += text(cx, 168, ch, 84, "url(#ink)", 800, extra='filter="url(#emboss)"'); cx += 24; continue
        col = "".join(text(cx, 168 + j * 84, j, 84, "url(#ink)", 800, extra='filter="url(#emboss)"') for j in range(10))
        odometer += f'<g clip-path="url(#odo)"><g class="roll" style="transform:translateY(-{int(ch) * 84}px);animation-delay:{.2 + k * .12:.2f}s">{col}</g></g>'
        cx += 50
    body = f"""  <g clip-path="url(#frame)">
  <rect width="{W}" height="{H}" fill="url(#sky)"/>
  {rising(W, H, 8, 31, 5, 22)}
  <path d="{shape}" fill="url(#water)"/>
  <g clip-path="url(#body)">
    <g class="swell"><path d="{wave}" transform="translate(-160 {base - 60})" fill="none" stroke="#fff" stroke-opacity=".5" stroke-width="2"/></g>
    <g class="swell slow"><path d="{wave}" transform="translate(-160 {base - 110})" fill="none" stroke="#fff" stroke-opacity=".3" stroke-width="2"/></g>
  </g>
  <path d="{surface}" fill="none" stroke="#fff" stroke-width="2.5" stroke-opacity=".95"/>
  <circle cx="{X(n - 1):.1f}" cy="{Y(n - 1) - 12:.1f}" r="5" fill="{LIME}" stroke="#fff" stroke-width="2" class="now"/>
  {text(48, 58, "CONTRIBUCIONES · ÚLTIMO AÑO", 13, MID, 700, spacing=2.6)}
  {odometer}
  {text(52, 206, f"racha de {d['streak']} días  ·  {d['merged']} pull requests en proyectos ajenos", 14, DEEP, 500, kind="mono", opacity=.85)}
  {months}
  </g>
  <rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="29" fill="none" stroke="#fff" stroke-opacity=".9" stroke-width="1.5"/>"""
    style = (RISE_CSS + "\n      .swell{animation:swell 7s linear infinite}\n      .swell.slow{animation-duration:11s;animation-direction:reverse}\n      @keyframes swell{to{transform:translateX(160px)}}"
             "\n      .roll{animation:roll 1.8s cubic-bezier(.16,.84,.24,1) backwards}\n      @keyframes roll{from{transform:translateY(0)}}"
             "\n      .now{animation:now 1.6s ease-in-out infinite}\n      @keyframes now{50%{opacity:.25}}")
    return svg(W, H, "Contribuciones", f"{d['total']} contribuciones en el último año como nivel de agua semana a semana. Racha de {d['streak']} días. {d['merged']} pull requests en proyectos ajenos.",
               body, style, defs)


# ---------------------------------------------------------------- orbes
ORBS = {
    "sitio": ("#eaffc9", "#5cd34a", "#1f8a35", '<path d="M32 38v20h13l16 13V25L45 38z" fill="#fff"/><path d="M69 40a14 14 0 0 1 0 18M75 32a25 25 0 0 1 0 34" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round"/>'),
    "linkedin": ("#d6f6ff", "#2ba9ee", "#0a5fa5", None),
    "github": ("#cfe0ff", "#3f6fe0", "#14308f", '<path d="M40 36L24 50l16 14M60 36l16 14-16 14M54 30L46 70" fill="none" stroke="#fff" stroke-width="5.5" stroke-linecap="round" stroke-linejoin="round"/>'),
    "correo": ("#ffe9d0", "#ff9a4a", "#c2410c", '<rect x="24" y="33" width="52" height="36" rx="6" fill="none" stroke="#fff" stroke-width="5"/><path d="M26 38l24 18 24-18" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'),
}


def orb(name, label, index):
    c1, c2, c3, glyph = ORBS[name]
    glyph = glyph or f'<text x="50" y="66" {AERO} font-size="40" font-weight="800" fill="#fff" text-anchor="middle" filter="url(#ts)">in</text>'
    defs = f"""    <radialGradient id="o" cx=".5" cy=".88" r=".9"><stop offset="0" stop-color="{c1}"/><stop offset=".5" stop-color="{c2}"/><stop offset="1" stop-color="{c3}"/></radialGradient>
    <linearGradient id="hl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".95"/><stop offset="1" stop-color="#fff" stop-opacity=".06"/></linearGradient>
    <filter id="ts" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="1.5" stdDeviation="1" flood-color="#000" flood-opacity=".4"/></filter>
    <radialGradient id="sh" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#05508a" stop-opacity=".35"/><stop offset="1" stop-color="#05508a" stop-opacity="0"/></radialGradient>"""
    body = f"""  <ellipse cx="60" cy="132" rx="38" ry="7" fill="url(#sh)" class="shade"/>
  <g class="float" style="animation-delay:-{index * .9}s">
    <g transform="translate(10 6)">
      <circle cx="50" cy="50" r="46" fill="url(#o)" stroke="#fff" stroke-width="2.5"/>
      <g filter="url(#ts)">{glyph if 'filter' in glyph else glyph}</g>
      <ellipse cx="50" cy="27" rx="33" ry="19" fill="url(#hl)"/>
      <circle cx="50" cy="50" r="44" fill="none" stroke="#fff" stroke-opacity=".35"/>
    </g>
  </g>
  <rect x="{60 - len(label) * 4.6 - 14:.0f}" y="132" width="{len(label) * 9.2 + 28:.0f}" height="24" rx="12" fill="#fff" fill-opacity=".92"/>
  {text(60, 149, label, 14, DEEP, 800, "middle")}"""
    style = (".float{animation:float 4.2s ease-in-out infinite}\n      @keyframes float{50%{transform:translateY(-7px)}}\n"
             "      .shade{animation:shade 4.2s ease-in-out infinite;transform-box:fill-box;transform-origin:center}\n      @keyframes shade{50%{transform:scale(.82);opacity:.7}}")
    return svg(120, 160, label, f"enlace: {label}", body, style, defs)


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
    DOCS.mkdir(exist_ok=True)
    (DOCS / "snapshot.json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")  # la web lo lee en vivo
    for old in ASSETS.glob("*.svg"):
        old.unlink()
    write("hero.svg", hero())
    write("tide.svg", tide(data))
    for index, (name, label) in enumerate((("sitio", "con sonido"), ("linkedin", "linkedin"), ("github", "github"), ("correo", "correo"))):
        write(f"orb-{name}.svg", orb(name, label, index))
    print("listo:", len(list(ASSETS.glob("*.svg"))), "svg")


if __name__ == "__main__":
    main()
