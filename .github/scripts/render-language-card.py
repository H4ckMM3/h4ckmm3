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

if not languages:
    raise SystemExit("No public language statistics available")

total = languages.total()
top = sorted(languages.items(), key=lambda item: (-item[1], item[0]))[:6]
height = 87 + 25 * len(top)
rows = []
for index, (name, size) in enumerate(top):
    y = 68 + index * 25
    share = 100 * size / total
    percentage = f"{share:.1f}".replace(".", ",")
    rows.append(f'''
  <text x="24" y="{y}">{escape(name)}</text>
  <rect x="172" y="{y - 9}" width="235" height="7" fill="#dedede"/>
  <rect x="172" y="{y - 9}" width="{max(1, 235 * size / total):.2f}" height="7" fill="#111"/>
  <text x="471" y="{y}" text-anchor="end">{percentage}%</text>''')

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="495" height="{height}" viewBox="0 0 495 {height}" role="img" aria-labelledby="title desc">
<title id="title">Топ языков</title>
<desc id="desc">Доли по объёму кода в собственных публичных репозиториях {escape(owner)}.</desc>
<rect x="0.5" y="0.5" width="494" height="{height - 1}" fill="#fff" stroke="#111"/>
<g fill="#111" font-family="Arial, sans-serif" font-size="14">
  <text x="24" y="35" font-size="19" font-weight="bold">Топ языков</text>
  {''.join(rows)}
  <text x="24" y="{height - 18}" font-size="12" fill="#444">Доля кода в собственных публичных репозиториях</text>
</g>
</svg>
'''
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(svg, encoding="utf-8")
