"""genera los svg animados del perfil con datos reales de github. solo biblioteca estándar.

uso:  python scripts/generate.py             consulta github (GITHUB_TOKEN o la sesión de gh)
      python scripts/generate.py --offline   reutiliza data/snapshot.json
"""

import json
import math
import os
import subprocess
import sys
import urllib.request
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SNAPSHOT = ROOT / "data" / "snapshot.json"
LOGIN = "kisnner26"
ICONS = json.loads((Path(__file__).parent / "icons.json").read_text(encoding="utf-8"))

# paleta risografía, la misma del banner y las tarjetas
INK, PAPER, PAPER2 = "#1a1208", "#f3ead8", "#fbf6ea"
BLUE, ORANGE, PINK, TEAL, GOLD, PURPLE, RED = "#3b46a8", "#f0683a", "#e8527c", "#2a9d8f", "#f2b632", "#7a64a8", "#d6362f"
ACCENTS = [BLUE, ORANGE, PINK, TEAL, GOLD, PURPLE]
SERIF = "font-family=\"Georgia,'Times New Roman',serif\""
MONO = "font-family=\"'SF Mono',Menlo,Consolas,monospace\""

OSS = [("radareorg", "radare2", "https://github.com/radareorg/radare2/pulls?q=is%3Apr+author%3A" + LOGIN),
       ("rizinorg", "rizin", "https://github.com/rizinorg/rizin/pulls?q=is%3Apr+author%3A" + LOGIN),
       ("apple", "swift-nio", "https://github.com/apple/swift-nio/pulls?q=is%3Apr+author%3A" + LOGIN),
       ("apple", "swift-argument-parser", "https://github.com/apple/swift-argument-parser/pulls?q=is%3Apr+author%3A" + LOGIN)]
PROJECTS = [("lumora", "https://github.com/kisnner26/lumora", ORANGE), ("anaquel", "https://github.com/kisnner26/inventario-saas", PINK),
            ("claude-pet", "https://github.com/kisnner26/claude-pet", PURPLE), ("nexo", "https://github.com/kisnner26/nexo", BLUE),
            ("2-player-web", "https://github.com/kisnner26/2-player-web", TEAL)]
LANG_SLUG = {"JavaScript": "javascript", "Swift": "swift", "TypeScript": "typescript", "PHP": "php", "HTML": "html5",
             "Python": "python", "CSS": "css", "Kotlin": "kotlin", "C++": "cplusplus"}
STACK = [("Swift", "swift"), ("Xcode", "xcode"), ("Apple", "apple"), ("PHP", "php"), ("Laravel", "laravel"),
         ("JavaScript", "javascript"), ("TypeScript", "typescript"), ("Next.js", "nextdotjs"), ("Python", "python"),
         ("C#", None), ("Kotlin", "kotlin"), ("C++", "cplusplus"), ("MySQL", "mysql"), ("Redis", "redis"),
         ("Git", "git"), ("GitHub", "github")]


# ---------------------------------------------------------------- datos
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


