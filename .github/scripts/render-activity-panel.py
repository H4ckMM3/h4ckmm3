import json
import re
import sys
from itertools import groupby, takewhile
from pathlib import Path
from subprocess import check_output

owner, folder = sys.argv[1:]
output = Path(folder)
query = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""
response = check_output(["gh", "api", "graphql", "-f", f"query={query}", "-f", f"login={owner}"])
collection = json.loads(response)["data"]["user"]["contributionsCollection"]
calendar = collection["contributionCalendar"]
days = sorted((day for week in calendar["weeks"] for day in week["contributionDays"]), key=lambda day: day["date"])
worked = [day["contributionCount"] > 0 for day in days]
# When there are no contributions today, count a streak ending yesterday.
current_window = worked if worked and worked[-1] else worked[:-1]
current = sum(1 for _ in takewhile(bool, reversed(current_window)))
best = max((sum(1 for _ in run) for active, run in groupby(worked) if active), default=0)
metrics = [
    ("Вклады", calendar["totalContributions"]),
    ("Коммиты", collection["totalCommitContributions"]),
    ("Пул-реквесты", collection["totalPullRequestContributions"]),
    ("Текущая серия", current),
    ("Лучшая серия", best),
]
tiles = []
for i, (label, value) in enumerate(metrics):
    x = 29 + 171 * i
    unit = '<text x="144" y="53" text-anchor="end" font-size="13" fill="#9b4166">дн.</text>' if i >= 3 else ""
    tiles.append(f'''
<g transform="translate({x} 77)">
  <rect class="tile" style="--delay:{i * 180}ms" width="158" height="92" rx="15" fill="#fff" stroke="#edb5cf"/>
  <text x="14" y="25" font-size="15" fill="#79344f">{label}</text>
  <text x="14" y="65" font-size="34" font-weight="750" fill="#a51f61">{value}</text>
  {unit}
</g>''')

description = ", ".join(f"{label}: {value}" for label, value in metrics)
(output / "marin-activity.svg").write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="200" viewBox="0 0 900 200" role="img" aria-labelledby="title desc">
<title id="title">Активность marin за последний год</title><desc id="desc">{description}</desc>
<defs><linearGradient id="paper"><stop stop-color="#fff9fc"/><stop offset="1" stop-color="#fae0ee"/></linearGradient></defs>
<style>
@media (prefers-reduced-motion: no-preference) {{
  .tile {{ animation: heartbeat 5.5s ease-in-out var(--delay) infinite; }}
  .wave {{ stroke-dasharray: 26 132; animation: signal 3s linear infinite; }}
  @keyframes heartbeat {{ 0%, 31%, 100% {{ fill:#fff; }} 13% {{ fill:#ffe0ef; stroke:#e34b8e; }} }}
  @keyframes signal {{ to {{ stroke-dashoffset:-158; }} }}
}}
</style>
<rect x="1" y="1" width="898" height="198" rx="23" fill="url(#paper)" stroke="#e6a1c2" stroke-width="2"/>
<g font-family="system-ui,sans-serif">
  <text x="30" y="46" font-size="25" font-weight="750" fill="#902653">Активность GitHub</text>
  <text x="30" y="63" font-size="12" fill="#79344f">За последний год</text>
  <path d="M711 44h33l10-9 9 16 12-24 13 17h71" fill="none" stroke="#eeb2ce" stroke-width="2"/>
  <path class="wave" pathLength="158" d="M711 44h33l10-9 9 16 12-24 13 17h71" fill="none" stroke="#ba2b66" stroke-width="3" stroke-linecap="round"/>
  {''.join(tiles)}
</g>
</svg>
''', encoding="utf-8")

snake = (output / "snake-light.svg").read_text()
opening = re.search(r'<svg\b[^>]*\bviewBox="([^"]+)"[^>]*>', snake)
if not opening or not snake.endswith("</svg>"):
    raise ValueError("Unexpected contribution snake SVG")
view_box = opening[1]
content = snake[opening.end():-len("</svg>")]
content = content.replace("--ce:#fff4f9", "--ce:#f9e1ed")
(output / "marin-calendar.svg").write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="235" viewBox="0 0 900 235" role="img" aria-labelledby="title">
<title id="title">Розовая змейка на календаре вкладов GitHub</title>
<style>
.calendar-grid .c {{ width:14.5px; height:14.5px; stroke:#d9a5c0; stroke-width:.65px; }}
@media (prefers-reduced-motion: reduce) {{ .calendar-grid * {{ animation:none !important; }} }}
</style>
<rect x="1" y="1" width="898" height="233" rx="23" fill="#fff5fa" stroke="#e6a1c2" stroke-width="2"/>
<text x="30" y="42" font-family="system-ui,sans-serif" font-weight="750" font-size="22" fill="#902653">Календарь вкладов</text>
<svg class="calendar-grid" x="15" y="49" width="870" height="180" viewBox="{view_box}">{content}</svg>
</svg>
''', encoding="utf-8")
