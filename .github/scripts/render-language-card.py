import json
import sys
from collections import Counter
from html import escape
from pathlib import Path
from subprocess import check_output


def github(endpoint, *options):
    return json.loads(check_output(["gh", "api", endpoint, *options]))


owner = sys.argv[1]
output = Path(sys.argv[2])
pages = github(f"users/{owner}/repos?type=owner&per_page=100", "--paginate", "--slurp")
languages = Counter()
for page in pages:
    for repo in page:
        if not repo["fork"] and not repo["private"]:
            languages.update(github(f"repos/{repo['full_name']}/languages"))

languages.pop("TeX", None)

if not languages:
    raise SystemExit("No public language statistics available")

total = languages.total()
top = sorted(languages.items(), key=lambda item: (-item[1], item[0]))[:6]
rows = []
for index, (name, size) in enumerate(top):
    x = 30 + 433 * (index // 3)
    y = 74 + 53 * (index % 3)
    share = size / total
    label = f"{100 * share:.1f}".replace(".", ",")
    width = max(2, 405 * share)
    rows.append(f'''<g transform="translate({x} {y})">
  <text x="0" y="0" fill="#79344f" font-size="16" font-weight="640">{escape(name)}</text>
  <text x="405" y="0" fill="#a51f61" font-size="16" text-anchor="end">{label}%</text>
  <rect x="0" y="11" width="405" height="9" rx="4.5" fill="#f4d6e6"/>
  <rect class="bar" style="--delay:{index * 160}ms" x="0" y="11" width="{width:.2f}" height="9" rx="4.5" fill="url(#ink)"/>
  <clipPath id="fill-{index}"><rect x="0" y="11" width="{width:.2f}" height="9" rx="4.5"/></clipPath>
  <g clip-path="url(#fill-{index})"><rect class="shine" style="--delay:{index * 380}ms" x="-60" y="11" width="60" height="9" fill="url(#highlight)"/></g>
</g>''')

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="240" viewBox="0 0 900 240" role="img" aria-labelledby="title desc">
<title id="title">Языки в репозиториях</title><desc id="desc">Доля кода в собственных публичных репозиториях {escape(owner)} без TeX.</desc>
<defs>
  <linearGradient id="ink"><stop stop-color="#a51f61"/><stop offset="1" stop-color="#e65d9d"/></linearGradient>
  <linearGradient id="highlight"><stop stop-color="#fff" stop-opacity="0"/><stop offset=".6" stop-color="#fff" stop-opacity=".72"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
</defs>
<style>
.shine {{ display:none; }}
@media (prefers-reduced-motion: no-preference) {{
  .bar {{ transform-origin:left; transform-box:fill-box; animation:grow .82s ease-out var(--delay) both; }}
  .shine {{ display:inline; animation:sweep 5s ease-in-out var(--delay) infinite; }}
  @keyframes grow {{ from {{ transform:scaleX(0); }} }}
  @keyframes sweep {{ 0%,17% {{ transform:translateX(0); }} 57%,100% {{ transform:translateX(470px); }} }}
}}
</style>
<rect x="1" y="1" width="898" height="238" rx="23" fill="#fff7fb" stroke="#e6a1c2" stroke-width="2"/>
<g font-family="system-ui,sans-serif">
  <text x="30" y="41" font-size="25" font-weight="750" fill="#902653">Топ языков</text>
  <text x="869" y="41" text-anchor="end" font-size="14" fill="#79344f">По объёму кода · без TeX</text>
  {"".join(rows)}
</g>
</svg>
'''
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(svg, encoding="utf-8")
output.with_name("marin-languages.svg").write_text(svg, encoding="utf-8")