def rest(path):
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request = urllib.request.Request("https://api.github.com/" + path, headers={
            "Authorization": f"bearer {token}", "User-Agent": "profile-generator", "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    return json.loads(subprocess.run(["gh", "api", path], check=True, capture_output=True, text=True).stdout)


QUERY = """query($login:String!){ user(login:$login){ followers{totalCount}
 repositories(ownerAffiliations:OWNER,isFork:false,privacy:PUBLIC,first:100){ totalCount nodes{ name languages(first:8,orderBy:{field:SIZE,direction:DESC}){ edges{ size node{name} } } } }
 contributionsCollection{ totalCommitContributions totalPullRequestContributions totalIssueContributions totalPullRequestReviewContributions
  contributionCalendar{ totalContributions weeks{ contributionDays{ date contributionCount } } } } } }"""


def collect():
    user = graphql(QUERY, {"login": LOGIN})["user"]
    collection = user["contributionsCollection"]
    languages = Counter()
    for repo in user["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            languages[edge["node"]["name"]] += edge["size"]
    oss = []
    for owner, name, link in OSS:
        found = rest(f"search/issues?q=repo:{owner}/{name}+author:{LOGIN}+type:pr&per_page=100&sort=updated")["items"]
        merged = sum(1 for item in found if item.get("pull_request", {}).get("merged_at"))
        opened = sum(1 for item in found if item["state"] == "open")
        latest = found[0]["title"] if found else ""
        oss.append(dict(owner=owner, name=name, link=link, merged=merged, open=opened, total=len(found), latest=latest))
    external = rest(f"search/issues?q=author:{LOGIN}+type:pr+is:merged+-user:{LOGIN}&per_page=100")["items"]
    projects = sorted({item["repository_url"].rsplit("/", 1)[-1] for item in external})
    days = [day for week in collection["contributionCalendar"]["weeks"] for day in week["contributionDays"]]
    return dict(
        generated=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        total=collection["contributionCalendar"]["totalContributions"],
        commits=collection["totalCommitContributions"], prs=collection["totalPullRequestContributions"],
        issues=collection["totalIssueContributions"], reviews=collection["totalPullRequestReviewContributions"],
        repos=user["repositories"]["totalCount"], followers=user["followers"]["totalCount"],
        weeks=[[day["contributionCount"] for day in week["contributionDays"]] for week in collection["contributionCalendar"]["weeks"]],
        dates=[[day["date"] for day in week["contributionDays"]] for week in collection["contributionCalendar"]["weeks"]],
        languages=languages.most_common(8), oss=oss,
        merged_external=len(external), merged_projects=projects, last_day=days[-1]["date"] if days else "")


def streaks(weeks):
    counts = [c for week in weeks for c in week]
    best = run = 0
    for c in counts:
        run = run + 1 if c else 0
        best = max(best, run)
    current, tail = 0, list(reversed(counts))
    if tail and tail[0] == 0:
        tail = tail[1:]  # hoy puede estar en cero sin romper la racha
    for c in tail:
        if not c:
            break
        current += 1
    return current, best


# ---------------------------------------------------------------- piezas visuales
def svg(width, height, title, desc, body, extra_style=""):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="t d">
  <title id="t">{escape(title)}</title>
  <desc id="d">{escape(desc)}</desc>
  <defs>
    <filter id="grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="4"/><feColorMatrix values="0 0 0 0 .16  0 0 0 0 .1  0 0 0 0 .04  0 0 0 1.1 -.42"/></filter>
    <pattern id="dots" width="9" height="9" patternUnits="userSpaceOnUse"><circle cx="4.5" cy="4.5" r="1.8" fill="{INK}" fill-opacity=".16"/></pattern>
    <style>
      .m{{mix-blend-mode:multiply}}
      .pop{{transform-box:fill-box;transform-origin:center;animation:pop .6s cubic-bezier(.2,.9,.3,1.3) backwards}}
      @keyframes pop{{0%{{opacity:0;transform:scale(1.5) rotate(-5deg)}}100%{{opacity:1;transform:none}}}}
      .rise{{animation:rise .7s ease-out backwards}}
      @keyframes rise{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
      .bob{{animation:bob 4s ease-in-out infinite}}
      @keyframes bob{{50%{{transform:translateY(-5px)}}}}
      .tw{{animation:tw 2.6s ease-in-out infinite}}
      @keyframes tw{{50%{{opacity:.25}}}}
      {extra_style}
      @media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
    </style>
  </defs>
{body}
</svg>
"""


def card(x, y, w, h, shadow, fill=PAPER, rot=0, tape=True, tape_x=None):
    cx, cy = x + w / 2, y + h / 2
    tx = tape_x if tape_x is not None else x + w * 0.5 - 40
    tape_svg = (f'<rect x="{tx}" y="{y - 10}" width="80" height="24" fill="{GOLD}" opacity=".92" transform="rotate(-2 {tx + 40} {y})"/>'
                if tape else "")
    return (f'<g transform="rotate({rot} {cx} {cy})">'
            f'<rect x="{x + 8}" y="{y + 8}" width="{w}" height="{h}" rx="14" fill="{shadow}"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}" stroke="{INK}" stroke-width="3"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="url(#dots)" opacity=".6"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" filter="url(#grain)" class="m" opacity=".22"/>'
            f'{tape_svg}</g>')


def text(x, y, s, size, fill=INK, kind="serif", weight=700, anchor="start", italic=True, spacing=0, extra=""):
    family = SERIF if kind == "serif" else MONO
    style = ' font-style="italic"' if (kind == "serif" and italic) else ""
    letter = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x}" y="{y}" {family} font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}"{style}{letter} {extra}>{escape(str(s))}</text>')


def logo(slug, x, y, size, fill=INK):
    icon = ICONS[slug]
    scale = size / 24
    return f'<g transform="translate({x} {y}) scale({scale})" fill="{fill}"><path d="{icon["d"]}"/></g>'


def csharp(x, y, size, fill=INK):
    s = size / 24
    return (f'<g transform="translate({x} {y}) scale({s})" fill="none" stroke="{fill}" stroke-width="2.2" stroke-linecap="round">'
            f'<path d="M12 2 21 7v10l-9 5-9-5V7z" stroke-linejoin="round"/><path d="M15 9.5a4 4 0 1 0 0 5"/>'
            f'<path d="M16 11v2M18 11v2M15 11.6h4M15 12.8h4" stroke-width="1.1"/></g>')


# ---------------------------------------------------------------- cada archivo
def header(name, number, color):
    label = name.replace("-", " ")
    w = 96 + int(len(label) * 17.5)
    body = f"""  <g class="rise">
    <rect x="22" y="22" width="{w}" height="46" rx="8" fill="{color}"/>
    <rect x="14" y="14" width="{w}" height="46" rx="8" fill="{PAPER2}" stroke="{INK}" stroke-width="3"/>
    {text(34, 46, number, 17, color, "mono", 700, spacing=2)}
    {text(78, 48, label, 29, INK)}
    <path d="M{w + 40} 40 C {w + 190} 14, {w + 290} 64, {w + 450} 38 S 940 18, 1186 40" fill="none" stroke="{INK}" stroke-width="3.5" stroke-linecap="round" stroke-dasharray="1000" stroke-dashoffset="1000" style="animation:draw 1.6s ease-out .3s forwards"/>
    <circle cx="1186" cy="40" r="6" fill="{color}" class="tw"/>
  </g>"""
    style = "@keyframes draw{to{stroke-dashoffset:0}}"
    return svg(1200, 84, label, f"encabezado de sección: {label}", body, style)


def about():
    lines = ["estudio ingeniería en sistemas en la UAM y construyo",
             "apps nativas para macOS, iOS y watchOS, backend",
             "transaccional y herramientas web."]
    body = [card(24, 30, 760, 236, BLUE, rot=-.4)]
    for i, line in enumerate(lines):
        body.append(f'<g class="rise" style="animation-delay:{.2 + i * .18}s">{text(56, 92 + i * 38, line, 28, INK, weight=400)}</g>')
    body.append(f'<g class="rise" style="animation-delay:.9s">{text(56, 98 + 3 * 38, "contribuyo a open source: radare2, rizin y Apple.", 28, ORANGE)}</g>')
    body.append(text(56, 246, "i study information systems engineering at UAM, build native Apple apps", 14, INK, "mono", 400, extra='opacity=".62"'))
    # sello y chips a la derecha
    chips = [("UAM", BLUE), ("managua, ni", ORANGE), ("macOS", PINK), ("iOS", TEAL), ("watchOS", PURPLE), ("backend", GOLD), ("ing. inversa", RED)]
    cx, cy = 830, 54
    for i, (label, color) in enumerate(chips):
        w = 30 + len(label) * 11
        if cx + w > 1176:
            cx, cy = 830, cy + 56
        body.append(f'<g class="pop" style="animation-delay:{.4 + i * .1}s"><rect x="{cx + 4}" y="{cy + 4}" width="{w}" height="40" rx="20" fill="{color}"/>'
                    f'<rect x="{cx}" y="{cy}" width="{w}" height="40" rx="20" fill="{PAPER2}" stroke="{INK}" stroke-width="3"/>'
                    f'{text(cx + w / 2, cy + 26, label, 15, INK, "mono", 700, "middle")}</g>')
        cx += w + 18
    body.append(f'<g class="bob"><circle cx="1010" cy="238" r="22" fill="{ORANGE}"/><circle cx="1010" cy="238" r="22" fill="url(#dots)"/></g>')
    return svg(1200, 300, "sobre mí", "estudio ingeniería en sistemas, apps nativas de Apple, backend transaccional y open source", "\n".join(body))


def stats(d):
    current, best = streaks(d["weeks"])
    weekly = [sum(w) for w in d["weeks"]]
    body = [card(24, 28, 450, 270, ORANGE, rot=-.3)]
    body.append(text(52, 78, "contribuciones", 15, INK, "mono", 700, spacing=3, extra='opacity=".6"'))
    body.append(f'<g class="pop">{text(50, 168, d["total"], 96, BLUE)}</g>')
    body.append(text(54, 198, "en los últimos 12 meses", 17, INK, "mono", 400, extra='opacity=".7"'))
    top = max(weekly) or 1
    pts = [(58 + i * (392 / max(len(weekly) - 1, 1)), 278 - (v / top) * 58) for i, v in enumerate(weekly)]
    path = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    body.append(f'<path d="{path}" fill="none" stroke="{ORANGE}" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round" stroke-dasharray="1400" stroke-dashoffset="1400" style="animation:draw 2.4s ease-out .5s forwards"/>')
    peak = pts[weekly.index(max(weekly))]
    body.append(f'<circle cx="{peak[0]:.1f}" cy="{peak[1]:.1f}" r="6" fill="{PINK}" stroke="{INK}" stroke-width="2.5" class="tw"/>')
    small = [("commits", d["commits"], BLUE), ("pull requests", d["prs"], PINK), ("issues", d["issues"], TEAL),
             ("repos públicos", d["repos"], PURPLE), ("racha actual", f"{current} d", ORANGE), ("mejor racha", f"{best} d", GOLD)]
    for i, (label, value, color) in enumerate(small):
        col, row = i % 3, i // 3
        x, y = 500 + col * 232, 28 + row * 142
        body.append(f'<g class="rise" style="animation-delay:{.15 + i * .1}s">{card(x, y, 214, 124, color, rot=(-1, .6, -.4)[col], tape=False)}')
        body.append(f'<g class="pop" style="animation-delay:{.3 + i * .1}s">{text(x + 22, y + 74, value, 54, color if color != GOLD else INK)}</g>')
        body.append(text(x + 24, y + 104, label, 14, INK, "mono", 700, spacing=1.5, extra='opacity=".65"'))
        body.append("</g>")
    return svg(1200, 330, "contribuciones en GitHub", f"{d['total']} contribuciones en 12 meses: {d['commits']} commits, {d['prs']} pull requests, {d['issues']} issues; racha actual {current} días, mejor racha {best}",
               "\n".join(body), "@keyframes draw{to{stroke-dashoffset:0}}")


def heatmap(d):
    counts = [c for w in d["weeks"] for c in w if c]
    counts.sort()
    q = [counts[int(len(counts) * f)] for f in (.25, .5, .75)] if counts else [1, 2, 3]
    palette = ["#e4d8bf", GOLD, ORANGE, PINK, BLUE]

    def level(c):
        return 0 if c == 0 else 1 if c <= q[0] else 2 if c <= q[1] else 3 if c <= q[2] else 4

    x0, y0, pitch, size = 78, 96, 20, 16
    body = [card(24, 28, 1152, 234, TEAL, rot=0)]
    body.append(text(52, 74, "mapa de calor · un cuadro por día", 15, INK, "mono", 700, spacing=2, extra='opacity=".6"'))
    months = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    seen = None
    for i, week in enumerate(d["dates"]):
        month = int(week[0][5:7]) if week else 0
        if month != seen:
            seen = month
            body.append(text(x0 + i * pitch, 90, months[month - 1], 12, INK, "mono", 400, extra='opacity=".6"'))
    for r, label in ((1, "lun"), (3, "mié"), (5, "vie")):
        body.append(text(52, y0 + r * pitch + 13, label, 11, INK, "mono", 400, extra='opacity=".5"'))
    for i, (week, dates) in enumerate(zip(d["weeks"], d["dates"])):
        for r, (c, day) in enumerate(zip(week, dates)):
            body.append(f'<rect class="pop" x="{x0 + i * pitch}" y="{y0 + r * pitch}" width="{size}" height="{size}" rx="4" fill="{palette[level(c)]}" '
                        f'stroke="{INK}" stroke-opacity=".35" stroke-width="1" style="animation-delay:{i * 0.035:.2f}s"><title>{day}: {c}</title></rect>')
    body.append(f'<rect x="{x0 - 8}" y="{y0 - 8}" width="18" height="{7 * pitch + 12}" fill="{PAPER2}" opacity=".6" class="m" style="animation:scan 9s linear 3s infinite"/>')
    lx = 1176 - 20 - 5 * 26 - 110
    body.append(text(lx, 244, "menos", 12, INK, "mono", 400, extra='opacity=".6"'))
    for i, color in enumerate(palette):
        body.append(f'<rect x="{lx + 54 + i * 26}" y="232" width="16" height="16" rx="4" fill="{color}" stroke="{INK}" stroke-opacity=".35"/>')
    body.append(text(lx + 54 + 5 * 26 + 6, 244, "más", 12, INK, "mono", 400, extra='opacity=".6"'))
    style = f"@keyframes scan{{from{{transform:translateX(0)}}to{{transform:translateX({53 * pitch}px)}}}} .m{{mix-blend-mode:multiply}}"
    return svg(1200, 290, "mapa de contribuciones", "calendario de contribuciones de los últimos 12 meses, un cuadro por día", "\n".join(body), style)


def languages(d):
    top = d["languages"][:6]
    total = sum(size for _, size in top) or 1
    body = [card(24, 28, 1152, 224, PURPLE)]
    body.append(text(52, 74, "lenguajes · por tamaño de código en mis repos públicos", 15, INK, "mono", 700, spacing=2, extra='opacity=".6"'))
    x = 54
    width = 1092
    body.append(f'<rect x="{x}" y="94" width="{width}" height="40" rx="10" fill="{PAPER2}" stroke="{INK}" stroke-width="3"/>')
    cursor = x
    for i, (name, size) in enumerate(top):
        w = width * size / total
        color = ACCENTS[i % len(ACCENTS)]
        body.append(f'<rect class="grow" x="{cursor:.1f}" y="98" width="{max(w - 3, 2):.1f}" height="32" rx="7" fill="{color}" style="animation-delay:{i * .18}s"/>')
        cursor += w
    for i, (name, size) in enumerate(top):
        col, row = i % 3, i // 3
        lx, ly = 58 + col * 372, 170 + row * 44
        color = ACCENTS[i % len(ACCENTS)]
        body.append(f'<g class="rise" style="animation-delay:{.5 + i * .1}s"><rect x="{lx}" y="{ly - 20}" width="30" height="30" rx="8" fill="{color}"/>')
        slug = LANG_SLUG.get(name)
        if slug:
            body.append(logo(slug, lx + 6, ly - 14, 18, PAPER2))
        elif name == "C#":
            body.append(csharp(lx + 5, ly - 15, 20, PAPER2))
        body.append(text(lx + 44, ly + 2, name, 22, INK))
        body.append(text(lx + 330, ly + 2, f"{size * 100 / total:.1f}%", 15, INK, "mono", 700, "end", extra='opacity=".6"'))
        body.append("</g>")
    style = ".grow{transform-box:fill-box;transform-origin:left;animation:grow 1s cubic-bezier(.2,.8,.2,1) backwards}@keyframes grow{from{transform:scaleX(0)}}"
    return svg(1200, 280, "lenguajes", "lenguajes más usados en mis repositorios públicos: " + ", ".join(n for n, _ in top), "\n".join(body), style)


def stack():
    body = []
    tile, gap, x0, y0 = 120, 16, 64, 36
    for i, (name, slug) in enumerate(STACK):
        col, row = i % 8, i // 8
        x, y = x0 + col * (tile + gap), y0 + row * (tile + gap + 22)
        color = ACCENTS[i % len(ACCENTS)]
        rot = (-2.2, 1.6, -1.2, 2.4)[i % 4]
        delay = (i % 8) * .25 + row * .4
        body.append(f'<g class="rise" style="animation-delay:{i * .06:.2f}s"><g class="bob" style="animation-delay:{delay}s" transform="rotate({rot} {x + tile / 2} {y + tile / 2})">'
                    f'<rect x="{x + 7}" y="{y + 7}" width="{tile}" height="{tile}" rx="16" fill="{color}"/>'
                    f'<rect x="{x}" y="{y}" width="{tile}" height="{tile}" rx="16" fill="{PAPER}" stroke="{INK}" stroke-width="3"/>'
                    f'<rect x="{x}" y="{y}" width="{tile}" height="{tile}" rx="16" fill="url(#dots)" opacity=".7"/>')
        if slug:
            body.append(f'<g class="m">{logo(slug, x + 28 + 3, y + 22 + 3, 64, color)}</g>{logo(slug, x + 28, y + 22, 64, INK)}')
        else:
            body.append(f'<g class="m">{csharp(x + 31, y + 25, 64, color)}</g>{csharp(x + 28, y + 22, 64, INK)}')
        body.append(text(x + tile / 2, y + tile - 12, name, 13, INK, "mono", 700, "middle"))
        body.append("</g></g>")
    return svg(1200, 340, "stack", "tecnologías: " + ", ".join(n for n, _ in STACK), "\n".join(body))


def oss_summary(d):
    names = d["merged_projects"]
    body = [card(24, 24, 1152, 120, GOLD, rot=-.2, tape=False)]
    body.append(f'<g class="pop">{text(56, 106, d["merged_external"], 84, ORANGE)}</g>')
    body.append(text(150, 82, "pull requests mergeados", 28, INK))
    body.append(text(150, 112, f"en {len(names)} proyectos ajenos · {sum(o['open'] for o in d['oss'])} abiertos en revisión", 15, INK, "mono", 400, extra='opacity=".7"'))
    x, y = 560, 56
    for i, name in enumerate(names):
        w = 26 + len(name) * 10
        if x + w > 1150:
            x, y = 560, y + 44
        body.append(f'<g class="pop" style="animation-delay:{.3 + i * .12}s"><rect x="{x + 3}" y="{y + 3}" width="{w}" height="34" rx="17" fill="{ACCENTS[i % 6]}"/>'
                    f'<rect x="{x}" y="{y}" width="{w}" height="34" rx="17" fill="{PAPER2}" stroke="{INK}" stroke-width="3"/>{text(x + w / 2, y + 23, name, 14, INK, "mono", 700, "middle")}</g>')
        x += w + 16
    return svg(1200, 170, "open source", f"{d['merged_external']} pull requests mergeados en {len(names)} proyectos: {', '.join(names)}", "\n".join(body))


def oss_card(o, index):
    color = ACCENTS[(index * 2 + 1) % 6]
    stamp, stamp_color = ("mergeado", TEAL) if o["merged"] else ("en revisión", BLUE)
    count = o["merged"] or o["open"] or o["total"]
    noun = "PR" if count == 1 else "PRs"
    body = [card(16, 26, 268, 210, color, rot=(-1, .8, -.6, 1)[index % 4])]
    body.append(text(40, 70, o["owner"] + " /", 13, INK, "mono", 700, spacing=1, extra='opacity=".55"'))
    name_size = max(17, min(32, int(228 / (len(o["name"]) * 0.56))))
    body.append(text(40, 70 + 8 + name_size, o["name"], name_size, INK))
    body.append(f'<g class="pop" style="animation-delay:{.3 + index * .15}s">{text(40, 182, count, 60, color if color != GOLD else ORANGE)}</g>')
    body.append(text(40 + 36 + 28 * len(str(count)), 182, noun, 22, INK, "mono", 700, extra='opacity=".7"'))
    body.append(f'<g class="pop" style="animation-delay:{.6 + index * .15}s" transform="rotate(-7 224 146)"><rect x="168" y="130" width="106" height="32" rx="6" fill="{PAPER2}" fill-opacity=".85" stroke="{stamp_color}" stroke-width="3"/>'
                f'{text(221, 152, stamp, 14, stamp_color, "mono", 700, "middle", spacing=1.2)}</g>')
    title = o["latest"] if len(o["latest"]) <= 30 else o["latest"][:29] + "…"
    body.append(text(40, 222, title, 11, INK, "mono", 400, extra='opacity=".55"'))
    return svg(300, 262, o["name"], f"{o['name']}: {o['merged']} pull requests mergeados, {o['open']} abiertos", "\n".join(body))


def pill(label, color, width, icon=None):
    body = [f'<g><rect x="5" y="5" width="{width - 8}" height="48" rx="24" fill="{color}"/>'
            f'<rect x="2" y="2" width="{width - 8}" height="48" rx="24" fill="{PAPER2}" stroke="{INK}" stroke-width="3"/>']
    tx = 28
    if icon:
        body.append(icon)
        tx = 66
    body.append(text(tx, 33, label, 17, INK, "mono", 700))
    ax = width - 40
    body.append(f'<g class="nudge"><path d="M{ax} 26h18m-7-7 7 7-7 7" fill="none" stroke="{color}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/></g></g>')
    style = "@keyframes nudge{50%{transform:translateX(4px)}}.nudge{animation:nudge 1.8s ease-in-out infinite}"
    return svg(width, 60, label, f"enlace: {label}", "\n".join(body), style)


def linkedin_glyph(x, y, color):
    return (f'<g transform="translate({x} {y})"><rect width="30" height="30" rx="6" fill="{color}"/>'
            f'<text x="15" y="23" {SERIF} font-size="21" font-weight="700" font-style="italic" fill="{PAPER2}" text-anchor="middle">in</text></g>')


def mail_glyph(x, y, color):
    return (f'<g transform="translate({x} {y})" fill="none" stroke="{color}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round">'
            f'<rect x="1" y="4" width="28" height="22" rx="4"/><path d="m2 8 13 10L28 8"/></g>')


def web_glyph(x, y, color):
    return (f'<g transform="translate({x} {y})" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round">'
            f'<circle cx="15" cy="15" r="13"/><ellipse cx="15" cy="15" rx="6" ry="13"/><path d="M2 15h26"/></g>')


def footer(d):
    waves = ""
    for i, (color, dy, dur) in enumerate(((BLUE, 0, 14), (PURPLE, 14, 18), (ORANGE, 28, 22))):
        waves += (f'<g style="animation:sway {dur}s ease-in-out infinite alternate"><path d="M-80 {60 + dy} C 140 {20 + dy}, 300 {100 + dy}, 520 {58 + dy} S 900 {16 + dy}, 1280 {64 + dy} V 160 H-80z" '
                  f'fill="{color}" opacity="{.9 - i * .18}"/></g>')
    body = f"""  <rect width="1200" height="150" fill="none"/>
  <clipPath id="f"><rect width="1200" height="150" rx="20"/></clipPath>
  <g clip-path="url(#f)">{waves}
    <rect x="320" y="70" width="560" height="56" rx="12" fill="{PAPER2}" stroke="{INK}" stroke-width="3"/>
    {text(600, 96, "hecho a mano en managua", 22, INK, anchor="middle")}
    {text(600, 116, f"actualizado {d['generated']} · datos de la api de github", 12, INK, "mono", 400, "middle", extra='opacity=".6"')}
  </g>"""
    return svg(1200, 150, "pie", "hecho a mano en Managua, Nicaragua", body, "@keyframes sway{to{transform:translateX(70px)}}")


# ---------------------------------------------------------------- orquestación
def write(name, content):
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / name).write_text(content, encoding="utf-8")


def main():
    if "--offline" in sys.argv:
        data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    else:
        data = collect()
        SNAPSHOT.parent.mkdir(exist_ok=True)
        SNAPSHOT.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    for number, (name, color) in enumerate((("proyectos", ORANGE), ("contribuciones", BLUE), ("stack", PINK), ("open-source", TEAL), ("contacto", PURPLE)), 1):
        write(f"h-{name}.svg", header(name, f"0{number}", color))
    write("about.svg", about())
    write("stats.svg", stats(data))
    write("heatmap.svg", heatmap(data))
    write("langs.svg", languages(data))
    write("stack.svg", stack())
    write("oss.svg", oss_summary(data))
    for i, o in enumerate(data["oss"]):
        write(f"oss-{o['name']}.svg", oss_card(o, i))
    for name, _, color in PROJECTS:
        write(f"link-{name}.svg", pill(name, color, 60 + len(name) * 11 + 44))
    write("link-portafolio.svg", pill("portafolio", ORANGE, 250, web_glyph(24, 11, ORANGE)))
    write("link-linkedin.svg", pill("LinkedIn", BLUE, 238, linkedin_glyph(24, 11, BLUE)))
    write("link-github.svg", pill("GitHub", INK, 226, f'<g class="m">{logo("github", 24, 12, 28, PURPLE)}</g>{logo("github", 22, 10, 28, INK)}'))
    write("link-correo.svg", pill("correo", PINK, 214, mail_glyph(24, 11, PINK)))
    write("footer.svg", footer(data))
    print("listo:", len(list(ASSETS.glob("*.svg"))), "svg")


if __name__ == "__main__":
    main()
