#!/usr/bin/env python3
import html
import json
import os
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

USERNAME = os.getenv("GH_USERNAME", "Hmuhasibi21")
TOKEN = os.getenv("GH_TOKEN", "")
OUT = Path("assets")
OUT.mkdir(exist_ok=True)

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "Hmuhasibi21-profile-stats",
    "X-GitHub-Api-Version": "2022-11-28",
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def gh_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def esc(value):
    return html.escape(str(value))


def pct(part, total):
    return 0 if total <= 0 else (part / total * 100.0)


def write_stats(profile, repos):
    owned = [repo for repo in repos if not repo.get("fork")]
    stars = sum(repo.get("stargazers_count", 0) for repo in owned)
    forks = sum(repo.get("forks_count", 0) for repo in owned)

    now = datetime.now(timezone.utc)
    recent = 0

    for repo in owned:
        pushed = repo.get("pushed_at")
        if not pushed:
            continue
        try:
            pushed_at = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
            if (now - pushed_at).days <= 30:
                recent += 1
        except ValueError:
            pass

    items = [
        ("Public Repositories", profile.get("public_repos", len(owned))),
        ("Total Stars", stars),
        ("Total Forks", forks),
        ("Followers", profile.get("followers", 0)),
        ("Following", profile.get("following", 0)),
        ("Active Repos · 30d", recent),
    ]

    rows = []
    for index, (label, value) in enumerate(items):
        col = index % 2
        row = index // 2
        x = 32 + col * 225
        y = 86 + row * 48

        rows.append(
            f'<text x="{x}" y="{y}" class="label">{esc(label)}</text>'
        )
        rows.append(
            f'<text x="{x}" y="{y + 22}" class="value">{esc(value)}</text>'
        )

    updated = now.strftime("%d %b %Y · %H:%M UTC")

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="470" height="245" viewBox="0 0 470 245" role="img" aria-label="GitHub Profile Statistics">
<defs>
  <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
    <feDropShadow dx="0" dy="4" stdDeviation="7" flood-color="#1f2328" flood-opacity="0.10"/>
  </filter>
  <linearGradient id="accentGradient" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="#0969da"/>
    <stop offset="100%" stop-color="#54aeff"/>
  </linearGradient>
</defs>
<style>
  .background{{fill:#ffffff;stroke:#d0d7de;stroke-width:1}}
  .title{{fill:#1f2328;font:700 19px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}}
  .username{{fill:#656d76;font:500 12px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}}
  .label{{fill:#656d76;font:500 12px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}}
  .value{{fill:#0969da;font:700 19px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}}
  .footer{{fill:#8c959f;font:400 11px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}}
</style>
<rect x="4" y="4" width="462" height="237" rx="16" class="background" filter="url(#shadow)"/>
<rect x="24" y="25" width="4" height="27" rx="2" fill="url(#accentGradient)"/>
<text x="42" y="45" class="title">GitHub Snapshot</text>
<text x="438" y="45" text-anchor="end" class="username">@{esc(USERNAME)}</text>
<line x1="28" y1="64" x2="442" y2="64" stroke="#d8dee4"/>
{''.join(rows)}
<circle cx="32" cy="222" r="4" fill="#1a7f37"/>
<text x="44" y="226" class="footer">Auto-updated · {esc(updated)}</text>
</svg>'''

    (OUT / "github-stats.svg").write_text(svg, encoding="utf-8")


def write_languages(repos):
    totals = defaultdict(int)

    for repo in repos:
        if repo.get("fork"):
            continue

        name = repo.get("name")
        if not name:
            continue

        try:
            languages = gh_json(
                f"https://api.github.com/repos/{USERNAME}/{name}/languages"
            )
            for language, size in languages.items():
                totals[language] += int(size)
        except Exception as error:
            print(f"warning: languages for {name}: {error}")

    total = sum(totals.values())
    top = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:6]
    palette = ["#0969da", "#8250df", "#1a7f37", "#bf8700", "#cf222e", "#57606a"]

    rows = []
    y = 80

    for index, (language, size) in enumerate(top):
        percent = pct(size, total)
        width = max(2, round(340 * percent / 100))
        color = palette[index % len(palette)]

        rows.append(f'<circle cx="32" cy="{y - 4}" r="5" fill="{color}"/>')
        rows.append(f'<text x="46" y="{y}" class="language">{esc(language)}</text>')
        rows.append(f'<text x="438" y="{y}" text-anchor="end" class="percentage">{percent:.1f}%</text>')
        rows.append(f'<rect x="32" y="{y + 10}" width="340" height="6" rx="3" fill="#eaeef2"/>')
        rows.append(f'<rect x="32" y="{y + 10}" width="{width}" height="6" rx="3" fill="{color}"/>')
        y += 31

    if not top:
        rows.append('<text x="32" y="100" class="description">No public language data available.</text>')

    updated = datetime.now(timezone.utc).strftime("%d %b %Y · %H:%M UTC")

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="470" height="300" viewBox="0 0 470 300" role="img" aria-label="Top Programming Languages">
<defs>
  <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
    <feDropShadow dx="0" dy="4" stdDeviation="7" flood-color="#1f2328" flood-opacity="0.10"/>
  </filter>
  <linearGradient id="accentGradient" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="#8250df"/>
    <stop offset="100%" stop-color="#a475f9"/>
  </linearGradient>
</defs>
<style>
  .background{{fill:#ffffff;stroke:#d0d7de;stroke-width:1}}
  .title{{fill:#1f2328;font:700 19px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}}
  .subtitle{{fill:#656d76;font:500 12px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}}
  .language{{fill:#24292f;font:600 12px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}}
  .percentage{{fill:#656d76;font:500 12px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}}
  .description{{fill:#656d76;font:500 13px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}}
  .footer{{fill:#8c959f;font:400 11px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}}
</style>
<rect x="4" y="4" width="462" height="292" rx="16" class="background" filter="url(#shadow)"/>
<rect x="24" y="25" width="4" height="27" rx="2" fill="url(#accentGradient)"/>
<text x="42" y="45" class="title">Top Languages</text>
<text x="438" y="45" text-anchor="end" class="subtitle">public repositories</text>
<line x1="28" y1="64" x2="442" y2="64" stroke="#d8dee4"/>
{''.join(rows)}
<text x="32" y="282" class="footer">Auto-updated · {esc(updated)}</text>
</svg>'''

    (OUT / "top-langs.svg").write_text(svg, encoding="utf-8")


def main():
    print(f"Generating profile statistics for @{USERNAME}...")

    profile = gh_json(f"https://api.github.com/users/{USERNAME}")
    repos = []
    page = 1

    while True:
        batch = gh_json(
            f"https://api.github.com/users/{USERNAME}/repos"
            f"?type=owner&sort=updated&per_page=100&page={page}"
        )

        if not batch:
            break

        repos.extend(batch)

        if len(batch) < 100:
            break

        page += 1

    write_stats(profile, repos)
    write_languages(repos)

    print(f"Generated profile stats from {len(repos)} public repositories.")


if __name__ == "__main__":
    main()
